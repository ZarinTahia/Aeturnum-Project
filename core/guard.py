"""
guard.py
Relationship access control — delegates to db.py for real DB queries.
"""

from data.db import check_relationship as db_check_relationship


def check_relationship(user_id: str, target_profile_id: str) -> dict:
    return db_check_relationship(user_id, target_profile_id)


def denial_message(result: dict, target_name: str) -> str:
    reason = result["reason"]

    if reason == "pending":
        return f"You're not connected with {target_name} — your connection request is still pending."
    elif reason == "blocked":
        return f"You don't have access to {target_name}'s profile."
    elif reason == "no_relationship":
        return f"You're not connected with {target_name} on Aeternum."
    else:
        return f"You don't have access to {target_name}'s profile."
