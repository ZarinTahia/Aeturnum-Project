"""
seed_large.py
Generates and seeds a large realistic dataset into PostgreSQL.
Produces: ~500 users, ~1000 profiles, ~3000 relationships, ~5000 nodes, ~10000 blocks.
Run: python3 -m data.seed_large
"""

import os
import json
import random
import uuid
from datetime import date, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

random.seed(42)

# ─────────────────────────────────────────────
# DATA POOLS
# ─────────────────────────────────────────────

FIRST_NAMES_FEMALE = [
    "Alice", "Emma", "Olivia", "Sophia", "Isabella", "Mia", "Amelia", "Harper",
    "Evelyn", "Abigail", "Emily", "Charlotte", "Avery", "Sofia", "Ella", "Grace",
    "Scarlett", "Victoria", "Riley", "Aria", "Lily", "Aurora", "Zoey", "Penelope",
    "Layla", "Nora", "Lillian", "Eleanor", "Hannah", "Lillian", "Addison", "Aubrey",
    "Ellie", "Stella", "Natalie", "Zoe", "Leah", "Hazel", "Violet", "Aurora",
    "Savannah", "Audrey", "Brooklyn", "Bella", "Claire", "Skylar", "Lucy", "Paisley",
    "Everly", "Anna", "Caroline", "Nova", "Genesis", "Emilia", "Kennedy", "Samantha",
    "Maya", "Willow", "Kinsley", "Naomi", "Aaliyah", "Elena", "Sarah", "Ariana",
    "Allison", "Gabriella", "Alice", "Chloe", "Autumn", "Nevaeh", "Isla", "Makayla",
    "Margaret", "Ruth", "Dorothy", "Frances", "Helen", "Edith", "Betty", "Joan",
    "Martha", "Barbara", "Patricia", "Nancy", "Sandra", "Mary", "Linda", "Susan",
]

FIRST_NAMES_MALE = [
    "Bob", "James", "Oliver", "William", "Benjamin", "Elijah", "Lucas", "Mason",
    "Logan", "Alexander", "Ethan", "Daniel", "Matthew", "Aiden", "Henry", "Joseph",
    "Jackson", "Samuel", "Sebastian", "David", "Carter", "Wyatt", "Jayden", "John",
    "Owen", "Dylan", "Luke", "Gabriel", "Anthony", "Isaac", "Grayson", "Jack",
    "Julian", "Levi", "Christopher", "Joshua", "Andrew", "Lincoln", "Michael",
    "Ryan", "Nathan", "Aaron", "Charles", "Thomas", "Caleb", "Connor", "Eli",
    "Landon", "Adrian", "Jonathan", "Nolan", "Jeremiah", "Easton", "Elias", "Colton",
    "Cameron", "Carson", "Robert", "Angel", "Maverick", "Nicholas", "Dominic",
    "Jaxon", "Greyson", "Adam", "Ian", "Austin", "Santiago", "Jordan", "Cooper",
    "Harold", "Walter", "Raymond", "Frank", "Arthur", "Albert", "Ernest", "George",
    "Howard", "Eugene", "Roy", "Ralph", "Fred", "Carl", "Gerald", "Edward",
]

LAST_NAMES = [
    "Carter", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
    "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez",
    "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
    "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera",
    "Campbell", "Mitchell", "Roberts", "Phillips", "Evans", "Turner", "Parker",
    "Collins", "Edwards", "Stewart", "Morris", "Murphy", "Rogers", "Cook", "Morgan",
    "Peterson", "Cooper", "Reed", "Bailey", "Bell", "Gomez", "Kelly", "Howard",
    "Ward", "Cox", "Diaz", "Richardson", "Wood", "Watson", "Brooks", "Bennett",
    "Gray", "James", "Reyes", "Cruz", "Hughes", "Price", "Myers", "Long", "Foster",
    "Sanders", "Ross", "Morales", "Powell", "Sullivan", "Russell", "Ortiz", "Jenkins",
]

