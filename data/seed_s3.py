"""
seed_s3.py
Downloads placeholder images and uploads them to real S3.
Updates the blocks table with real S3 paths.
Run once: python3 -m data.seed_s3
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from data.s3_storage import upload_from_url, get_signed_url

load_dotenv()

# Mapping: block_id → { s3_path, unsplash_url, caption }
IMAGES = [
    {
        "block_id":    "block-005",
        "file_id":     "file-001",
        "s3_path":     "memories/rose/apple-pie.jpg",
        "source_url":  "https://images.unsplash.com/photo-1621743478914-cc8a86d7e7b5?w=800",
        "caption":     "Grandma Rose's famous apple pie",
    },
    {
        "block_id":    "block-006",
        "file_id":     "file-002",
        "s3_path":     "memories/rose/garden.jpg",
        "source_url":  "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800",
        "caption":     "Nana's backyard garden in Burlington",
    },
    {
        "block_id":    "block-007",
        "file_id":     "file-003",
        "s3_path":     "memories/rose/birthday-memory.jpg",
        "source_url":  "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800",
        "caption":     "Remembering Nana on her birthday",
    },
    {
        "block_id":    "block-008",
        "file_id":     "file-004",
        "s3_path":     "memories/harold/workshop.jpg",
        "source_url":  "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
        "caption":     "Dad's woodworking workshop",
    },
]

# ─────────────────────────────────────────────
# Step 1 — Upload images to S3
# ─────────────────────────────────────────────
print("Uploading images to S3...")
for img in IMAGES:
    upload_from_url(img["source_url"], img["s3_path"])

# ─────────────────────────────────────────────
# Step 2 — Update blocks table with S3 paths
# ─────────────────────────────────────────────
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

for img in IMAGES:
    # Store S3 path in block content (signed URL generated at retrieval time)
    new_content = json.dumps({
        "s3_path": img["s3_path"],
        "caption": img["caption"],
    })
    cur.execute("""
        UPDATE blocks SET content = %s WHERE id = %s
    """, (new_content, img["block_id"]))

    # Update files table path
    cur.execute("""
        UPDATE files SET path = %s WHERE id = %s
    """, (img["s3_path"], img["file_id"]))

conn.commit()
cur.close()
conn.close()
print("✅ Database updated with S3 paths.")

# ─────────────────────────────────────────────
# Step 3 — Re-index Pinecone with signed URLs
# ─────────────────────────────────────────────
print("Re-indexing Pinecone with signed S3 URLs...")
from data.index_data import docs
from data.vector_store import ensure_index, get_vector_store

# Replace Unsplash URLs with fresh signed S3 URLs in docs
s3_map = {img["caption"]: img["s3_path"] for img in IMAGES}

for doc in docs:
    if doc.metadata.get("chunk_type") in ("image", "video"):
        caption = doc.metadata.get("caption", "")
        s3_path = s3_map.get(caption)
        if s3_path:
            signed_url = get_signed_url(s3_path)
            doc.metadata["media_url"] = signed_url

ensure_index()
store = get_vector_store()
store.add_documents(docs)
print(f"✅ Re-indexed {len(docs)} chunks with real S3 signed URLs.")
