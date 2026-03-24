"""
mock_data.py
Simulates the Aeternum PostgreSQL schema in memory.
Structure mirrors: users, profiles, relationships, nodes, blocks.
"""

from datetime import date

# ─────────────────────────────────────────────
# USERS
# mirrors: users table
# ─────────────────────────────────────────────
USERS = {
    "user-001": {
        "id": "user-001",
        "first_name": "Alice",
        "last_name": "Carter",
        "email": "alice@example.com",
        "status": "active",
        "profile_id": "profile-001",
        "current_profile_id": "profile-001",
        "family_id": "family-001",
    },
    "user-002": {
        "id": "user-002",
        "first_name": "Bob",
        "last_name": "Carter",
        "email": "bob@example.com",
        "status": "active",
        "profile_id": "profile-002",
        "current_profile_id": "profile-002",
        "family_id": "family-001",
    },
}

# ─────────────────────────────────────────────
# FAMILIES
# mirrors: families table
# ─────────────────────────────────────────────
FAMILIES = {
    "family-001": {
        "id": "family-001",
        "name": "Carter Family",
    }
}

# ─────────────────────────────────────────────
# PROFILES
# mirrors: profiles table
# type: USER (living) | CURATED (deceased / historical)
# ─────────────────────────────────────────────
PROFILES = {
    # Alice's own profile
    "profile-001": {
        "id": "profile-001",
        "user_id": "user-001",
        "type": "USER",
        "name": "Alice",
        "last_name": "Carter",
        "bio": "Alice is a software engineer who loves hiking and photography.",
        "birth_date": date(1990, 4, 12),
        "death_date": None,
        "gender": "Female",
        "preferred_pronouns": "she/her",
        "place_of_birth": "Boston, MA",
        "current_place": "San Francisco, CA",
        "marital_status": "Single",
        "ethnicity": "Caucasian/White",
        "nicknames": ["Ali"],
        "education": [
            {"institution": "MIT", "degree": "B.Sc. Computer Science", "year": 2012}
        ],
        "career": [
            {"company": "TechCorp", "role": "Senior Engineer", "since": "2018"}
        ],
        "hobbies": ["hiking", "photography", "cooking"],
        "interests_and_favourites": {
            "music": "Indie folk",
            "food": "Italian",
            "book": "The Alchemist",
        },
        "personal_achievements": ["Built open-source library with 2k stars"],
        "life_events": [
            {"year": 2012, "event": "Graduated from MIT"},
            {"year": 2018, "event": "Moved to San Francisco"},
        ],
        "reflections_and_messages": [],
        "is_active": True,
    },

    # Bob's own profile
    "profile-002": {
        "id": "profile-002",
        "user_id": "user-002",
        "type": "USER",
        "name": "Bob",
        "last_name": "Carter",
        "bio": "Bob is Alice's brother. He is a chef based in New York.",
        "birth_date": date(1988, 9, 3),
        "death_date": None,
        "gender": "Male",
        "preferred_pronouns": "he/him",
        "place_of_birth": "Boston, MA",
        "current_place": "New York, NY",
        "marital_status": "Married",
        "ethnicity": "Caucasian/White",
        "nicknames": ["Bobby"],
        "education": [
            {"institution": "Culinary Institute of America", "degree": "Culinary Arts", "year": 2010}
        ],
        "career": [
            {"company": "Le Bernardin", "role": "Head Chef", "since": "2015"}
        ],
        "hobbies": ["cooking", "cycling", "wine tasting"],
        "interests_and_favourites": {
            "music": "Jazz",
            "food": "French cuisine",
            "book": "Kitchen Confidential",
        },
        "personal_achievements": ["Michelin star nomination 2022"],
        "life_events": [
            {"year": 2010, "event": "Graduated from Culinary Institute"},
            {"year": 2015, "event": "Became Head Chef at Le Bernardin"},
        ],
        "reflections_and_messages": [],
        "is_active": True,
    },

    # Grandmother — CURATED (deceased)
    "profile-003": {
        "id": "profile-003",
        "user_id": "user-001",   # Alice manages this profile
        "type": "CURATED",
        "name": "Rose",
        "last_name": "Carter",
        "bio": "Rose was a beloved grandmother, schoolteacher, and avid gardener who lived in Vermont.",
        "birth_date": date(1932, 6, 15),
        "death_date": date(2018, 11, 2),
        "gender": "Female",
        "preferred_pronouns": "she/her",
        "place_of_birth": "Burlington, VT",
        "current_place": None,
        "marital_status": "Widowed",
        "ethnicity": "Caucasian/White",
        "nicknames": ["Grandma Rose", "Nana"],
        "education": [
            {"institution": "University of Vermont", "degree": "B.A. Education", "year": 1954}
        ],
        "career": [
            {"company": "Burlington Elementary School", "role": "Schoolteacher", "since": "1955", "until": "1990"}
        ],
        "hobbies": ["gardening", "knitting", "baking", "reading"],
        "interests_and_favourites": {
            "music": "Classical, especially Chopin",
            "food": "Apple pie and roast chicken",
            "book": "Little Women",
        },
        "personal_achievements": [
            "Taught over 1,000 children during her 35-year career",
            "Won the Vermont Garden Show three years in a row",
        ],
        "life_events": [
            {"year": 1954, "event": "Graduated from University of Vermont"},
            {"year": 1956, "event": "Married Harold Carter"},
            {"year": 1960, "event": "Had her first child"},
            {"year": 1990, "event": "Retired from teaching after 35 years"},
            {"year": 2005, "event": "Harold (husband) passed away"},
            {"year": 2018, "event": "Passed away peacefully at home, aged 86"},
        ],
        "reflections_and_messages": [
            "She always said: 'A garden is a friend you can visit any time.'",
            "Her apple pie recipe has been passed down through three generations.",
        ],
        "is_active": True,
    },

    # Father — USER (living)
    "profile-004": {
        "id": "profile-004",
        "user_id": "user-001",  # Alice manages this profile
        "type": "USER",
        "name": "Harold",
        "last_name": "Carter Jr.",
        "bio": "Harold Jr. is Alice and Bob's father, a retired architect living in Vermont.",
        "birth_date": date(1958, 3, 22),
        "death_date": None,
        "gender": "Male",
        "preferred_pronouns": "he/him",
        "place_of_birth": "Burlington, VT",
        "current_place": "Burlington, VT",
        "marital_status": "Divorced",
        "ethnicity": "Caucasian/White",
        "nicknames": ["Dad", "Harry"],
        "education": [
            {"institution": "Yale School of Architecture", "degree": "M.Arch", "year": 1983}
        ],
        "career": [
            {"company": "Carter & Associates", "role": "Principal Architect", "since": "1985", "until": "2020"}
        ],
        "hobbies": ["woodworking", "fishing", "model trains"],
        "interests_and_favourites": {
            "music": "Classic rock",
            "food": "BBQ",
            "book": "The Wright Brothers",
        },
        "personal_achievements": [
            "Designed over 200 residential buildings in New England",
        ],
        "life_events": [
            {"year": 1983, "event": "Graduated from Yale"},
            {"year": 1985, "event": "Founded Carter & Associates"},
            {"year": 2020, "event": "Retired"},
        ],
        "reflections_and_messages": [],
        "is_active": True,
    },

    # A stranger — no relationship with Alice
    "profile-005": {
        "id": "profile-005",
        "user_id": "user-002",
        "type": "USER",
        "name": "Stranger",
        "last_name": "Person",
        "bio": "Someone Alice has no connection with.",
        "birth_date": date(1995, 1, 1),
        "death_date": None,
        "gender": "Male",
        "preferred_pronouns": "he/him",
        "place_of_birth": "Unknown",
        "current_place": "Unknown",
        "marital_status": "Single",
        "ethnicity": "Prefer not to say",
        "nicknames": [],
        "education": [],
        "career": [],
        "hobbies": [],
        "interests_and_favourites": {},
        "personal_achievements": [],
        "life_events": [],
        "reflections_and_messages": [],
        "is_active": True,
    },
}