CITIES = [
    ("New York", "USA"), ("Los Angeles", "USA"), ("Chicago", "USA"), ("Houston", "USA"),
    ("Phoenix", "USA"), ("Philadelphia", "USA"), ("San Antonio", "USA"), ("San Diego", "USA"),
    ("Dallas", "USA"), ("San Jose", "USA"), ("Austin", "USA"), ("Jacksonville", "USA"),
    ("Boston", "USA"), ("Seattle", "USA"), ("Denver", "USA"), ("Nashville", "USA"),
    ("Portland", "USA"), ("Las Vegas", "USA"), ("Memphis", "USA"), ("Baltimore", "USA"),
    ("Burlington", "USA"), ("San Francisco", "USA"), ("Atlanta", "USA"), ("Miami", "USA"),
    ("London", "UK"), ("Manchester", "UK"), ("Birmingham", "UK"), ("Leeds", "UK"),
    ("Toronto", "Canada"), ("Vancouver", "Canada"), ("Montreal", "Canada"),
    ("Sydney", "Australia"), ("Melbourne", "Australia"), ("Brisbane", "Australia"),
    ("Dublin", "Ireland"), ("Edinburgh", "Scotland"), ("Paris", "France"),
    ("Berlin", "Germany"), ("Amsterdam", "Netherlands"), ("Rome", "Italy"),
]

RELATIONSHIP_TYPES = [
    "mother", "father", "sister", "brother", "grandmother", "grandfather",
    "granddaughter", "grandson", "aunt", "uncle", "niece", "nephew",
    "daughter", "son", "wife", "husband", "partner", "friend",
    "colleague", "mentor", "cousin", "stepdaughter", "stepson", "stepmother", "stepfather",
]

HOBBIES_POOL = [
    "gardening", "knitting", "baking", "reading", "hiking", "photography",
    "cooking", "cycling", "painting", "woodworking", "fishing", "traveling",
    "yoga", "running", "swimming", "dancing", "singing", "playing piano",
    "writing", "chess", "bird watching", "pottery", "sewing", "volunteering",
    "wine tasting", "model trains", "calligraphy", "scrapbooking", "astronomy",
]

MUSIC_GENRES = [
    "Classical", "Jazz", "Indie folk", "Rock", "Blues", "Country",
    "R&B", "Soul", "Pop", "Opera", "Gospel", "Bluegrass", "Latin",
    "Swing", "Traditional Irish", "Classic rock", "Folk", "Motown",
]

FOODS = [
    "Italian", "French cuisine", "BBQ", "Apple pie", "Roast chicken",
    "Sushi", "Tacos", "Greek food", "Indian curry", "Mediterranean",
    "Southern cooking", "Seafood", "Pasta", "Dim sum", "Thai food",
]

BOOKS = [
    "The Alchemist", "Little Women", "Kitchen Confidential", "To Kill a Mockingbird",
    "Pride and Prejudice", "The Great Gatsby", "1984", "Moby Dick",
    "War and Peace", "Jane Eyre", "Wuthering Heights", "The Wright Brothers",
    "A Tale of Two Cities", "Les Misérables", "Don Quixote", "Anna Karenina",
    "Middlemarch", "Gone with the Wind", "Rebecca", "The Old Man and the Sea",
]

EDUCATION_INSTITUTIONS = [
    ("Harvard University", "B.A. History"), ("MIT", "B.Sc. Computer Science"),
    ("Yale University", "B.A. English Literature"), ("Stanford University", "M.Sc. Engineering"),
    ("Columbia University", "B.A. Political Science"), ("Princeton University", "B.A. Mathematics"),
    ("University of Chicago", "M.B.A."), ("NYU", "B.F.A. Fine Arts"),
    ("UCLA", "B.Sc. Biology"), ("University of Michigan", "B.S. Nursing"),
    ("Duke University", "M.D."), ("Cornell University", "B.Sc. Agriculture"),
    ("Dartmouth College", "B.A. Economics"), ("Brown University", "B.A. Sociology"),
    ("Georgetown University", "J.D. Law"), ("Boston University", "B.Sc. Education"),
    ("University of Vermont", "B.A. Education"), ("Culinary Institute of America", "Culinary Arts"),
    ("Yale School of Architecture", "M.Arch"), ("Juilliard School", "B.M. Music"),
    ("Northeastern University", "B.Sc. Information Systems"), ("Tufts University", "B.A. Psychology"),
]

