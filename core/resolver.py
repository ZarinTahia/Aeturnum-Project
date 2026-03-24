"""
resolver.py
Uses the LLM to identify which profiles the user is referring to in their message.
No hardcoded alias dictionaries — the LLM understands natural language references.
"""

import json
from data.db import get_relationships_for_user, get_all_profiles, get_user
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()


def _get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY", ""),
        max_tokens=256,
        temperature=0,
    )


def resolve_profiles(user_id: str, user_message: str) -> list:
    """
    Uses the LLM to identify which profiles the user is referring to.

    Returns:
        List of (profile_id, relationship) tuples — empty list if none found.
    """
    user = get_user(user_id)
    if not user:
        return []

    relationships = get_relationships_for_user(user_id)
    all_profiles = get_all_profiles()

    if not relationships:
        return []

    # Build a description of each available profile for the LLM
    profile_descriptions = []
    profile_map = {}  # profile_id -> relationship row

    for rel in relationships:
        profile = all_profiles.get(rel["to_profile_id"])
        if not profile:
            continue

        nicknames = profile.get("nicknames") or []
        nick_str = f", also known as: {', '.join(nicknames)}" if nicknames else ""
        custom = f", custom label: {rel['custom_label']}" if rel.get("custom_label") else ""

        desc = (
            f"- profile_id: {rel['to_profile_id']} | "
            f"name: {profile['name']} {profile['last_name']}{nick_str} | "
            f"relationship: {rel['type']}{custom} | "
            f"status: {rel['status']}"
        )
        profile_descriptions.append(desc)
        profile_map[rel["to_profile_id"]] = rel

    if not profile_descriptions:
        return []

    profiles_list = "\n".join(profile_descriptions)

    system = SystemMessage(content=f"""You are a profile resolver. The user is asking about people in their family/network.
Your job: identify which profile_id(s) from the list below the user is referring to in their message.

Available profiles:
{profiles_list}

Rules:
- Return ONLY a JSON array of profile_id strings, e.g. ["profile-003"] or ["profile-003", "profile-004"]
- If the user is not asking about any specific person, return []
- Use context clues: "grandma", "nana", "gran" → the grandmother profile; "dad", "father", "papa" → the father profile
- A greeting like "hi" or a general question with no person mentioned → return []
- Return nothing else — just the JSON array""")

    human = HumanMessage(content=user_message)

    try:
        llm = _get_llm()
        response = llm.invoke([system, human])
        raw = response.content.strip()

        # Extract JSON array from response
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []

        profile_ids = json.loads(raw[start:end])

        matched = []
        for pid in profile_ids:
            if pid in profile_map:
                matched.append((pid, profile_map[pid]))

        return matched

    except Exception:
        return []