# ─────────────────────────────────────────────
# RELATIONSHIPS
# mirrors: relationships table
# status: pending | connected | blocked | ignored | disconnected
# type: one of 57 RelationshipType values
# ─────────────────────────────────────────────
RELATIONSHIPS = [
    {
        "id": "rel-001",
        "from_profile_id": "profile-001",   # Alice
        "to_profile_id": "profile-003",     # Grandma Rose
        "type": "granddaughter",
        "status": "connected",
        "custom_label": "Grandma Rose",
        "family_id": "family-001",
    },
    {
        "id": "rel-002",
        "from_profile_id": "profile-001",   # Alice
        "to_profile_id": "profile-004",     # Father Harold
        "type": "father",
        "status": "connected",
        "custom_label": "Dad",
        "family_id": "family-001",
    },
    {
        "id": "rel-003",
        "from_profile_id": "profile-001",   # Alice
        "to_profile_id": "profile-002",     # Bob
        "type": "brother",
        "status": "pending",                # not yet connected
        "custom_label": None,
        "family_id": "family-001",
    },
    # No relationship between Alice (profile-001) and Stranger (profile-005)
]

# ─────────────────────────────────────────────
# NODES (memories / posts)
# mirrors: nodes table
# type: post | memory | document | media
# ─────────────────────────────────────────────
NODES = [
    {
        "id": "node-001",
        "profile_id": "profile-003",        # about Grandma Rose
        "user_id": "user-001",              # contributed by Alice
        "type": "memory",
        "title": "Grandma's Apple Pie",
        "date_iso": date(2010, 12, 25),
        "status": "active",
        "location_city": "Burlington",
        "location_country": "USA",
    },
    {
        "id": "node-002",
        "profile_id": "profile-003",        # about Grandma Rose
        "user_id": "user-002",              # contributed by Bob
        "type": "memory",
        "title": "Learning to Garden with Nana",
        "date_iso": date(2005, 7, 4),
        "status": "active",
        "location_city": "Burlington",
        "location_country": "USA",
    },
    {
        "id": "node-003",
        "profile_id": "profile-003",        # about Grandma Rose
        "user_id": "user-001",
        "type": "post",
        "title": "Remembering Nana on her birthday",
        "date_iso": date(2019, 6, 15),
        "status": "active",
        "location_city": None,
        "location_country": None,
    },
    {
        "id": "node-004",
        "profile_id": "profile-004",        # about Father Harold
        "user_id": "user-001",
        "type": "memory",
        "title": "Dad's woodworking workshop",
        "date_iso": date(2015, 8, 10),
        "status": "active",
        "location_city": "Burlington",
        "location_country": "USA",
    },
]

