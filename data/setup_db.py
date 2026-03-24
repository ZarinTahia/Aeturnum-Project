"""
setup_db.py
Creates tables and seeds data in PostgreSQL (AWS RDS).
Run once: python3 data/setup_db.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cur = conn.cursor()

# ─────────────────────────────────────────────
# CREATE TABLES
# ─────────────────────────────────────────────

cur.execute("""
    CREATE TABLE IF NOT EXISTS families (
        id          VARCHAR(50) PRIMARY KEY,
        name        VARCHAR(255)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id                   VARCHAR(50) PRIMARY KEY,
        first_name           VARCHAR(255) NOT NULL,
        last_name            VARCHAR(255) NOT NULL,
        email                VARCHAR(255) UNIQUE NOT NULL,
        status               VARCHAR(50) DEFAULT 'active',
        family_id            VARCHAR(50) REFERENCES families(id),
        profile_id           VARCHAR(50),
        current_profile_id   VARCHAR(50)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id                        VARCHAR(50) PRIMARY KEY,
        user_id                   VARCHAR(50) REFERENCES users(id),
        type                      VARCHAR(20) DEFAULT 'USER',
        name                      VARCHAR(255),
        last_name                 VARCHAR(255),
        bio                       TEXT,
        birth_date                DATE,
        death_date                DATE,
        gender                    VARCHAR(50),
        preferred_pronouns        VARCHAR(50),
        place_of_birth            VARCHAR(255),
        current_place             VARCHAR(255),
        marital_status            VARCHAR(100),
        ethnicity                 VARCHAR(100),
        nicknames                 JSONB,
        education                 JSONB,
        career                    JSONB,
        hobbies                   JSONB,
        interests_and_favourites  JSONB,
        personal_achievements     JSONB,
        life_events               JSONB,
        reflections_and_messages  JSONB,
        is_active                 BOOLEAN DEFAULT TRUE
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS relationships (
        id               VARCHAR(50) PRIMARY KEY,
        from_profile_id  VARCHAR(50) REFERENCES profiles(id),
        to_profile_id    VARCHAR(50) REFERENCES profiles(id),
        family_id        VARCHAR(50) REFERENCES families(id),
        type             VARCHAR(100) NOT NULL,
        status           VARCHAR(50) DEFAULT 'pending',
        custom_label     VARCHAR(100),
        UNIQUE (from_profile_id, to_profile_id)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        id               VARCHAR(50) PRIMARY KEY,
        profile_id       VARCHAR(50) REFERENCES profiles(id),
        user_id          VARCHAR(50) REFERENCES users(id),
        type             VARCHAR(50),
        title            VARCHAR(255),
        date_iso         DATE,
        status           VARCHAR(20) DEFAULT 'active',
        location_city    VARCHAR(255),
        location_country VARCHAR(255)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id                  VARCHAR(50) PRIMARY KEY,
        user_id             VARCHAR(50) REFERENCES users(id),
        node_id             VARCHAR(50) REFERENCES nodes(id),
        path                VARCHAR(500) NOT NULL,
        filename            VARCHAR(255),
        disk                VARCHAR(50) DEFAULT 's3',
        size                BIGINT,
        mime_type           VARCHAR(100),
        processing_status   VARCHAR(50) DEFAULT 'completed',
        caption             VARCHAR(500),
        exists              BOOLEAN DEFAULT TRUE,
        created_at          TIMESTAMP DEFAULT NOW(),
        updated_at          TIMESTAMP DEFAULT NOW()
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS blocks (
        id       VARCHAR(50) PRIMARY KEY,
        node_id  VARCHAR(50) REFERENCES nodes(id),
        file_id  VARCHAR(50) REFERENCES files(id),
        type     VARCHAR(50),
        content  JSONB,
        status   VARCHAR(20) DEFAULT 'active',
        "order"  INTEGER DEFAULT 1
    );
""")

# Add file_id column to blocks if it doesn't exist
cur.execute("""
    ALTER TABLE blocks ADD COLUMN IF NOT EXISTS file_id VARCHAR(50) REFERENCES files(id);
""")

print("✅ Tables created.")

# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────
import json

# Families
cur.execute("""
    INSERT INTO families (id, name) VALUES (%s, %s)
    ON CONFLICT (id) DO NOTHING;
""", ("family-001", "Carter Family"))

# Users
users = [
    ("user-001", "Alice", "Carter", "alice@example.com", "active", "family-001", "profile-001", "profile-001"),
    ("user-002", "Bob",   "Carter", "bob@example.com",   "active", "family-001", "profile-002", "profile-002"),
]
for u in users:
    cur.execute("""
        INSERT INTO users (id, first_name, last_name, email, status, family_id, profile_id, current_profile_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, u)

# Profiles
profiles = [
    (
        "profile-001", "user-001", "USER", "Alice", "Carter",
        "Alice is a software engineer who loves hiking and photography.",
        "1990-04-12", None, "Female", "she/her", "Boston, MA", "San Francisco, CA", "Single", "Caucasian/White",
        json.dumps(["Ali"]),
        json.dumps([{"institution": "MIT", "degree": "B.Sc. Computer Science", "year": 2012}]),
        json.dumps([{"company": "TechCorp", "role": "Senior Engineer", "since": "2018"}]),
        json.dumps(["hiking", "photography", "cooking"]),
        json.dumps({"music": "Indie folk", "food": "Italian", "book": "The Alchemist"}),
        json.dumps(["Built open-source library with 2k stars"]),
        json.dumps([{"year": 2012, "event": "Graduated from MIT"}, {"year": 2018, "event": "Moved to San Francisco"}]),
        json.dumps([]),
        True
    ),
    (
        "profile-002", "user-002", "USER", "Bob", "Carter",
        "Bob is Alice's brother. He is a chef based in New York.",
        "1988-09-03", None, "Male", "he/him", "Boston, MA", "New York, NY", "Married", "Caucasian/White",
        json.dumps(["Bobby"]),
        json.dumps([{"institution": "Culinary Institute of America", "degree": "Culinary Arts", "year": 2010}]),
        json.dumps([{"company": "Le Bernardin", "role": "Head Chef", "since": "2015"}]),
        json.dumps(["cooking", "cycling", "wine tasting"]),
        json.dumps({"music": "Jazz", "food": "French cuisine", "book": "Kitchen Confidential"}),
        json.dumps(["Michelin star nomination 2022"]),
        json.dumps([{"year": 2010, "event": "Graduated from Culinary Institute"}, {"year": 2015, "event": "Became Head Chef at Le Bernardin"}]),
        json.dumps([]),
        True
    ),
    (
        "profile-003", "user-001", "CURATED", "Rose", "Carter",
        "Rose was a beloved grandmother, schoolteacher, and avid gardener who lived in Vermont.",
        "1932-06-15", "2018-11-02", "Female", "she/her", "Burlington, VT", None, "Widowed", "Caucasian/White",
        json.dumps(["Grandma Rose", "Nana"]),
        json.dumps([{"institution": "University of Vermont", "degree": "B.A. Education", "year": 1954}]),
        json.dumps([{"company": "Burlington Elementary School", "role": "Schoolteacher", "since": "1955", "until": "1990"}]),
        json.dumps(["gardening", "knitting", "baking", "reading"]),
        json.dumps({"music": "Classical, especially Chopin", "food": "Apple pie and roast chicken", "book": "Little Women"}),
        json.dumps(["Taught over 1,000 children during her 35-year career", "Won the Vermont Garden Show three years in a row"]),
        json.dumps([
            {"year": 1954, "event": "Graduated from University of Vermont"},
            {"year": 1956, "event": "Married Harold Carter"},
            {"year": 1960, "event": "Had her first child"},
            {"year": 1990, "event": "Retired from teaching after 35 years"},
            {"year": 2005, "event": "Harold (husband) passed away"},
            {"year": 2018, "event": "Passed away peacefully at home, aged 86"}
        ]),
        json.dumps([
            "She always said: 'A garden is a friend you can visit any time.'",
            "Her apple pie recipe has been passed down through three generations."
        ]),
        True
    ),
    (
        "profile-004", "user-001", "USER", "Harold", "Carter Jr.",
        "Harold Jr. is Alice and Bob's father, a retired architect living in Vermont.",
        "1958-03-22", None, "Male", "he/him", "Burlington, VT", "Burlington, VT", "Divorced", "Caucasian/White",
        json.dumps(["Dad", "Harry"]),
        json.dumps([{"institution": "Yale School of Architecture", "degree": "M.Arch", "year": 1983}]),
        json.dumps([{"company": "Carter & Associates", "role": "Principal Architect", "since": "1985", "until": "2020"}]),
        json.dumps(["woodworking", "fishing", "model trains"]),
        json.dumps({"music": "Classic rock", "food": "BBQ", "book": "The Wright Brothers"}),
        json.dumps(["Designed over 200 residential buildings in New England"]),
        json.dumps([
            {"year": 1983, "event": "Graduated from Yale"},
            {"year": 1985, "event": "Founded Carter & Associates"},
            {"year": 2020, "event": "Retired"}
        ]),
        json.dumps([]),
        True
    ),
    (
        "profile-005", "user-002", "USER", "Stranger", "Person",
        "Someone Alice has no connection with.",
        "1995-01-01", None, "Male", "he/him", "Unknown", "Unknown", "Single", "Prefer not to say",
        json.dumps([]), json.dumps([]), json.dumps([]), json.dumps([]),
        json.dumps({}), json.dumps([]), json.dumps([]), json.dumps([]),
        True
    ),
]

for p in profiles:
    cur.execute("""
        INSERT INTO profiles (
            id, user_id, type, name, last_name, bio, birth_date, death_date,
            gender, preferred_pronouns, place_of_birth, current_place,
            marital_status, ethnicity, nicknames, education, career, hobbies,
            interests_and_favourites, personal_achievements, life_events,
            reflections_and_messages, is_active
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING;
    """, p)

print("✅ Profiles seeded.")

# Relationships
relationships = [
    ("rel-001", "profile-001", "profile-003", "family-001", "granddaughter", "connected", "Grandma Rose"),
    ("rel-002", "profile-001", "profile-004", "family-001", "father",        "connected", "Dad"),
    ("rel-003", "profile-001", "profile-002", "family-001", "brother",       "pending",   None),
]
for r in relationships:
    cur.execute("""
        INSERT INTO relationships (id, from_profile_id, to_profile_id, family_id, type, status, custom_label)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, r)

print("✅ Relationships seeded.")

# Nodes
nodes = [
    ("node-001", "profile-003", "user-001", "memory", "Grandma's Apple Pie",              "2010-12-25", "active", "Burlington", "USA"),
    ("node-002", "profile-003", "user-002", "memory", "Learning to Garden with Nana",     "2005-07-04", "active", "Burlington", "USA"),
    ("node-003", "profile-003", "user-001", "post",   "Remembering Nana on her birthday", "2019-06-15", "active", None,         None),
    ("node-004", "profile-004", "user-001", "memory", "Dad's woodworking workshop",       "2015-08-10", "active", "Burlington", "USA"),
]
for n in nodes:
    cur.execute("""
        INSERT INTO nodes (id, profile_id, user_id, type, title, date_iso, status, location_city, location_country)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, n)

print("✅ Nodes seeded.")

# Blocks
blocks = [
    # Text blocks
    ("block-001", "node-001", "text", json.dumps({"text": "Every Christmas, Grandma Rose would wake up at 5am to start her famous apple pie. The whole house smelled of cinnamon and butter. She taught me her secret — always use Granny Smith apples and never skip the lemon zest."}), "active", 1),
    ("block-002", "node-002", "text", json.dumps({"text": "Nana had a garden that stretched the full length of her backyard. She knew every plant by name. She would say: 'Bobby, a garden teaches you patience — you plant today and trust tomorrow.' I think about that every time I plate a dish."}), "active", 1),
    ("block-003", "node-003", "text", json.dumps({"text": "Today would have been Nana's 87th birthday. She lived a full, beautiful life. 35 years of teaching, a garden she loved, and a family she held together with warmth and patience. We miss you every day, Grandma Rose."}), "active", 1),
    ("block-004", "node-004", "text", json.dumps({"text": "Dad's workshop smells like sawdust and machine oil. He spent every weekend in there building furniture — a rocking chair for Grandma, bookshelves for our rooms. He never used instructions. He said 'measure twice, cut once' and somehow it always worked."}), "active", 1),

]
for b in blocks:
    cur.execute("""
        INSERT INTO blocks (id, node_id, file_id, type, content, status, "order")
        VALUES (%s, %s, NULL, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, b)

print("✅ Blocks seeded.")

# Files — mirrors files table, simulates S3 paths
files = [
    ("file-001", "user-001", "node-001", "memories/rose/apple-pie.jpg",        "apple-pie.jpg",        "image/jpeg", 204800, "Grandma Rose's famous apple pie"),
    ("file-002", "user-002", "node-002", "memories/rose/garden.jpg",           "garden.jpg",           "image/jpeg", 184320, "Nana's backyard garden in Burlington"),
    ("file-003", "user-001", "node-003", "memories/rose/birthday-memory.jpg",  "birthday-memory.jpg",  "image/jpeg", 163840, "Remembering Nana on her birthday"),
    ("file-004", "user-001", "node-004", "memories/harold/workshop.jpg",       "workshop.jpg",         "image/jpeg", 245760, "Dad's woodworking workshop"),
]
for f in files:
    cur.execute("""
        INSERT INTO files (id, user_id, node_id, path, filename, mime_type, size, caption)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, f)

print("✅ Files seeded.")

# Image blocks — reference file_id, URL simulates a resolved S3 signed URL
image_blocks = [
    ("block-005", "node-001", "file-001", "image", json.dumps({
        "url": "https://images.unsplash.com/photo-1621743478914-cc8a86d7e7b5?w=800",
        "caption": "Grandma Rose's famous apple pie",
    }), "active", 2),
    ("block-006", "node-002", "file-002", "image", json.dumps({
        "url": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800",
        "caption": "Nana's backyard garden in Burlington",
    }), "active", 2),
    ("block-007", "node-003", "file-003", "image", json.dumps({
        "url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800",
        "caption": "Remembering Nana on her birthday",
    }), "active", 2),
    ("block-008", "node-004", "file-004", "image", json.dumps({
        "url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
        "caption": "Dad's woodworking workshop",
    }), "active", 2),
]
for b in image_blocks:
    cur.execute("""
        INSERT INTO blocks (id, node_id, file_id, type, content, status, "order")
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, b)

print("✅ Image blocks seeded.")

conn.commit()
cur.close()
conn.close()
print("\n✅ Database setup complete.")
