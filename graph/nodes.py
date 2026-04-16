"""
graph/nodes.py
LangGraph node functions — each handles one step of the Memoria flow.

Flow: resolve → guard → retrieve → generate
- resolve:  LLM 1   — identifies which profile(s) the user is asking about
- guard:    SQL CTE  — checks connected relationship to each profile
- retrieve: Pinecone — vector similarity search across ALL profile data + memories
- generate: LLM 2   — composes the final response from retrieved chunks
"""

from core.resolver import resolve_profiles
from core.guard import check_relationship, denial_message
from core.vector_retriever import retrieve_context
from data.db import get_profile
from llm.memoria import call_llm, general_chat
from graph.state import MemoriaState

MEDIA_KEYWORDS = {
    "photo", "photos", "picture", "pictures", "image", "images",
    "show", "video", "videos", "see", "watch",
}


def resolve_node(state: MemoriaState) -> MemoriaState:
    """
    LLM 1 call — identifies which profile(s) the user is asking about.
    Falls back to previously resolved profiles for follow-up messages.
    Pinecone handles relevance ranking in the retrieve step.
    """
    profile_ids = resolve_profiles(state["user_id"], state["user_message"])

    resolved = []
    if profile_ids:
        from data.db import get_relationships_for_user
        relationships = get_relationships_for_user(state["user_id"])
        rel_map = {r["to_profile_id"]: r for r in relationships}
        for pid in profile_ids:
            if pid in rel_map:
                resolved.append((pid, rel_map[pid]))

    # Fall back to previous conversation context for follow-up messages
    if not resolved and state.get("resolved_profiles"):
        resolved = state["resolved_profiles"]

    return {**state, "resolved_profiles": resolved}


def guard_node(state: MemoriaState) -> MemoriaState:
    """
    SQL recursive graph query — verifies the user has a connected
    relationship to each resolved profile. No LLM involved.
    """
    allowed = []
    denied  = []

    for profile_id, rel in state["resolved_profiles"]:
        profile      = get_profile(profile_id)
        profile_name = f"{profile['name']} {profile['last_name']}"
        result       = check_relationship(state["user_id"], profile_id)

        if result["allowed"]:
            allowed.append({
                "profile_id":        profile_id,
                "relationship_type": result["relationship_type"],
                "custom_label":      result["custom_label"],
            })
        else:
            denied.append(denial_message(result, profile_name))

    return {**state, "allowed_profiles": allowed, "denied_messages": denied}


def retrieve_node(state: MemoriaState) -> MemoriaState:
    """
    Pinecone vector search — finds the most relevant chunks for the user's
    question across ALL profile data (bio, birth date, location, education,
    career, life events, reflections, memory blocks, photos, etc.).
    Only searches within profiles the user is authorised to access.
    """
    allowed_ids = [p["profile_id"] for p in state["allowed_profiles"]]
    wants_media = bool(set(state["user_message"].lower().split()) & MEDIA_KEYWORDS)

    context, media_items = retrieve_context(
        user_message=state["user_message"],
        profile_ids=allowed_ids,
        wants_media=wants_media,
    )

    return {
        **state,
        "retrieved_context": context,
        "media_items":       media_items,
        "wants_media":       wants_media,
    }


def generate_node(state: MemoriaState) -> MemoriaState:
    """
    LLM 2 — composes the final response using retrieved context
    and conversation history.
    """
    allowed       = state["allowed_profiles"]
    profile_names = []

    for p in allowed:
        profile = get_profile(p["profile_id"])
        label   = p["custom_label"] or f"{profile['name']} {profile['last_name']}"
        profile_names.append(label)

    if allowed:
        # Always prepend relationship facts so the LLM can answer
        # questions like "is she my grandmother?" even if Pinecone
        # didn't surface a chunk about the relationship.
        rel_lines = []
        for p in allowed:
            profile  = get_profile(p["profile_id"])
            name     = f"{profile['name']} {profile['last_name']}"
            rel_type = p["relationship_type"] or ""
            label    = p["custom_label"] or rel_type
            if rel_type:
                rel_lines.append(
                    f"{name} is the user's {rel_type}"
                    + (f" (called '{label}')" if label != rel_type else "")
                    + "."
                )

        rel_header = "\n".join(rel_lines)
        full_context = (
            rel_header + "\n\n" + state["retrieved_context"]
            if rel_header
            else state["retrieved_context"]
        )

        response = call_llm(
            user_message=state["user_message"],
            context=full_context,
            profile_names=profile_names,
            history=state["messages"],
            has_media=state["wants_media"] and bool(state["media_items"]),
        )
    elif state.get("denied_messages"):
        response = "\n".join(state["denied_messages"])
        return {**state, "response": response}
    else:
        response = general_chat(state["user_message"], state["messages"])

    # Append any denial messages alongside an allowed-profile response
    if allowed and state.get("denied_messages"):
        response += "\n\n" + "\n".join(state["denied_messages"])

    return {**state, "response": response}
