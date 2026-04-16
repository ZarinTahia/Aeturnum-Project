"""
graph/state.py
LangGraph state definition for the Memoria conversation flow.
"""

from typing import TypedDict


class MemoriaState(TypedDict):
    user_id:          str
    user_message:     str
    messages:         list        # full conversation history

    resolved_profiles: list       # [(profile_id, rel), ...]  — from resolver
    allowed_profiles:  list       # [{ profile_id, relationship_type, custom_label }]
    denied_messages:   list       # denial strings for blocked/unconnected profiles

    retrieved_context: str        # relevant chunks from Pinecone vector search
    media_items:       list       # [{ chunk_type, media_url, caption, node_title, node_date }]
    wants_media:       bool       # did the user ask for photos/videos?

    response:          str        # final LLM response