COMPANIES = [
    ("TechCorp", "Software Engineer"), ("MediCare Health", "Registered Nurse"),
    ("GreenLeaf Architecture", "Architect"), ("Sunrise Elementary", "Teacher"),
    ("City Library", "Librarian"), ("First National Bank", "Accountant"),
    ("Hartwell Law Firm", "Lawyer"), ("Burlington Police Dept", "Officer"),
    ("St. Mary's Hospital", "Doctor"), ("Summit High School", "Principal"),
    ("Rivera Construction", "Project Manager"), ("Blue Ridge Farm", "Farmer"),
    ("Le Bernardin", "Head Chef"), ("Anchor Publishing", "Editor"),
    ("Westfield Gallery", "Curator"), ("SkyHigh Airlines", "Pilot"),
    ("Carter & Associates", "Principal Architect"), ("Maple Grove Bakery", "Baker"),
    ("Horizon Real Estate", "Agent"), ("Greenway Landscaping", "Landscaper"),
]

# ─────────────────────────────────────────────
# MEMORY TEXT TEMPLATES
# ─────────────────────────────────────────────

MEMORY_TEMPLATES = [
    # Childhood
    ("Summers at the Old House", lambda name, gender: (
        f"{name} used to spend every summer at the old family house by the lake. "
        f"{'She' if gender == 'Female' else 'He'} would wake up before sunrise to go fishing and "
        f"come back smelling of sunscreen and lake water. Those were the happiest days."
    )),
    ("First Day of School", lambda name, gender: (
        f"I remember walking {name} to school on the very first day. "
        f"{'She' if gender == 'Female' else 'He'} was nervous but tried so hard not to show it. "
        f"By the time I picked {'her' if gender == 'Female' else 'him'} up, {'she' if gender == 'Female' else 'he'} had already made three friends."
    )),
    ("Learning to Ride a Bike", lambda name, gender: (
        f"{name} learned to ride a bike in the driveway on a warm Saturday afternoon. "
        f"{'She' if gender == 'Female' else 'He'} fell seven times and got back up eight. "
        f"By sunset {'she' if gender == 'Female' else 'he'} was riding all the way down the street without any help."
    )),
    # Family
    ("Holiday Traditions", lambda name, gender: (
        f"Every holiday, {name} would start cooking two days in advance. "
        f"The whole family knew {'her' if gender == 'Female' else 'his'} recipes by heart but nobody ever dared to make them — "
        f"it just wasn't the same without {'her' if gender == 'Female' else 'him'}."
    )),
    ("Family Road Trip", lambda name, gender: (
        f"We took a road trip one summer and {name} was the one who kept everyone calm when we got lost. "
        f"{'She' if gender == 'Female' else 'He'} pulled out an old paper map — wouldn't touch the GPS — "
        f"and got us exactly where we needed to go."
    )),
    ("Sunday Dinners", lambda name, gender: (
        f"Sunday dinners at {name}'s table were legendary. "
        f"{'She' if gender == 'Female' else 'He'} cooked enough to feed twice the number of people invited "
        f"and somehow there was always just enough left over for everyone to take a plate home."
    )),
    # Career
    ("Retirement Day", lambda name, gender: (
        f"The day {name} retired, the whole office came out for {'her' if gender == 'Female' else 'his'} farewell. "
        f"{'She' if gender == 'Female' else 'He'} had spent over thirty years there and knew every person by name. "
        f"{'She' if gender == 'Female' else 'He'} cried only once — when they brought out the cake."
    )),
    ("First Big Achievement", lambda name, gender: (
        f"{name} called me the evening {'she' if gender == 'Female' else 'he'} got the news. "
        f"I had never heard {'her' if gender == 'Female' else 'him'} sound so proud yet so quiet at the same time. "
        f"It was one of those moments you hold onto forever."
    )),
    # Personality
    ("The Way They Laughed", lambda name, gender: (
        f"{name} had a laugh that filled every room. "
        f"{'She' if gender == 'Female' else 'He'} never laughed quietly — it was always full and open, "
        f"and it always made everyone else start laughing too, even when they didn't know why."
    )),
    ("Morning Routine", lambda name, gender: (
        f"Every morning {name} was up before everyone else. "
        f"{'She' if gender == 'Female' else 'He'} would make coffee, sit by the window, and read for exactly one hour before the day began. "
        f"{'She' if gender == 'Female' else 'He'} said that hour was sacred."
    )),
    ("Advice I Still Carry", lambda name, gender: (
        f"The best advice {name} ever gave me was simple: "
        f"'Do the thing that scares you a little. That's how you know it matters.' "
        f"I've thought about {'her' if gender == 'Female' else 'his'} words more times than I can count."
    )),
    ("Their Garden", lambda name, gender: (
        f"{name}'s garden was {'her' if gender == 'Female' else 'his'} sanctuary. "
        f"{'She' if gender == 'Female' else 'He'} knew every plant by its Latin name and tended to them like old friends. "
        f"People used to stop on the street just to look at it."
    )),
    # Loss / Remembrance
    ("Last Visit", lambda name, gender: (
        f"The last time I visited {name}, we sat on the porch and talked for hours about nothing in particular. "
        f"I didn't know it then, but I was already memorizing everything — "
        f"the sound of {'her' if gender == 'Female' else 'his'} voice, the way {'she' if gender == 'Female' else 'he'} held {'her' if gender == 'Female' else 'his'} tea cup."
    )),
    ("What I Miss Most", lambda name, gender: (
        f"What I miss most about {name} is the ordinary things. "
        f"{'Her' if gender == 'Female' else 'His'} phone calls on Tuesday evenings. "
        f"The way {'she' if gender == 'Female' else 'he'} always asked how I was eating. "
        f"The way {'she' if gender == 'Female' else 'he'} ended every call with 'love you, take care.'"
    )),
    # Milestones
    ("Graduation Day", lambda name, gender: (
        f"When {name} graduated, the whole family drove four hours to be there. "
        f"{'She' if gender == 'Female' else 'He'} spotted us in the crowd and waved so hard {'her' if gender == 'Female' else 'his'} cap nearly fell off. "
        f"We still have the photo on the wall."
    )),
    ("Wedding Day", lambda name, gender: (
        f"{name}'s wedding day was everything {'she' if gender == 'Female' else 'he'} had hoped for. "
        f"It rained a little in the morning and {'she' if gender == 'Female' else 'he'} just laughed and said 'good luck.' "
        f"By the ceremony the sun was out and the whole garden was glowing."
    )),
    ("New Baby", lambda name, gender: (
        f"The day {name} held {'her' if gender == 'Female' else 'his'} first grandchild, the room went quiet. "
        f"{'She' if gender == 'Female' else 'He'} looked down at that tiny face and whispered something none of us could hear. "
        f"We didn't ask. Some moments belong only to the person living them."
    )),
    # Hobbies
    ("Fishing at Dawn", lambda name, gender: (
        f"{name} took me fishing for the first time when I was seven. "
        f"We didn't catch much but {'she' if gender == 'Female' else 'he'} didn't seem to mind. "
        f"{'She' if gender == 'Female' else 'He'} said the point was never really the fish."
    )),
    ("Teaching Me to Cook", lambda name, gender: (
        f"{name} taught me to cook by letting me make mistakes. "
        f"{'She' if gender == 'Female' else 'He'} never grabbed the spoon from my hand. "
        f"{'She' if gender == 'Female' else 'He'} just stood next to me and said 'try again, you'll feel when it's right.'"
    )),
    ("Late Night Conversations", lambda name, gender: (
        f"Some of the best conversations I had with {name} happened after midnight. "
        f"The rest of the house was asleep and {'she' if gender == 'Female' else 'he'} and I would sit at the kitchen table "
        f"with tea and talk about everything — life, regrets, hopes, and the funny little things in between."
    )),
]

