"""
Shared data storage. Everyone uses these functions, so DON'T change how they work
without telling the team.

Right now data is saved to a local JSON file (data/users.json) so the app works
with zero setup. Later we can swap these functions to use Firebase and nobody
else's code has to change.
"""
import json
import os

DATA_FOLDER = "data"
DATA_FILE = os.path.join(DATA_FOLDER, "users.json")


def empty_user():
    return {
        "allergies": [],
        "medications": [],
        "avoid_foods": [],
        "scan_history": [],
        "calorie_log": [],
        "calorie_goal": 2000,
        "files": [],
    }


def load_all():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_all(all_users):
    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(DATA_FILE, "w") as file:
        json.dump(all_users, file, indent=2)


def get_user(username):
    """Returns this user's data. Creates a blank profile if they're new."""
    if username == "":
        return empty_user()
    all_users = load_all()
    if username not in all_users:
        all_users[username] = empty_user()
        save_all(all_users)
    user = all_users[username]
    # Fill in any fields added after the user was created
    defaults = empty_user()
    for key in defaults:
        if key not in user:
            user[key] = defaults[key]
    return user


def save_user(username, user):
    if username == "":
        return
    all_users = load_all()
    all_users[username] = user
    save_all(all_users)
