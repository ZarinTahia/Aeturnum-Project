"""
graph/nodes.py
LangGraph node functions — each handles one step of the Memoria flow.
"""

from core.resolver import resolve_profiles
from core.guard import check_relationship, denial_message
from core.retriever import retrieve
from data.db import get_profile
from llm.memoria import call_llm, general_chat
from graph.state import MemoriaState

MEDIA_KEYWORDS = {"photo", "photos", "picture", "pictures", "image", "images",
                  "show", "video", "videos", "see", "watch"}


def resolve_node(state: MemoriaState) -> MemoriaState:
    """Identifies which profiles the user is asking about."""
    resolved = resolve_profiles(state["user_id"], state["user_message"])

    # Fall back to previously active profiles for follow-up messages
    if not resolved and state.get("resolved_profiles"):
        resolved = state["resolved_profiles"]

    return {**state, "resolved_profiles": resolved}


def guard_node(state: MemoriaState) -> MemoriaState:
    """Checks relationship access for each resolved profile."""
    allowed = []
    denied  = []

    for profile_id, rel in state["resolved_profiles"]:
        profile     = get_profile(profile_id)
        profile_name = f"{profile['name']} {profile['last_name']}"
        result      = check_relationship(state["user_id"], profile_id)

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
    """Retrieves relevant context + media from Pinecone."""
    profile_ids = [p["profile_id"] for p in state["allowed_profiles"]]

    # Detect if user wants media
    words       = set(state["user_message"].lower().split())
    wants_media = bool(words & MEDIA_KEYWORDS)

    result      = retrieve(state["user_message"], profile_ids, wants_media=wants_media)

    return {
        **state,
        "retrieved_context": result["context"],
        "media_items":       result["media"] if wants_media else [],
        "wants_media":       wants_media,
    }


def generate_node(state: MemoriaState) -> MemoriaState:
    """Calls the LLM with retrieved context and conversation history."""
    allowed = state["allowed_profiles"]
    profile_names = []
    for p in allowed:
        profile = get_profile(p["profile_id"])
        label = p["custom_label"] or f"{profile['name']} {profile['last_name']}"
        profile_names.append(label)

    if allowed:
        response = call_llm(
            user_message=state["user_message"],
            context=state["retrieved_context"],
            profile_names=profile_names,
            history=state["messages"],
            has_media=state["wants_media"] and bool(state["media_items"]),
        )
    elif state.get("denied_messages"):
        # Only denial messages — no LLM needed
        response = "\n".join(state["denied_messages"])
        return {**state, "response": response}
    else:
        # No profile found at all — general greeting/question
        response = general_chat(state["user_message"], state["messages"])

    # Append denial messages alongside an allowed-profile response
    if allowed and state.get("denied_messages"):
        response += "\n\n" + "\n".join(state["denied_messages"])

    return {**state, "response": response}
