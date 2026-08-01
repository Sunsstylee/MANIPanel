import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Верховные роли управления сайтом (в нижнем регистре для сравнения)
TOP_ROLES = ["owner", "co-owner", "developer"]

# ==========================================
# РАБОТА С НАСТРОЙКАМИ САЙТА
# ==========================================

DEFAULT_SETTINGS = {
    "site_closed": False,
    "page_permissions": {
        "dashboard": ["Owner", "Co-Owner", "Developer", "Administrator", "Moderator", "Speaker", "Dobiver", "User"],
        "admin": ["Owner", "Co-Owner", "Developer", "Administrator"],
        "logs": ["Owner", "Co-Owner", "Developer"],
        "actions": ["Owner", "Co-Owner", "Developer"],
        "replacements": ["Owner", "Co-Owner", "Developer"]
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            settings = json.load(f)
            if "site_closed" not in settings:
                settings["site_closed"] = False
            if "page_permissions" not in settings:
                settings["page_permissions"] = DEFAULT_SETTINGS["page_permissions"]
            return settings
        except json.JSONDecodeError:
            return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

# ==========================================
# РАБОТА С ПОЛЬЗОВАТЕЛЯМИ
# ==========================================

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
    if isinstance(raw_data, str):
        return {
            "password": raw_data,
            "roles": ["Administrator"] if username.lower() == "admin" else ["User"],
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

def get_user_roles(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return ["User"]
    norm = normalize_user_data(username, user_data)
    return norm.get("roles", ["User"])

def is_top_admin(username):
    """Проверяет, имеет ли пользователь одну из главных ролей (Owner, Co-Owner, Developer) без учета регистра."""
    if not username:
        return False
    roles = get_user_roles(username)
    user_roles_lower = [str(r).strip().lower() for r in roles]
    return any(r in TOP_ROLES for r in user_roles_lower)

def get_user_role(username):
    roles = get_user_roles(username)
    return roles[0] if roles else "User"

def get_user_status(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return "Beginner"
    norm = normalize_user_data(username, user_data)
    return norm.get("status", "Beginner")

def get_users_count():
    users = load_users()
    return len(users)

def add_user(username, password, roles, status):
    users = load_users()
    if username in users:
        return False, "err_user_exists"
    
    users[username] = {
        "password": password,
        "roles": roles if isinstance(roles, list) else [roles],
        "status": status
    }
    save_users(users)
    return True, "msg_account_created"

def update_user(old_username, roles, status, new_password=None, new_username=None):
    users = load_users()
    if old_username not in users:
        return False, "err_user_not_found"
    
    current = normalize_user_data(old_username, users[old_username])
    target_username = old_username

    if new_username and new_username != old_username:
        if new_username in users:
            return False, "err_user_exists"
        
        del users[old_username]
        target_username = new_username

    current["roles"] = roles if isinstance(roles, list) else [roles]
    current["status"] = status
    if new_password:
        current["password"] = new_password
        
    users[target_username] = current
    save_users(users)
    return True, "msg_account_updated"

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True, "msg_user_deleted"
    return False, "err_user_not_found"