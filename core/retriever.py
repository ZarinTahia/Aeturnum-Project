"""
retriever.py
Semantic retrieval from Pinecone.
Replaces context_builder — returns relevant chunks + media for a query.
"""

from data.vector_store import search


def retrieve(query: str, profile_ids: list, top_k: int = 6, wants_media: bool = False) -> dict:
    """
    Retrieves relevant context chunks and media for a query.
    When wants_media=True, runs a separate search specifically for image/video chunks.

    Returns:
        {
            "context": str,           # text to inject into LLM
            "media": list of dicts    # { chunk_type, media_url, caption, node_title }
        }
    """
    results = search(query, profile_ids, top_k=top_k)

    context_lines = []
    media = []

    for result in results:
        meta       = result["metadata"]
        text       = result["text"]
        chunk_type = meta.get("chunk_type", "")

        # Add text chunks to context (skip image/video — handled separately)
        if chunk_type not in ("image", "video"):
            context_lines.append(text)

    # If user wants media, do a dedicated media search — return only the best match
    if wants_media:
        media_results = search(query, profile_ids, top_k=5)
        seen_captions = set()
        for result in media_results:
            meta       = result["metadata"]
            chunk_type = meta.get("chunk_type", "")
            caption    = meta.get("caption", "")
            if chunk_type in ("image", "video") and meta.get("media_url") and caption not in seen_captions:
                seen_captions.add(caption)
                media.append({
                    "chunk_type": chunk_type,
                    "media_url":  meta["media_url"],
                    "caption":    caption,
                    "node_title": meta.get("node_title", ""),
                    "node_date":  meta.get("node_date", ""),
                })
                break  # Only the single most relevant image

    return {
        "context": "\n".join(context_lines),
        "media":   media,
    }
