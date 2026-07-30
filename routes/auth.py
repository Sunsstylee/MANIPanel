from flask import Blueprint, render_template, request, redirect, url_for, session
from database.database import verify_user, get_user_role, get_users_count
from locales.i18n import t
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Автоматическая передача статистики в сайдбар для всех страниц
@auth_bp.context_processor
def inject_sidebar_stats():
    return dict(
        sidebar_stats={
            'users_count': get_users_count(), # Динамическое кол-во аккаунтов из файла/БД
            'total_logs': 0,                  # Пока нет логики логов — ставим 0
            'active_usd': '0.00'              # Пока нет логов — ставим 0.00
        }
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
        
    error_key = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if verify_user(username, password):
            session['username'] = username
            return redirect(url_for('auth.dashboard'))
        else:
            error_key = "error_invalid"
            
    return render_template('auth/login.html', error_key=error_key)

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username')
    role = get_user_role(username)
    return render_template('auth/dashboard.html', username=username, role=role)

@auth_bp.route('/logs')
@login_required
def logs():
    lang = session.get('lang', 'ru')
    return render_template('coming_soon.html', page_name=t('nav_logs', lang))

@auth_bp.route('/actions')
@login_required
def actions():
    lang = session.get('lang', 'ru')
    return render_template('coming_soon.html', page_name=t('nav_actions', lang))

@auth_bp.route('/replacements')
@login_required
def replacements():
    lang = session.get('lang', 'ru')
    return render_template('coming_soon.html', page_name=t('nav_replacements', lang))

@auth_bp.route('/admin')
@login_required
def admin_panel():
    lang = session.get('lang', 'ru')
    return render_template('coming_soon.html', page_name=t('nav_admin', lang))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))