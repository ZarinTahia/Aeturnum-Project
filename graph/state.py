"""
graph/state.py
LangGraph state definition for Memoria conversation flow.
"""

from typing import TypedDict, Optional


class MemoriaState(TypedDict):
    user_id:          str
    user_message:     str
    messages:         list          # full conversation history

    resolved_profiles: list         # [(profile_id, rel), ...]
    allowed_profiles:  list         # [{ profile_id, relationship_type, custom_label }]
    denied_messages:   list         # denial strings for blocked profiles

    retrieved_context: str          # text retrieved from Pinecone
    media_items:       list         # [{ chunk_type, media_url, caption, ... }]
    wants_media:       bool         # did user ask for photos/videos?

    response:          str          # final LLM response
