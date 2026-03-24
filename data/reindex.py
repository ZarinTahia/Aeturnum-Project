"""
reindex.py
Clears the Pinecone index and re-indexes all data from scratch.
Run with: python3 -m data.reindex
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX_NAME", "memoria-index")

# ── Step 1: Delete all vectors in the index ───────────────────────────────────
print("Clearing Pinecone index...")
pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)
index.delete(delete_all=True)
print("✅ All vectors deleted.")

# ── Step 2: Re-build docs and index ──────────────────────────────────────────
print("Re-indexing from database...")

import json
from langchain_core.documents import Document
from data.db import get_all_profiles, get_nodes_for_profile, get_blocks_for_node
from data.s3_storage import get_signed_url
from data.vector_store import get_vector_store

docs = []


def make_doc(text, metadata):
    return Document(page_content=text, metadata=metadata)


profiles = get_all_profiles()

for profile_id, profile in profiles.items():
    full_name = f"{profile['name']} {profile['last_name']}".strip()
    base_meta = {"profile_id": profile_id, "profile_name": full_name}

    if profile.get("bio"):
        docs.append(make_doc(f"{full_name}: {profile['bio']}", {**base_meta, "chunk_type": "bio"}))

    if profile.get("birth_date"):
        text = f"{full_name} was born on {profile['birth_date']}."
        if profile.get("death_date"):
            text += f" Passed away on {profile['death_date']}."
        docs.append(make_doc(text, {**base_meta, "chunk_type": "birth_death"}))

    if profile.get("place_of_birth") or profile.get("current_place"):
        parts = []
        if profile.get("place_of_birth"):
            parts.append(f"born in {profile['place_of_birth']}")
        if profile.get("current_place"):
            parts.append(f"currently lives in {profile['current_place']}")
        docs.append(make_doc(f"{full_name}: {', '.join(parts)}.", {**base_meta, "chunk_type": "location"}))

    if profile.get("education"):
        for edu in profile["education"]:
            text = f"{full_name} studied {edu.get('degree','')} at {edu.get('institution','')} in {edu.get('year','')}."
            docs.append(make_doc(text, {**base_meta, "chunk_type": "education"}))

    if profile.get("career"):
        for job in profile["career"]:
            until = f" until {job['until']}" if job.get("until") else ""
            text  = f"{full_name} worked as {job.get('role','')} at {job.get('company','')} since {job.get('since','')}{until}."
            docs.append(make_doc(text, {**base_meta, "chunk_type": "career"}))

    if profile.get("hobbies"):
        hobbies = profile["hobbies"]
        if isinstance(hobbies, str):
            hobbies = json.loads(hobbies)
        docs.append(make_doc(f"{full_name} loved: {', '.join(hobbies)}.", {**base_meta, "chunk_type": "hobbies"}))

    if profile.get("interests_and_favourites"):
        favs = profile["interests_and_favourites"]
        if isinstance(favs, str):
            favs = json.loads(favs)
        parts = [f"{k}: {v}" for k, v in favs.items()]
        docs.append(make_doc(f"{full_name}'s favourites — {', '.join(parts)}.", {**base_meta, "chunk_type": "interests"}))

    if profile.get("personal_achievements"):
        achievements = profile["personal_achievements"]
        if isinstance(achievements, str):
            achievements = json.loads(achievements)
        for ach in achievements:
            docs.append(make_doc(f"{full_name} achievement: {ach}", {**base_meta, "chunk_type": "achievement"}))

    if profile.get("life_events"):
        events = profile["life_events"]
        if isinstance(events, str):
            events = json.loads(events)
        for event in events:
            docs.append(make_doc(f"{full_name} in {event['year']}: {event['event']}.", {**base_meta, "chunk_type": "life_event"}))

    if profile.get("reflections_and_messages"):
        refs = profile["reflections_and_messages"]
        if isinstance(refs, str):
            refs = json.loads(refs)
        for ref in refs:
            docs.append(make_doc(f"{full_name} — {ref}", {**base_meta, "chunk_type": "reflection"}))

    nodes = get_nodes_for_profile(profile_id)
    for node in nodes:
        node_meta = {
            **base_meta,
            "node_id":    node["id"],
            "node_title": node.get("title", ""),
            "node_date":  str(node.get("date_iso", "")),
            "node_type":  node.get("type", ""),
        }

        blocks = get_blocks_for_node(node["id"])
        for block in blocks:
            if block["type"] == "text":
                text = block["content"].get("text", "")
                if text:
                    docs.append(make_doc(f"[Memory: {node.get('title','')}] {text}", {**node_meta, "chunk_type": "memory"}))

            elif block["type"] == "image":
                content = block["content"]
                caption = content.get("caption", "")
                s3_path = content.get("s3_path", "")
                # Generate a fresh signed URL (valid 1 hour at index time)
                # Will be refreshed again at retrieval time using s3_path
                media_url = get_signed_url(s3_path) if s3_path else content.get("url", "")
                docs.append(make_doc(
                    f"[Photo from: {node.get('title','')}] {caption}",
                    {
                        **node_meta,
                        "chunk_type": "image",
                        "media_url":  media_url,
                        "s3_path":    s3_path,
                        "caption":    caption,
                    }
                ))

            elif block["type"] == "video":
                content   = block["content"]
                caption   = content.get("caption", "")
                s3_path   = content.get("s3_path", "")
                media_url = get_signed_url(s3_path) if s3_path else content.get("url", "")
                docs.append(make_doc(
                    f"[Video from: {node.get('title','')}] {caption}",
                    {
                        **node_meta,
                        "chunk_type": "video",
                        "media_url":  media_url,
                        "s3_path":    s3_path,
                        "caption":    caption,
                    }
                ))

print(f"📦 Total chunks: {len(docs)}")
store = get_vector_store()
store.add_documents(docs)
print(f"✅ Re-indexed {len(docs)} chunks into Pinecone.")