# ─────────────────────────────────────────────
# BLOCKS (content inside nodes)
# mirrors: blocks table
# type: text | image | video | audio | file | embed
# ─────────────────────────────────────────────
BLOCKS = [
    {
        "id": "block-001",
        "node_id": "node-001",
        "type": "text",
        "order": 1,
        "status": "active",
        "content": {
            "text": (
                "Every Christmas, Grandma Rose would wake up at 5am to start her famous apple pie. "
                "The whole house smelled of cinnamon and butter. She taught me her secret — "
                "always use Granny Smith apples and never skip the lemon zest."
            )
        },
    },
    {
        "id": "block-002",
        "node_id": "node-002",
        "type": "text",
        "order": 1,
        "status": "active",
        "content": {
            "text": (
                "Nana had a garden that stretched the full length of her backyard. "
                "She knew every plant by name. She would say: 'Bobby, a garden teaches you patience — "
                "you plant today and trust tomorrow.' I think about that every time I plate a dish."
            )
        },
    },
    {
        "id": "block-003",
        "node_id": "node-003",
        "type": "text",
        "order": 1,
        "status": "active",
        "content": {
            "text": (
                "Today would have been Nana's 87th birthday. She lived a full, beautiful life. "
                "35 years of teaching, a garden she loved, and a family she held together with warmth and patience. "
                "We miss you every day, Grandma Rose."
            )
        },
    },
    {
        "id": "block-004",
        "node_id": "node-004",
        "type": "text",
        "order": 1,
        "status": "active",
        "content": {
            "text": (
                "Dad's workshop smells like sawdust and machine oil. "
                "He spent every weekend in there building furniture — a rocking chair for Grandma, "
                "bookshelves for our rooms. He never used instructions. He said 'measure twice, cut once' "
                "and somehow it always worked."
            )
        },
    },
]


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def get_user(user_id: str):
    return USERS.get(user_id)

def get_profile(profile_id: str):
    return PROFILES.get(profile_id)

def get_connected_profiles(user_id: str) -> list[dict]:
    """Return all profiles that this user's active profile has a CONNECTED relationship with."""
    user = get_user(user_id)
    if not user:
        return []
    my_profile_id = user["current_profile_id"]
    connected = []
    for rel in RELATIONSHIPS:
        if rel["from_profile_id"] == my_profile_id and rel["status"] == "connected":
            profile = get_profile(rel["to_profile_id"])
            if profile:
                connected.append({
                    "profile": profile,
                    "relationship_type": rel["type"],
                    "custom_label": rel["custom_label"],
                })
    return connected

def get_nodes_for_profile(profile_id: str) -> list[dict]:
    """Return all active nodes (memories/posts) for a given profile."""
    return [n for n in NODES if n["profile_id"] == profile_id and n["status"] == "active"]

def get_blocks_for_node(node_id: str) -> list[dict]:
    """Return all active blocks for a given node."""
    return [b for b in BLOCKS if b["node_id"] == node_id and b["status"] == "active"]
