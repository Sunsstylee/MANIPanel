from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.database import (
    get_all_users, add_user, update_user, delete_user, get_users_count,
    load_settings, save_settings, is_top_admin, get_user_roles, TOP_ROLES,
    format_balance
)
from locales.i18n import t

techpanel_bp = Blueprint('techpanel', __name__, url_prefix='/techpanel')

# Единый список всех ролей сайта
VALID_ROLES = ["Owner", "Co-Owner", "Developer", "Administrator", "Moderator", "Speaker", "Dobiver", "User"]
VALID_STATUSES = ["Beginner", "Worker", "Pro"]

@techpanel_bp.route('/')
def techpanel():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    current_username = session.get('username')
    users = get_all_users()
    settings = load_settings()
    
    user_roles = get_user_roles(current_username)
    if isinstance(user_roles, str):
        user_roles = [user_roles]
        
    user_roles_lower = {str(r).strip().lower() for r in user_roles}
    is_top = is_top_admin(current_username)
    
    allowed_roles = settings.get('page_permissions', {}).get('techpanel', settings.get('page_permissions', {}).get('admin', []))
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    allowed_roles_lower = {str(r).strip().lower() for r in allowed_roles}
    
    has_permission = is_top or bool(user_roles_lower & allowed_roles_lower)
    
    # Подсчет суммы всех балансов
    total_balance = 0.0
    for u in users.values():
        b_str = str(u.get('balance', '0')).replace('$', '').replace(',', '').strip()
        try:
            total_balance += float(b_str)
        except ValueError:
            pass

    sidebar_stats = {
        "users_count": len(users),
        "total_logs": 0,
        "active_usd": format_balance(total_balance)
    }
    
    lang = session.get('lang', 'ru')
    return render_template('techpanel/techpanel.html', 
                           users=users,
                           sidebar_stats=sidebar_stats, 
                           t=lambda key: t(key, lang),
                           roles=VALID_ROLES,
                           statuses=VALID_STATUSES,
                           is_top_admin=is_top,
                           has_permission=has_permission,
                           site_settings=settings)

@techpanel_bp.route('/api/users', methods=['GET'])
def api_get_users():
    lang = session.get('lang', 'ru')
    if 'username' not in session:
        return jsonify({'error': t('err_unauthorized', lang)}), 401
    
    users = get_all_users()
    result = []
    for username, data in users.items():
        result.append({
            "username": username,
            "roles": data.get("roles", []),
            "status": data.get("status", "Beginner"),
            "balance": data.get("balance", "$0.00")
        })
        
    return jsonify({"users": result})

@techpanel_bp.route('/api/users/create', methods=['POST'])
def api_create_user():
    lang = session.get('lang', 'ru')
    if 'username' not in session:
        return jsonify({'error': t('err_unauthorized', lang)}), 401
        
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    roles = data.get('roles', [])
    status = data.get('status', 'Beginner')
    balance = data.get('balance', '$0.00')

    if not username or not password:
        return jsonify({'success': False, 'message': t('err_fill_credentials', lang)}), 400

    if not roles:
        roles = ["User"]

    success, msg = add_user(username, password, roles, status, balance)
    return jsonify({'success': success, 'message': t(msg, lang)})

@techpanel_bp.route('/api/users/update', methods=['POST'])
def api_update_user():
    lang = session.get('lang', 'ru')
    if 'username' not in session:
        return jsonify({'error': t('err_unauthorized', lang)}), 401
        
    data = request.get_json() or {}
    old_username = data.get('old_username', '').strip() or data.get('username', '').strip()
    new_username = data.get('new_username', '').strip()
    roles = data.get('roles', [])
    status = data.get('status', 'Beginner')
    new_password = data.get('password', '').strip()
    balance = data.get('balance')

    if not old_username:
        return jsonify({'success': False, 'message': t('err_user_not_specified', lang)}), 400

    if not new_username:
        return jsonify({'success': False, 'message': t('err_fill_credentials', lang)}), 400

    if not roles:
        roles = ["User"]

    success, msg = update_user(
        old_username=old_username, 
        roles=roles, 
        status=status, 
        new_password=new_password if new_password else None,
        new_username=new_username if new_username != old_username else None,
        balance=balance
    )

    if success and session.get('username') == old_username and new_username != old_username:
        session['username'] = new_username

    return jsonify({'success': success, 'message': t(msg, lang)})

@techpanel_bp.route('/api/users/delete', methods=['POST'])
def api_delete_user():
    lang = session.get('lang', 'ru')
    if 'username' not in session:
        return jsonify({'error': t('err_unauthorized', lang)}), 401
        
    data = request.get_json() or {}
    username = data.get('username', '').strip()

    if username == session.get('username'):
        return jsonify({'success': False, 'message': t('err_cannot_delete_self', lang)}), 400

    success, msg = delete_user(username)
    return jsonify({'success': success, 'message': t(msg, lang)})

@techpanel_bp.route('/api/users/delete_bulk', methods=['POST'])
def api_delete_users_bulk():
    lang = session.get('lang', 'ru')
    if 'username' not in session:
        return jsonify({'error': t('err_unauthorized', lang)}), 401

    data = request.get_json() or {}
    usernames = data.get('usernames', [])
    current_user = session.get('username')

    if not usernames or not isinstance(usernames, list):
        return jsonify({'success': False, 'message': t('err_user_not_specified', lang)}), 400

    deleted_count = 0
    errors = []

    for username in usernames:
        username = str(username).strip()
        if not username:
            continue
        if username == current_user:
            errors.append(t('err_cannot_delete_self', lang))
            continue

        success, msg = delete_user(username)
        if success:
            deleted_count += 1
        else:
            errors.append(t(msg, lang))

    if deleted_count > 0:
        return jsonify({'success': True, 'count': deleted_count, 'errors': errors})
    
    return jsonify({'success': False, 'message': errors[0] if errors else t('err_user_not_specified', lang)}), 400

@techpanel_bp.route('/api/settings', methods=['GET'])
def api_get_settings():
    if 'username' not in session or not is_top_admin(session['username']):
        return jsonify({'error': 'Forbidden'}), 403
    
    settings = load_settings()
    return jsonify({
        'settings': settings,
        'valid_roles': VALID_ROLES
    })

@techpanel_bp.route('/api/settings', methods=['POST'])
def api_update_settings():
    if 'username' not in session or not is_top_admin(session['username']):
        return jsonify({'error': 'Forbidden'}), 403
        
    data = request.get_json() or {}
    settings = load_settings()

    if 'site_closed' in data:
        settings['site_closed'] = bool(data['site_closed'])
        
    if 'page_permissions' in data and isinstance(data['page_permissions'], dict):
        settings['page_permissions'] = data['page_permissions']

    save_settings(settings)
    return jsonify({'success': True, 'settings': settings})