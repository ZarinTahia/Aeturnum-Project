"""
embedder.py
Converts text to vector embeddings using HuggingFace sentence-transformers.
Free, runs locally, no API key needed.
"""

from langchain_huggingface import HuggingFaceEmbeddings

_embedder = None

def get_embedder() -> HuggingFaceEmbeddings:
    """Returns a singleton embedder instance."""
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedder


def embed_text(text: str) -> list:
    """Embed a single string."""
    return get_embedder().embed_query(text)


def embed_texts(texts: list) -> list:
    """Embed a list of strings."""
    return get_embedder().embed_documents(texts)
