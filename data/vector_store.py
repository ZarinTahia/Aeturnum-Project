"""
vector_store.py
Pinecone vector store operations via LangChain.
Handles upsert and semantic search with profile-level filtering.
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from data.embedder import get_embedder

load_dotenv()

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX     = os.getenv("PINECONE_INDEX_NAME", "memoria-index")
EMBEDDING_DIM      = 384  # all-MiniLM-L6-v2 output dimension


def get_pinecone_client() -> Pinecone:
    return Pinecone(api_key=PINECONE_API_KEY)


def ensure_index():
    """Create the Pinecone index if it doesn't exist."""
    pc = get_pinecone_client()
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"✅ Pinecone index '{PINECONE_INDEX}' created.")
    else:
        print(f"✅ Pinecone index '{PINECONE_INDEX}' already exists.")


def get_vector_store() -> PineconeVectorStore:
    """Returns a LangChain PineconeVectorStore instance."""
    return PineconeVectorStore(
        index_name=PINECONE_INDEX,
        embedding=get_embedder(),
        pinecone_api_key=PINECONE_API_KEY,
    )


def search(query: str, profile_ids: list, top_k: int = 6) -> list:
    """
    Semantic search filtered to specific profile IDs.
    Returns list of dicts: { text, metadata }
    """
    store = get_vector_store()

    # Filter to only retrieve chunks belonging to allowed profiles
    filter_condition = {"profile_id": {"$in": profile_ids}}

    results = store.similarity_search(
        query=query,
        k=top_k,
        filter=filter_condition,
    )

    from data.s3_storage import get_signed_url

    output = []
    for doc in results:
        meta = dict(doc.metadata)

        # Refresh signed URL at retrieval time so it never expires
        if meta.get("chunk_type") in ("image", "video") and meta.get("media_url"):
            s3_path = meta.get("s3_path")
            if s3_path:
                meta["media_url"] = get_signed_url(s3_path)

        output.append({"text": doc.page_content, "metadata": meta})

    return output
