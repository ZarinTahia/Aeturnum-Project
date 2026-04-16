"""
pinecone_indexer.py
Chunks ALL profile data (bio, birth date, place of birth, education, career,
hobbies, life events, reflections, etc.) plus every memory block into Pinecone.

This replaces the context_builder approach — instead of dumping everything into
a single string, every fact becomes its own searchable vector chunk.

Run once (or re-run to refresh after profile/node changes):
    python3 -m data.pinecone_indexer
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from data.db import get_all_profiles, get_nodes_for_profile, get_blocks_for_node

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX_NAME", "memoria-index")
EMBED_MODEL      = "all-MiniLM-L6-v2"
EMBED_DIM        = 384
BATCH_SIZE       = 100


def _get_embedder() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


# ─────────────────────────────────────────────
# Profile field → text chunks
# ─────────────────────────────────────────────

def _profile_chunks(profile: dict) -> list[dict]:
    """Turn every profile field into an individual searchable text chunk."""
    pid  = profile["id"]
    name = f"{profile['name']} {profile.get('last_name', '')}".strip()
    out  = []

    def add(text: str, chunk_type: str):
        if text and text.strip():
            out.append({
                "profile_id": pid,
                "chunk_type": chunk_type,
                "block_type": "text",
                "text":       text.strip(),
                "media_url":  "",
                "caption":    "",
                "node_title": "",
                "node_date":  "",
            })

    if profile.get("bio"):
        add(profile["bio"], "bio")

    if profile.get("birth_date"):
        add(f"{name} was born on {profile['birth_date']}.", "birth_date")

    if profile.get("place_of_birth"):
        add(f"{name}'s place of birth is {profile['place_of_birth']}.", "place_of_birth")

    if profile.get("death_date"):
        add(f"{name} passed away on {profile['death_date']}.", "death_date")

    if profile.get("current_place"):
        add(f"{name} currently lives in {profile['current_place']}.", "current_place")

    if profile.get("gender"):
        add(f"{name}'s gender is {profile['gender']}.", "gender")

    if profile.get("marital_status"):
        add(f"{name}'s marital status is {profile['marital_status']}.", "marital_status")

    if profile.get("preferred_pronouns"):
        add(f"{name}'s preferred pronouns are {profile['preferred_pronouns']}.", "pronouns")

    if profile.get("ethnicity"):
        add(f"{name}'s ethnicity: {profile['ethnicity']}.", "ethnicity")

    if profile.get("nicknames"):
        add(f"{name} is also known as {', '.join(profile['nicknames'])}.", "nicknames")

    for edu in (profile.get("education") or []):
        add(
            f"{name} studied {edu.get('degree', '')} at {edu.get('institution', '')} "
            f"in {edu.get('year', '')}.",
            "education",
        )

    for job in (profile.get("career") or []):
        until = f" until {job['until']}" if job.get("until") else " (current)"
        add(
            f"{name} worked as {job.get('role', '')} at {job.get('company', '')} "
            f"from {job.get('since', '')}{until}.",
            "career",
        )

    if profile.get("hobbies"):
        add(f"{name}'s hobbies include {', '.join(profile['hobbies'])}.", "hobbies")

    for key, val in (profile.get("interests_and_favourites") or {}).items():
        add(f"{name}'s favourite {key} is {val}.", "interests")

    for ach in (profile.get("personal_achievements") or []):
        add(f"{name}'s achievement: {ach}", "achievement")

    for event in (profile.get("life_events") or []):
        add(f"In {event['year']}, {name}: {event['event']}.", "life_event")

    for ref in (profile.get("reflections_and_messages") or []):
        add(f"{name}: {ref}", "reflection")

    return out


# ─────────────────────────────────────────────
# Node blocks → text / media chunks
# ─────────────────────────────────────────────

def _node_chunks(profile: dict) -> list[dict]:
    """Turn every block inside a profile's memory nodes into a chunk."""
    pid   = profile["id"]
    out   = []

    for node in get_nodes_for_profile(pid):
        node_title = node.get("title", "Untitled")
        node_date  = str(node.get("date_iso", ""))

        for block in get_blocks_for_node(node["id"]):
            if block["type"] == "text":
                text = block["content"].get("text", "").strip()
                if text:
                    out.append({
                        "profile_id": pid,
                        "chunk_type": "memory_block",
                        "block_type": "text",
                        "text":       f"[Memory: {node_title}] {text}",
                        "media_url":  "",
                        "caption":    block["content"].get("caption", ""),
                        "node_title": node_title,
                        "node_date":  node_date,
                    })

            elif block["type"] in ("image", "video"):
                caption = block["content"].get("caption", "")
                url     = (
                    block["content"].get("url", "")
                    or block["content"].get("s3_path", "")
                )
                # Index caption as text so similarity search can find it;
                # store the URL in metadata for rendering.
                search_text = (
                    f"[Photo in {node_title}] {caption}"
                    if caption
                    else f"[Photo in {node_title}]"
                )
                out.append({
                    "profile_id": pid,
                    "chunk_type": "memory_block",
                    "block_type": block["type"],
                    "text":       search_text,
                    "media_url":  url,
                    "caption":    caption,
                    "node_title": node_title,
                    "node_date":  node_date,
                })

    return out


# ─────────────────────────────────────────────
# Main indexing routine
# ─────────────────────────────────────────────

def build_all_chunks() -> list[dict]:
    profiles   = get_all_profiles()
    all_chunks = []
    for profile in profiles.values():
        all_chunks.extend(_profile_chunks(profile))
        all_chunks.extend(_node_chunks(profile))
    return all_chunks


def upsert_to_pinecone(chunks: list[dict]):
    pc    = Pinecone(api_key=PINECONE_API_KEY)
    model = _get_embedder()

    # Create index if it doesn't exist
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        print(f"Creating index '{PINECONE_INDEX}' (dim={EMBED_DIM}, cosine)...")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    index = pc.Index(PINECONE_INDEX)

    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with '{EMBED_MODEL}'...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    vectors = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id":       f"{chunk['profile_id']}_chunk_{i}",
            "values":   emb.tolist(),
            "metadata": chunk,
        })

    for i in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[i : i + BATCH_SIZE]
        index.upsert(vectors=batch)
        print(f"  Upserted {min(i + BATCH_SIZE, len(vectors))}/{len(vectors)}")

    print(f"\nDone — {len(vectors)} vectors in '{PINECONE_INDEX}'.")


if __name__ == "__main__":
    print("Building chunks from all profiles and nodes...")
    chunks = build_all_chunks()
    print(f"Total chunks: {len(chunks)}")
    upsert_to_pinecone(chunks)
