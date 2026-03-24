"""
context_builder.py
Assembles a structured context string about a profile for the LLM.
Pulls from: profiles, nodes, blocks.
"""

from data.db import get_profile, get_nodes_for_profile, get_blocks_for_node


def build_context(profile_id: str, relationship_type: str, custom_label: str) -> str:
    """
    Builds a plain-text context string about the target profile.
    This gets injected into the LLM system prompt.
    """
    profile = get_profile(profile_id)
    if not profile:
        return ""

    label = custom_label or f"{profile['name']} {profile['last_name']}"
    full_name = f"{profile['name']} {profile['last_name']}".strip()
    lines = []

    # ── Basic Info ──────────────────────────────────────
    lines.append(f"PROFILE: {full_name}")
    lines.append(f"Also known as: {', '.join(profile['nicknames']) if profile['nicknames'] else 'N/A'}")
    lines.append(f"Type: {profile['type']}")
    lines.append(f"Relationship to user: {relationship_type} (called '{label}')")

    if profile.get("bio"):
        lines.append(f"Bio: {profile['bio']}")

    if profile.get("birth_date"):
        lines.append(f"Date of birth: {profile['birth_date']}")

    if profile.get("death_date"):
        lines.append(f"Date of death: {profile['death_date']} (deceased)")

    if profile.get("place_of_birth"):
        lines.append(f"Place of birth: {profile['place_of_birth']}")

    if profile.get("current_place"):
        lines.append(f"Current location: {profile['current_place']}")

    if profile.get("gender"):
        lines.append(f"Gender: {profile['gender']}")

    if profile.get("marital_status"):
        lines.append(f"Marital status: {profile['marital_status']}")

    # ── Education ────────────────────────────────────────
    if profile.get("education"):
        lines.append("\nEDUCATION:")
        for edu in profile["education"]:
            lines.append(f"  - {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('year', '')})")

    # ── Career ───────────────────────────────────────────
    if profile.get("career"):
        lines.append("\nCAREER:")
        for job in profile["career"]:
            until = f" until {job['until']}" if job.get("until") else " (current)"
            lines.append(f"  - {job.get('role', '')} at {job.get('company', '')} since {job.get('since', '')}{until}")

    # ── Hobbies & Interests ──────────────────────────────
    if profile.get("hobbies"):
        lines.append(f"\nHOBBIES: {', '.join(profile['hobbies'])}")

    if profile.get("interests_and_favourites"):
        lines.append("\nFAVOURITES:")
        for key, val in profile["interests_and_favourites"].items():
            lines.append(f"  - {key.capitalize()}: {val}")

    # ── Achievements ─────────────────────────────────────
    if profile.get("personal_achievements"):
        lines.append("\nACHIEVEMENTS:")
        for ach in profile["personal_achievements"]:
            lines.append(f"  - {ach}")

    # ── Life Events ──────────────────────────────────────
    if profile.get("life_events"):
        lines.append("\nLIFE EVENTS:")
        for event in profile["life_events"]:
            lines.append(f"  - {event['year']}: {event['event']}")

    # ── Reflections ──────────────────────────────────────
    if profile.get("reflections_and_messages"):
        lines.append("\nREFLECTIONS & MESSAGES:")
        for ref in profile["reflections_and_messages"]:
            lines.append(f"  - \"{ref}\"")

    # ── Memories / Nodes ─────────────────────────────────
    nodes = get_nodes_for_profile(profile_id)
    if nodes:
        lines.append("\nMEMORIES & POSTS:")
        for node in nodes:
            lines.append(f"\n  [{node['type'].upper()}] {node.get('title', 'Untitled')} ({node.get('date_iso', '')})")
            blocks = get_blocks_for_node(node["id"])
            for block in blocks:
                if block["type"] == "text":
                    lines.append(f"  {block['content']['text']}")
                elif block["type"] == "image":
                    caption = block["content"].get("caption", "")
                    lines.append(f"  [PHOTO] {caption}")

    return "\n".join(lines)


def get_media_for_profile(profile_id: str, user_message: str = "") -> list:
    """
    Returns image/video blocks for a profile's nodes.
    If user_message is provided, only returns media for the matching node.
    Otherwise returns all media.
    Each item: { node_id, node_title, node_date, type, url, caption }
    """
    nodes = get_nodes_for_profile(profile_id)
    media = []
    message_lower = user_message.lower()

    for node in nodes:
        node_title = node.get("title", "").lower()
        node_date = str(node.get("date_iso", ""))

        # If user message is provided, only include media from matching node
        if user_message:
            title_words = [w for w in node_title.split() if len(w) > 3]
            if not any(word in message_lower for word in title_words):
                continue

        blocks = get_blocks_for_node(node["id"])
        for block in blocks:
            if block["type"] in ("image", "video"):
                media.append({
                    "node_id": node["id"],
                    "node_title": node.get("title", "Untitled"),
                    "node_date": node_date,
                    "type": block["type"],
                    "url": block["content"].get("url", ""),
                    "caption": block["content"].get("caption", ""),
                })
    return media


def build_multi_context(profiles_data: list) -> tuple:
    """
    Builds combined context for multiple profiles.

    profiles_data: list of dicts with keys: profile_id, relationship_type, custom_label

    Returns:
        (combined_context_string, list of profile names)
    """
    contexts = []
    names = []

    for p in profiles_data:
        context = build_context(p["profile_id"], p["relationship_type"], p["custom_label"])
        if context:
            contexts.append(context)
            profile = get_profile(p["profile_id"])
            if profile:
                names.append(p["custom_label"] or f"{profile['name']} {profile['last_name']}")

    combined = "\n\n" + ("─" * 40) + "\n\n".join(contexts)
    return combined, names
