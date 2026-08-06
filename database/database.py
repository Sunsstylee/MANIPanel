import json
import os
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

TOP_ROLES = ["owner", "co-owner", "developer"]

DEFAULT_SETTINGS = {
    "site_closed": False,
    "page_permissions": {
        "dashboard": ["Owner", "Co-Owner", "Developer", "Administrator", "Moderator", "Speaker", "Dobiver", "User"],
        "techpanel": ["Owner", "Co-Owner", "Developer", "Administrator"],
        "logs": ["Owner", "Co-Owner", "Developer"],
        "actions": ["Owner", "Co-Owner", "Developer"],
        "replacements": ["Owner", "Co-Owner", "Developer"],
        "clients": ["Owner", "Co-Owner", "Developer"]
    }
}

class Replacement(db.Model):
    __tablename__ = 'replacements'
    
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(100), unique=True, nullable=False)
    steam_name = db.Column(db.String(100), nullable=True)
    steam_url = db.Column(db.String(255), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    inv_tradable = db.Column(db.String(50), default='0.00')
    inv_sub = db.Column(db.String(50), default='0.00')
    games = db.Column(db.String(100), default='csgo')
    swapped_offers = db.Column(db.Integer, default=0)
    algorithm = db.Column(db.Integer, default=4)
    min_dep = db.Column(db.Integer, default=50)
    time = db.Column(db.String(50), nullable=True)
    date = db.Column(db.String(50), nullable=True)
    spammer = db.Column(db.String(100), nullable=True)
    note = db.Column(db.String(255), default='')

    def to_dict(self):
        return {
            'id': self.id,
            'steam_id': self.steam_id,
            'steam_name': self.steam_name or self.steam_id,
            'steam_url': self.steam_url,
            'avatar_url': self.avatar_url,
            'inv_tradable': self.inv_tradable,
            'inv_sub': self.inv_sub,
            'games': self.games.split(',') if self.games else [],
            'swapped_offers': self.swapped_offers,
            'algorithm': self.algorithm,
            'min_dep': self.min_dep,
            'time': self.time,
            'date': self.date,
            'spammer': self.spammer,
            'note': self.note
        }

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if Replacement.query.count() == 0:
            initial_data = [
                Replacement(
                    steam_id='76561198000000001',
                    steam_name='SBY139',
                    steam_url='https://steamcommunity.com/profiles/76561198000000001',
                    avatar_url='https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg',
                    inv_tradable='23.51',
                    inv_sub='8.52',
                    games='dota2,csgo,rust',
                    swapped_offers=0,
                    algorithm=4,
                    min_dep=50,
                    time='12:41:30',
                    date='6.8.2026',
                    spammer='Sunsstylee',
                    note=''
                ),
                Replacement(
                    steam_id='76561198000000002',
                    steam_name='cRaZyBaNaNツ',
                    steam_url='https://steamcommunity.com/profiles/76561198000000002',
                    avatar_url='https://avatars.steamstatic.com/b5bd569220fa447289659b967d26425032a4e9ef_full.jpg',
                    inv_tradable='236.91',
                    inv_sub='0.85',
                    games='dota2,csgo',
                    swapped_offers=0,
                    algorithm=4,
                    min_dep=50,
                    time='0:9:44',
                    date='3.8.2026',
                    spammer='Sunsstylee',
                    note=''
                )
            ]
            db.session.bulk_save_objects(initial_data)
            db.session.commit()

def format_balance(val):
    if val is None or str(val).strip() == "":
        return "$0.00"
    val_str = str(val).strip().replace(',', '.')
    cleaned = ''.join(c for c in val_str if c in ['.', '-'] or c.isdigit())
    try:
        num = float(cleaned)
        num_rounded = round(num, 3)
        if round(num_rounded * 1000) % 10 != 0:
            formatted = f"{num_rounded:.3f}"
        else:
            formatted = f"{num_rounded:.2f}"
        return f"${formatted}"
    except ValueError:
        return "$0.00"

def generate_default_finance_history(current_amount=0.0):
    today = datetime.now()
    history = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime("%d.%m")
        amount = round(float(current_amount), 2) if i == 0 else 0.0
        history.append({"date": date_str, "amount": amount})
    return history

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
            else:
                if "admin" in settings["page_permissions"]:
                    settings["page_permissions"]["techpanel"] = settings["page_permissions"].pop("admin")
                    save_settings(settings)
            return settings
        except json.JSONDecodeError:
            return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

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

def log_user_action(username, action_key, status_key="status_success", details=None):
    users = load_users()
    if username not in users or isinstance(users[username], str):
        return
    
    actions = users[username].get("recent_actions", [])
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    entry = {
        "action": action_key,
        "date": now_str,
        "status": status_key
    }
    if details:
        entry["details"] = details
        
    actions.insert(0, entry)
    users[username]["recent_actions"] = actions[:10]
    save_users(users)

def record_finance_snapshot(username, amount=None):
    users = load_users()
    if username not in users or isinstance(users[username], str):
        return
    
    user = users[username]
    if amount is None:
        b_str = str(user.get("balance", "0")).replace('$', '').replace(',', '').strip()
        try:
            amount = float(b_str)
        except ValueError:
            amount = 0.0

    today_str = datetime.now().strftime("%d.%m")
    history = user.get("finance_history", [])
    
    if len(history) < 7:
        full_history = generate_default_finance_history(amount)
        hist_dict = {item["date"]: item["amount"] for item in history}
        for item in full_history:
            if item["date"] in hist_dict:
                item["amount"] = hist_dict[item["date"]]
        item_today = next((x for x in full_history if x["date"] == today_str), None)
        if item_today:
            item_today["amount"] = round(amount, 2)
        history = full_history
    else:
        updated = False
        for entry in history:
            if entry.get("date") == today_str:
                entry["amount"] = round(amount, 2)
                updated = True
                break
        if not updated:
            history.append({"date": today_str, "amount": round(amount, 2)})

    users[username]["finance_history"] = history[-7:]
    save_users(users)

def normalize_user_data(username, raw_data):
    if isinstance(raw_data, str):
        return {
            "password": raw_data,
            "roles": ["Administrator"] if username.lower() == "admin" else ["User"],
            "status": "Beginner",
            "balance": "$0.00",
            "finance_history": generate_default_finance_history(0.0),
            "recent_actions": []
        }
    
    roles = raw_data.get("roles")
    if not roles:
        single_role = raw_data.get("role")
        roles = [single_role] if single_role else ["User"]
    elif isinstance(roles, str):
        roles = [roles]
        
    status = raw_data.get("status", "Beginner")
    password = raw_data.get("password", "")
    balance = raw_data.get("balance", "$0.00")
    
    b_val = 0.0
    try:
        b_val = float(str(balance).replace('$', '').replace(',', '').strip())
    except ValueError:
        pass

    finance_history = raw_data.get("finance_history", [])
    if not finance_history or len(finance_history) < 7:
        finance_history = generate_default_finance_history(b_val)

    recent_actions = raw_data.get("recent_actions", [])
    
    return {
        "password": password,
        "roles": roles,
        "status": status,
        "balance": format_balance(balance),
        "finance_history": finance_history[-7:],
        "recent_actions": recent_actions[:10]
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
    
    pwd = user_data if isinstance(user_data, str) else user_data.get("password")
    if pwd == password:
        log_user_action(username, "action_login", "status_success", details="details_login_success")
        record_finance_snapshot(username)
        return True
    return False

def get_user_roles(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return ["User"]
    norm = normalize_user_data(username, user_data)
    roles = norm.get("roles", ["User"])
    return [roles] if isinstance(roles, str) else roles

def is_top_admin(username):
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

def get_user_finance_data(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        default_hist = generate_default_finance_history(0.0)
        return {
            "labels": [i["date"] for i in default_hist],
            "values": [i["amount"] for i in default_hist]
        }
    norm = normalize_user_data(username, user_data)
    history = norm.get("finance_history", [])
    labels = [item.get("date", "") for item in history]
    values = [item.get("amount", 0) for item in history]
    return {"labels": labels, "values": values}

def get_user_recent_actions(username):
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return []
    norm = normalize_user_data(username, user_data)
    return norm.get("recent_actions", [])

def get_users_count():
    users = load_users()
    return len(users)

def get_sidebar_stats():
    users = get_all_users()
    total_balance = 0.0
    for u in users.values():
        b_str = str(u.get('balance', '0')).replace('$', '').replace(',', '').strip()
        try:
            total_balance += float(b_str)
        except ValueError:
            pass

    return {
        "users_count": len(users),
        "total_logs": 0,
        "active_usd": format_balance(total_balance)
    }

def get_top_users(limit=10):
    users = get_all_users()
    sorted_users = []
    for username, data in users.items():
        b_str = str(data.get('balance', '0')).replace('$', '').replace(',', '').strip()
        try:
            val = float(b_str)
        except ValueError:
            val = 0.0
        sorted_users.append({'username': username, 'amount': data.get('balance', '$0.00'), 'val': val})
    
    sorted_users.sort(key=lambda x: x['val'], reverse=True)
    top = []
    for idx, u in enumerate(sorted_users[:limit], 1):
        top.append({
            'rank': idx,
            'username': u['username'],
            'amount': u['amount']
        })
    return top

def get_top_speakers(limit=10):
    users = get_all_users()
    speakers = []
    
    for username, data in users.items():
        roles_lower = [str(r).lower() for r in data.get('roles', [])]
        if 'speaker' in roles_lower or 'спикер' in roles_lower:
            success_count = sum(1 for a in data.get('recent_actions', []) if a.get('status') in ['status_success', 'success', 'успешно'])
            speakers.append({'username': username, 'logs_count': success_count})

    speakers.sort(key=lambda x: x['logs_count'], reverse=True)
    top = []
    for idx, s in enumerate(speakers[:limit], 1):
        top.append({
            'rank': idx,
            'username': s['username'],
            'logs_count': s['logs_count']
        })
    return top

def add_user(username, password, roles, status, balance="$0.00"):
    users = load_users()
    if username in users:
        return False, "err_user_exists"
    
    formatted_b = format_balance(balance)
    b_val = 0.0
    try:
        b_val = float(str(formatted_b).replace('$', '').replace(',', '').strip())
    except ValueError:
        pass

    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    users[username] = {
        "password": password,
        "roles": roles if isinstance(roles, list) else [roles],
        "status": status,
        "balance": formatted_b,
        "finance_history": generate_default_finance_history(b_val),
        "recent_actions": [{
            "action": "action_login",
            "date": now_str,
            "status": "status_success",
            "details": "details_account_created"
        }]
    }
    save_users(users)
    return True, "msg_account_created"

def update_user(old_username, roles, status, new_password=None, new_username=None, balance=None):
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

    roles_list = roles if isinstance(roles, list) else [roles]
    
    changes = []
    if current.get("roles") != roles_list:
        changes.append("details_role_changed")
    if current.get("status") != status:
        changes.append("details_status_changed")
    if new_password:
        changes.append("details_password_changed")
    if balance is not None and current.get("balance") != format_balance(balance):
        changes.append(f"details_balance: {format_balance(balance)}")

    current["roles"] = roles_list
    current["status"] = status
    if new_password:
        current["password"] = new_password
    if balance is not None:
        current["balance"] = format_balance(balance)
        
    users[target_username] = current
    save_users(users)

    details_str = ", ".join(changes) if changes else "details_profile_updated"
    log_user_action(target_username, "action_settings_update", "status_success", details=details_str)

    if balance is not None:
        try:
            b_val = float(str(balance).replace('$', '').replace(',', '').strip())
            record_finance_snapshot(target_username, b_val)
        except ValueError:
            pass

    return True, "msg_account_updated"

def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        return True, "msg_user_deleted"
    return False, "err_user_not_found"