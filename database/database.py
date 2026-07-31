import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def normalize_user_data(username, raw_data):
    """ Приводит старые форматы пользователей к новому единому формату с массивом ролей и статусом """
    if isinstance(raw_data, str):
        return {
            "password": raw_data,
            "roles": ["Administrator"] if username == "admin" else ["User"],
            "status": "Beginner"
        }
    
    roles = raw_data.get("roles")
    if not roles:
        single_role = raw_data.get("role")
        roles = [single_role] if single_role else ["User"]
    elif isinstance(roles, str):
        roles = [roles]
        
    status = raw_data.get("status", "Beginner")
    password = raw_data.get("password", "")
    
    return {
        "password": password,
        "roles": roles,
        "status": status
    }

def get_all_users():
    users = load_users()
    normalized = {}
    for username, data in users.items():
        normalized[username] = normalize_user_data(username, data)
    return normalized

def verify_user(username, password):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return False
    if isinstance(user_data, str):
        return user_data == password
    return user_data.get("password") == password

def get_user_role(username):
    users = load_users()
    user_data = users.get(username)
    norm = normalize_user_data(username, user_data)
    return norm["roles"][0] if norm["roles"] else "User"

def get_users_count():
    users = load_users()
    return len(users)

def add_user(username, password, roles, status):
    users = load_users()
    if username in users:
        return False, "Пользователь с таким логином уже существует"
    
    users[username] = {
        "password": password,
        "roles": roles if isinstance(roles, list) else [roles],
        "status": status
    }
    save_users(users)
    return True, "Аккаунт успешно создан"

def update_user(username, roles, status, new_password=None):
    users = load_users()
    if username not in users:
        return False, "Пользователь не найден"
    
    current = normalize_user_data(username, users[username])
    current["roles"] = roles if isinstance(roles, list) else [roles]
    current["status"] = status
    if new_password:
        current["password"] = new_password
        
    users[username] = current
    save_users(users)
    return True, "Данные аккаунта обновлены"

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True, "Пользователь удален"
    return False, "Пользователь не найден"