IMAGE_CAPTIONS = [
    "A quiet afternoon at home",
    "Summer family gathering",
    "Holiday dinner at the table",
    "Out in the backyard garden",
    "On the front porch",
    "Old family photograph",
    "At the graduation ceremony",
    "Wedding day portrait",
    "Fishing trip at dawn",
    "In the kitchen baking",
    "Sunday morning walk",
    "Celebrating a birthday",
    "Family road trip stop",
    "At the beach in summer",
    "Winter holidays together",
    "First day of school photo",
    "Retirement party",
    "New baby in the family",
    "At the workplace",
    "Garden in full bloom",
]

UNSPLASH_IMAGES = [
    "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800",
    "https://images.unsplash.com/photo-1511895426328-dc8714191011?w=800",
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800",
    "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=800",
    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800",
    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800",
    "https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800",
    "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?w=800",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800",
    "https://images.unsplash.com/photo-1521119989659-a83eee488004?w=800",
    "https://images.unsplash.com/photo-1463453091185-61582044d556?w=800",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800",
    "https://images.unsplash.com/photo-1554151228-14d9def656e4?w=800",
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=800",
    "https://images.unsplash.com/photo-1501196354995-cbb51c65aaea?w=800",
    "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=800",
    "https://images.unsplash.com/photo-1491528323818-fdd1faba62cc?w=800",
    "https://images.unsplash.com/photo-1523264653568-d3d4032d1476?w=800",
    "https://images.unsplash.com/photo-1516914943479-89db7d9ae7f2?w=800",
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def random_date(start_year: int, end_year: int) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def random_gender() -> str:
    return random.choice(["Male", "Female"])

def random_name(gender: str) -> str:
    if gender == "Female":
        return random.choice(FIRST_NAMES_FEMALE)
    return random.choice(FIRST_NAMES_MALE)

def random_city() -> tuple:
    return random.choice(CITIES)

def random_hobbies() -> list:
    return random.sample(HOBBIES_POOL, k=random.randint(2, 5))

def random_education() -> list:
    inst, deg = random.choice(EDUCATION_INSTITUTIONS)
    year = random.randint(1950, 2020)
    return [{"institution": inst, "degree": deg, "year": year}]

def random_career() -> list:
    company, role = random.choice(COMPANIES)
    since = str(random.randint(1970, 2015))
    if random.random() < 0.4:
        until = str(random.randint(int(since) + 2, 2023))
        return [{"company": company, "role": role, "since": since, "until": until}]
    return [{"company": company, "role": role, "since": since}]

def random_life_events(birth_year: int) -> list:
    events = []
    milestones = [
        (18, "Graduated high school"),
        (22, "Graduated college"),
        (25, "Started first job"),
        (30, "Got married"),
        (32, "Had first child"),
        (60, "Celebrated 30th wedding anniversary"),
        (65, "Retired"),
    ]
    for age, event in milestones:
        year = birth_year + age
        if year <= 2024 and random.random() < 0.6:
            events.append({"year": year, "event": event})
    return events


# ─────────────────────────────────────────────
# GENERATORS
# ─────────────────────────────────────────────

def generate_family(idx: int) -> dict:
    last = random.choice(LAST_NAMES)
    return {"id": f"family-{idx:04d}", "name": f"{last} Family"}

def generate_user(idx: int, family_id: str, profile_id: str) -> dict:
    gender = random_gender()
    first = random_name(gender)
    last = random.choice(LAST_NAMES)
    return {
        "id": f"user-{idx:04d}",
        "first_name": first,
        "last_name": last,
        "email": f"{first.lower()}.{last.lower()}{idx}@example.com",
        "status": "active",
        "family_id": family_id,
        "profile_id": profile_id,
        "current_profile_id": profile_id,
    }

def generate_profile(profile_id: str, user_id: str, profile_type: str, family_id: str) -> dict:
    gender = random_gender()
    first = random_name(gender)
    last = random.choice(LAST_NAMES)

    if profile_type == "CURATED":
        birth_year = random.randint(1900, 1970)
        birth = random_date(birth_year, birth_year + 1)
        death_year = random.randint(birth_year + 60, min(birth_year + 95, 2023))
        death = random_date(death_year, min(death_year + 1, 2023))
    else:
        birth_year = random.randint(1950, 2000)
        birth = random_date(birth_year, birth_year + 1)
        death = None

    city, country = random_city()
    birth_city, birth_country = random_city()

    nicknames = []
    if random.random() < 0.5:
        nicknames = [random.choice(["Grandma", "Nana", "Pop", "Gramps", "Dad", "Mom", "Buddy", "Sis", "Bro"])]

    reflections = []
    if profile_type == "CURATED" and random.random() < 0.6:
        reflections = [
            f"{first} always said the most important thing in life is showing up.",
            f"We remember {first} every time we sit down for a family meal.",
        ]

    return {
        "id": profile_id,
        "user_id": user_id,
        "type": profile_type,
        "name": first,
        "last_name": last,
        "gender": gender,
        "preferred_pronouns": "she/her" if gender == "Female" else "he/him",
        "bio": f"{first} {last} was {'a beloved' if profile_type == 'CURATED' else 'a'} {random.choice(COMPANIES)[1].lower()} who lived in {city}.",
        "birth_date": birth.isoformat(),
        "death_date": death.isoformat() if death else None,
        "place_of_birth": f"{birth_city}, {birth_country}",
        "current_place": f"{city}, {country}" if not death else None,
        "marital_status": random.choice(["Single", "Married", "Divorced", "Widowed"]),
        "ethnicity": random.choice(["Caucasian/White", "Hispanic/Latino", "Black/African American", "Asian", "Mixed", "Prefer not to say"]),
        "nicknames": nicknames,
        "education": random_education(),
        "career": random_career(),
        "hobbies": random_hobbies(),
        "interests_and_favourites": {
            "music": random.choice(MUSIC_GENRES),
            "food": random.choice(FOODS),
            "book": random.choice(BOOKS),
        },
        "personal_achievements": [f"Dedicated {random.randint(10, 40)} years to {'her' if gender == 'Female' else 'his'} career."],
        "life_events": random_life_events(birth_year),
        "reflections_and_messages": reflections,
        "is_active": True,
    }

def generate_nodes_for_profile(profile_id: str, user_id: str, profile: dict, count: int) -> list:
    nodes = []
    used_templates = random.sample(MEMORY_TEMPLATES, k=min(count, len(MEMORY_TEMPLATES)))
    for i, (title, _) in enumerate(used_templates):
        node_id = uid("node")
        city, country = random_city()
        birth_year = int(profile["birth_date"][:4])
        nodes.append({
            "id": node_id,
            "profile_id": profile_id,
            "user_id": user_id,
            "type": random.choice(["memory", "memory", "memory", "post"]),
            "title": title,
            "date_iso": random_date(birth_year + 10, min(birth_year + 80, 2024)).isoformat(),
            "status": "active",
            "location_city": city if random.random() < 0.7 else None,
            "location_country": country if random.random() < 0.7 else None,
        })
    return nodes

def generate_blocks_for_node(node: dict, profile: dict) -> list:
    name = profile["name"]
    gender = profile["gender"]
    title = node["title"]

    # Find matching template
    text = None
    for t_title, t_fn in MEMORY_TEMPLATES:
        if t_title == title:
            text = t_fn(name, gender)
            break
    if not text:
        text = f"A memory about {name}."

    caption = random.choice(IMAGE_CAPTIONS)
    img_url = random.choice(UNSPLASH_IMAGES)
    profile_slug = name.lower().replace(" ", "-")

    return [
        {
            "id": uid("block"),
            "node_id": node["id"],
            "file_id": None,
            "type": "text",
            "content": json.dumps({"text": text}),
            "status": "active",
            "order": 1,
        },
        {
            "id": uid("block"),
            "node_id": node["id"],
            "file_id": None,
            "type": "image",
            "content": json.dumps({"url": img_url, "caption": caption}),
            "status": "active",
            "order": 2,
        },
    ]


# ─────────────────────────────────────────────
# MAIN SEED
# ─────────────────────────────────────────────

def main():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()

    NUM_FAMILIES  = 100
    NUM_USERS     = 500   # ~500 user accounts
    NUM_CURATED   = 500   # ~500 deceased/historical profiles
    NODES_PER_PROFILE = 10  # ~5000 nodes total

    print(f"Generating {NUM_FAMILIES} families, {NUM_USERS} users, {NUM_CURATED} curated profiles...")
    print(f"Expected: ~{(NUM_USERS + NUM_CURATED) * NODES_PER_PROFILE} nodes, ~{(NUM_USERS + NUM_CURATED) * NODES_PER_PROFILE * 2} blocks")

    # ── Families ────────────────────────────────
    families = [generate_family(i) for i in range(1, NUM_FAMILIES + 1)]
    for f in families:
        cur.execute(
            "INSERT INTO families (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
            (f["id"], f["name"])
        )
    print(f"✅ {len(families)} families inserted.")

    # ── Users + their own profiles ───────────────
    users = []
    user_profiles = []
    for i in range(1, NUM_USERS + 1):
        pid = f"profile-u{i:04d}"
        uid_str = f"user-{i:04d}"
        fam = random.choice(families)
        user = generate_user(i, fam["id"], pid)
        profile = generate_profile(pid, uid_str, "USER", fam["id"])
        users.append(user)
        user_profiles.append((profile, uid_str))

    for u in users:
        cur.execute("""
            INSERT INTO users (id, first_name, last_name, email, status, family_id, profile_id, current_profile_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """, (u["id"], u["first_name"], u["last_name"], u["email"],
              u["status"], u["family_id"], u["profile_id"], u["current_profile_id"]))
    print(f"✅ {len(users)} users inserted.")

    # ── Curated profiles (deceased/historical) ───
    curated_profiles = []
    for i in range(1, NUM_CURATED + 1):
        pid = f"profile-c{i:04d}"
        owner = random.choice(users)
        profile = generate_profile(pid, owner["id"], "CURATED", owner["family_id"])
        curated_profiles.append((profile, owner["id"]))

    all_profiles = user_profiles + curated_profiles

    # Insert all profiles
    for profile, _ in all_profiles:
        cur.execute("""
            INSERT INTO profiles (
                id, user_id, type, name, last_name, bio, birth_date, death_date,
                gender, preferred_pronouns, place_of_birth, current_place,
                marital_status, ethnicity, nicknames, education, career, hobbies,
                interests_and_favourites, personal_achievements, life_events,
                reflections_and_messages, is_active
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO NOTHING
        """, (
            profile["id"], profile["user_id"], profile["type"],
            profile["name"], profile["last_name"], profile["bio"],
            profile["birth_date"], profile["death_date"],
            profile["gender"], profile["preferred_pronouns"],
            profile["place_of_birth"], profile["current_place"],
            profile["marital_status"], profile["ethnicity"],
            json.dumps(profile["nicknames"]),
            json.dumps(profile["education"]),
            json.dumps(profile["career"]),
            json.dumps(profile["hobbies"]),
            json.dumps(profile["interests_and_favourites"]),
            json.dumps(profile["personal_achievements"]),
            json.dumps(profile["life_events"]),
            json.dumps(profile["reflections_and_messages"]),
            profile["is_active"],
        ))
    print(f"✅ {len(all_profiles)} profiles inserted.")
    conn.commit()

    # ── Relationships ────────────────────────────
    seen_pairs = set()
    rel_count = 0
    for u in users:
        my_profile_id = u["profile_id"]
        # Connect to 4–8 random other profiles
        targets = random.sample(all_profiles, k=random.randint(4, 8))
        for profile, _ in targets:
            to_pid = profile["id"]
            if to_pid == my_profile_id:
                continue
            pair = (my_profile_id, to_pid)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            rel_type = random.choice(RELATIONSHIP_TYPES)
            status = random.choices(["connected", "connected", "pending"], weights=[7, 2, 1])[0]
            custom = profile["name"] if random.random() < 0.4 else None
            rel_id = uid("rel")
            cur.execute("""
                INSERT INTO relationships (id, from_profile_id, to_profile_id, family_id, type, status, custom_label)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (rel_id, my_profile_id, to_pid, u["family_id"], rel_type, status, custom))
            rel_count += 1
    conn.commit()
    print(f"✅ {rel_count} relationships inserted.")

    # ── Nodes + Blocks ───────────────────────────
    node_count = 0
    block_count = 0
    batch_size = 100
    batch_nodes = []
    batch_blocks = []

    for profile, contributor_user_id in all_profiles:
        nodes = generate_nodes_for_profile(profile["id"], contributor_user_id, profile, NODES_PER_PROFILE)
        for node in nodes:
            batch_nodes.append(node)
            blocks = generate_blocks_for_node(node, profile)
            batch_blocks.extend(blocks)

        # Flush in batches to avoid huge transactions
        if len(batch_nodes) >= batch_size:
            for node in batch_nodes:
                cur.execute("""
                    INSERT INTO nodes (id, profile_id, user_id, type, title, date_iso, status, location_city, location_country)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (node["id"], node["profile_id"], node["user_id"], node["type"],
                      node["title"], node["date_iso"], node["status"],
                      node["location_city"], node["location_country"]))
            node_count += len(batch_nodes)

            for block in batch_blocks:
                cur.execute("""
                    INSERT INTO blocks (id, node_id, file_id, type, content, status, "order")
                    VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (block["id"], block["node_id"], block["file_id"],
                      block["type"], block["content"], block["status"], block["order"]))
            block_count += len(batch_blocks)

            conn.commit()
            print(f"  ... {node_count} nodes, {block_count} blocks so far")
            batch_nodes = []
            batch_blocks = []

    # Flush remaining
    for node in batch_nodes:
        cur.execute("""
            INSERT INTO nodes (id, profile_id, user_id, type, title, date_iso, status, location_city, location_country)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """, (node["id"], node["profile_id"], node["user_id"], node["type"],
              node["title"], node["date_iso"], node["status"],
              node["location_city"], node["location_country"]))
    node_count += len(batch_nodes)

    for block in batch_blocks:
        cur.execute("""
            INSERT INTO blocks (id, node_id, file_id, type, content, status, "order")
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """, (block["id"], block["node_id"], block["file_id"],
              block["type"], block["content"], block["status"], block["order"]))
    block_count += len(batch_blocks)

    conn.commit()
    print(f"✅ {node_count} nodes inserted.")
    print(f"✅ {block_count} blocks inserted.")

    cur.close()
    conn.close()
    print("\n✅ Large dataset seed complete.")
    print(f"\nSummary:")
    print(f"  Families:   {len(families)}")
    print(f"  Users:      {len(users)}")
    print(f"  Profiles:   {len(all_profiles)}")
    print(f"  Relations:  {rel_count}")
    print(f"  Nodes:      {node_count}")
    print(f"  Blocks:     {block_count}")


if __name__ == "__main__":
    main()
