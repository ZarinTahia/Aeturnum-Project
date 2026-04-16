"""
core/resolver.py
LLM call that identifies which profile(s) the user is asking about.
Node/content relevance is now handled by Pinecone vector search in retrieve_node,
so the resolver only needs to return profile_ids.
"""

import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from data.db import get_relationships_for_user, get_all_profiles, get_user

load_dotenv()

STOP_WORDS = {
    "tell", "me", "about", "the", "a", "an", "what", "who", "is", "are",
    "was", "were", "did", "do", "how", "when", "where", "why", "can", "you",
    "i", "my", "their", "his", "her", "its", "and", "or", "of", "to", "in",
    "on", "at", "for", "with", "that", "this", "show", "find", "get",
}


def _get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY", ""),
        max_tokens=128,
        temperature=0,
    )


def resolve_profiles(user_id: str, user_message: str) -> list:
    """
    Single LLM call — returns profile_ids the user is asking about.
    Content relevance is delegated to Pinecone in the retrieve step.

    Returns:
        ["profile-003", ...]  or  []
    """
    user = get_user(user_id)
    if not user:
        return []

    relationships = get_relationships_for_user(user_id)
    all_profiles  = get_all_profiles()

    if not relationships:
        return []

    # ── Build connected profile list ─────────────────────────────
    connected = []
    for rel in relationships:
        profile = all_profiles.get(rel["to_profile_id"])
        if profile and rel["status"] == "connected":
            connected.append((profile, rel))

    if not connected:
        return []

    # ── Pre-filter by keyword match to keep prompt small ─────────
    message_words = {
        w.strip("'\",.!?").lower()
        for w in user_message.split()
        if len(w) > 2 and w.lower() not in STOP_WORDS
    }

    candidates = []
    for profile, rel in connected:
        profile_terms = {
            profile["name"].lower(),
            profile["last_name"].lower(),
            rel["type"].lower(),
        }
        for nick in (profile.get("nicknames") or []):
            profile_terms.update(w.lower() for w in nick.split())
        if rel.get("custom_label"):
            profile_terms.update(w.lower() for w in rel["custom_label"].split())

        if message_words & profile_terms:
            candidates.append((profile, rel))

    # Fall back to all connected profiles so the LLM can handle
    # semantic references like "my grandmother"
    if not candidates:
        candidates = connected

    # ── Build prompt ──────────────────────────────────────────────
    profile_lines = []
    for profile, rel in candidates:
        nicknames = profile.get("nicknames") or []
        nick_str  = f" | also known as: {', '.join(nicknames)}" if nicknames else ""
        label_str = f" | called: {rel['custom_label']}" if rel.get("custom_label") else ""
        profile_lines.append(
            f"- profile_id: {profile['id']} | name: {profile['name']} {profile['last_name']}"
            f"{nick_str} | relationship: {rel['type']}{label_str}"
        )

    system = SystemMessage(content=f"""You are a memory assistant for a family remembrance app.

Profiles the user is connected to:
{chr(10).join(profile_lines)}

Identify ALL profile_id(s) the user is asking about using name, nickname, or relationship clues.
If multiple people are mentioned, return all of them.

Return ONLY this JSON:
{{"profile_ids": ["profile-xxx", "profile-yyy"]}}

Rules:
- Only return profile_ids from the list above — never invent or guess
- If the person the user mentions is NOT in the list above, return {{"profile_ids": []}}
- If the user asks about two people, return both profile_ids
- If no specific person is mentioned, return {{"profile_ids": []}}
- Return nothing else — only the JSON object""")

    try:
        response = _get_llm().invoke([system, HumanMessage(content=user_message)])
        raw      = response.content.strip()
        start    = raw.find("{")
        end      = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return []
        return json.loads(raw[start:end]).get("profile_ids", [])
    except Exception:
        return []
