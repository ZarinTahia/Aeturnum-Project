"""
core/vector_retriever.py
Queries Pinecone for the most relevant context chunks for a given user message,
filtered to only the profiles the user is authorised to access.

Returns a (context_text, media_items) tuple so retrieve_node can use it directly.
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX_NAME", "memoria-index")
EMBED_MODEL      = "all-MiniLM-L6-v2"

# Module-level singletons — loaded once, reused across requests.
_embedder = None
_index    = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def _get_index():
    global _index
    if _index is None:
        pc     = Pinecone(api_key=PINECONE_API_KEY)
        _index = pc.Index(PINECONE_INDEX)
    return _index


def retrieve_context(
    user_message: str,
    profile_ids: list,
    top_k: int = 6,
    wants_media: bool = False,
) -> tuple:
    """
    Embed user_message, query Pinecone separately for each profile
    so every profile gets an equal share of retrieved chunks.

    Returns:
        context_text  — joined text of relevant chunks (for LLM prompt)
        media_items   — list of image/video dicts (for UI rendering), max 1
    """
    if not profile_ids:
        return "", []

    query_vec     = _get_embedder().encode(user_message).tolist()
    index         = _get_index()
    context_lines = []
    media_items   = []

    for pid in profile_ids:
        results = index.query(
            vector=query_vec,
            top_k=top_k,
            filter={"profile_id": {"$eq": pid}},
            include_metadata=True,
        )

        for match in results.get("matches", []):
            meta       = match.get("metadata", {})
            block_type = meta.get("block_type", "text")
            text       = meta.get("text", "")

            if block_type in ("image", "video") and wants_media:
                url = meta.get("media_url", "")
                if url:
                    media_items.append({
                        "chunk_type": block_type,
                        "media_url":  url,
                        "caption":    meta.get("caption", ""),
                        "node_title": meta.get("node_title", ""),
                        "node_date":  meta.get("node_date", ""),
                    })
            elif text:
                context_lines.append(text)

    return "\n".join(context_lines), media_items[:1]
