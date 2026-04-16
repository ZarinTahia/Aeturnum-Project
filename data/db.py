"""
db.py
Real PostgreSQL connection and queries.
Replaces mock_data.py — same function signatures, real DB behind it.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

def get_user(user_id: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


# ─────────────────────────────────────────────
# PROFILES
# ─────────────────────────────────────────────

def get_profile(profile_id: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM profiles WHERE id = %s", (profile_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None



# ─────────────────────────────────────────────
# RELATIONSHIPS
# ─────────────────────────────────────────────

def get_relationships_for_user(user_id: str):
    """Return all relationships for this user's active profile."""
    user = get_user(user_id)
    if not user:
        return []

    my_profile_id = user["current_profile_id"]

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM relationships
        WHERE from_profile_id = %s
    """, (my_profile_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def check_relationship(user_id: str, target_profile_id: str):
    """
    Graph-based relationship check using recursive CTE.
    Simulates Apache AGE traversal on standard PostgreSQL.

    Traverses the relationship graph up to 6 degrees deep.
    Only CONNECTED edges are traversed — mirrors AGE sync rules.

    Returns same structure as guard.py.
    """
    user = get_user(user_id)
    if not user:
        return {"allowed": False, "relationship_type": None, "custom_label": None, "reason": "user_not_found"}

    my_profile_id = user["current_profile_id"]

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Recursive CTE — traverses connected relationships like a graph
    # Returns the direct relationship to the target if reachable
    cur.execute("""
        WITH RECURSIVE graph AS (
            -- Base case: direct relationships from user's profile
            SELECT
                from_profile_id,
                to_profile_id,
                type,
                status,
                custom_label,
                1 AS depth,
                ARRAY[from_profile_id]::text[] AS visited
            FROM relationships
            WHERE from_profile_id = %s AND status = 'connected'

            UNION ALL

            -- Recursive case: traverse further connections
            SELECT
                r.from_profile_id,
                r.to_profile_id,
                r.type,
                r.status,
                r.custom_label,
                g.depth + 1,
                g.visited || r.from_profile_id
            FROM relationships r
            INNER JOIN graph g ON r.from_profile_id = g.to_profile_id
            WHERE r.status = 'connected'
              AND NOT (r.from_profile_id = ANY(g.visited))
              AND g.depth < 6
        )
        SELECT type, custom_label, status, depth
        FROM graph
        WHERE to_profile_id = %s
        ORDER BY depth ASC
        LIMIT 1;
    """, (my_profile_id, target_profile_id))

    row = cur.fetchone()

    # Also check if a direct relationship exists with any status (for pending/blocked messages)
    cur.execute("""
        SELECT * FROM relationships
        WHERE from_profile_id = %s AND to_profile_id = %s
    """, (my_profile_id, target_profile_id))
    direct = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        row = dict(row)
        return {
            "allowed": True,
            "relationship_type": row["type"],
            "custom_label": row.get("custom_label"),
            "reason": "connected",
            "depth": row["depth"],
        }

    if direct:
        direct = dict(direct)
        return {
            "allowed": False,
            "relationship_type": direct["type"],
            "custom_label": direct.get("custom_label"),
            "reason": direct["status"],
            "depth": 1,
        }

    return {"allowed": False, "relationship_type": None, "custom_label": None, "reason": "no_relationship", "depth": None}


# ─────────────────────────────────────────────
# NODES & BLOCKS
# ─────────────────────────────────────────────


def get_nodes_for_profile(profile_id: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM nodes
        WHERE profile_id = %s AND status = 'active'
    """, (profile_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_blocks_for_node(node_id: str):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM blocks
        WHERE node_id = %s AND status = 'active'
        ORDER BY "order"
    """, (node_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# ALL PROFILES (for resolver)
# ─────────────────────────────────────────────

def get_all_profiles():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM profiles WHERE is_active = TRUE")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {row["id"]: dict(row) for row in rows}
