import json
import os

USERS_FILE = "subscribers.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def add_user(user_id: int):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def remove_user(user_id: int):
    users = load_users()
    if user_id in users:
        users.remove(user_id)
        save_users(users)
