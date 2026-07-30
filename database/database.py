import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_user(username, password):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return False
    # Поддержка и старого формата ("admin": "12345"), и нового с объектом
    if isinstance(user_data, str):
        return user_data == password
    return user_data.get("password") == password

def get_user_role(username):
    users = load_users()
    user_data = users.get(username)
    if isinstance(user_data, dict):
        return user_data.get("role", "User")
    return "Administrator" if username == "admin" else "User"

def get_users_count():
    users = load_users()
    return len(users)