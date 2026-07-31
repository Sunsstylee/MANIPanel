from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.database import get_all_users, add_user, update_user, delete_user, get_users_count
from locales.i18n import t

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

VALID_ROLES = ["Owner", "Administrator", "Moderator", "Speaker", "Dobiver", "User"]
VALID_STATUSES = ["Beginner", "Worker", "Pro"]

@admin_bp.route('/')
def admin_panel():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    users = get_all_users()
    
    sidebar_stats = {
        "users_count": len(users),
        "total_logs": 0,
        "active_usd": "0.00"
    }
    
    lang = session.get('lang', 'ru')
    return render_template('admpanel/admin.html', 
                           users=users,
                           sidebar_stats=sidebar_stats, 
                           t=lambda key: t(key, lang),
                           roles=VALID_ROLES,
                           statuses=VALID_STATUSES)

@admin_bp.route('/api/users', methods=['GET'])
def api_get_users():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = get_all_users()
    result = []
    for username, data in users.items():
        result.append({
            "username": username,
            "roles": data["roles"],
            "status": data["status"]
        })
        
    return jsonify({"users": result})

@admin_bp.route('/api/users/create', methods=['POST'])
def api_create_user():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    roles = data.get('roles', [])
    status = data.get('status', 'Beginner')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Заполните логин и пароль'}), 400

    if not roles:
        roles = ["User"]

    success, msg = add_user(username, password, roles, status)
    return jsonify({'success': success, 'message': msg})

@admin_bp.route('/api/users/update', methods=['POST'])
def api_update_user():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    roles = data.get('roles', [])
    status = data.get('status', 'Beginner')
    new_password = data.get('password', '').strip()

    if not username:
        return jsonify({'success': False, 'message': 'Пользователь не указан'}), 400

    if not roles:
        roles = ["User"]

    success, msg = update_user(username, roles, status, new_password if new_password else None)
    return jsonify({'success': success, 'message': msg})

@admin_bp.route('/api/users/delete', methods=['POST'])
def api_delete_user():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json() or {}
    username = data.get('username', '').strip()

    if username == session.get('username'):
        return jsonify({'success': False, 'message': 'Нельзя удалить собственный аккаунт'}), 400

    success, msg = delete_user(username)
    return jsonify({'success': success, 'message': msg})