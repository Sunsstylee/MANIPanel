from flask import Blueprint, render_template, request, redirect, url_for, session
from database.database import (
    verify_user, get_user_role, get_user_status, 
    get_user_finance_data, get_user_recent_actions,
    get_top_users, get_top_speakers
)
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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    lang_param = request.args.get('lang')
    if lang_param in ['ru', 'en']:
        session['lang'] = lang_param

    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
        
    error_key = None
    username = ""
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            error_key = "error_empty"
        elif verify_user(username, password):
            session['username'] = username
            return redirect(url_for('auth.dashboard'))
        else:
            error_key = "error_invalid"
            
    lang = session.get('lang', 'ru')
    return render_template('auth/login.html', error_key=error_key, username=username, t=lambda key: t(key, lang))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    lang = session.get('lang', 'ru')
    username = session.get('username')
    role = get_user_role(username)
    status = get_user_status(username)
    finance_data = get_user_finance_data(username) or {}
    recent_actions = get_user_recent_actions(username) or []
    top_users = get_top_users(10)
    top_speakers = get_top_speakers(10)
    
    return render_template(
        'auth/dashboard.html', 
        username=username, 
        role=role, 
        status=status, 
        finance_labels=finance_data.get('labels', []),
        finance_values=finance_data.get('values', []),
        recent_actions=recent_actions,
        top_users=top_users,
        top_speakers=top_speakers,
        t=lambda key: t(key, lang)
    )

@auth_bp.route('/clients')
@login_required
def clients():
    lang = session.get('lang', 'ru')
    return render_template('coming_soon.html', page_name=t('nav_clients', lang), t=lambda key: t(key, lang))

@auth_bp.route('/techpanel')
@login_required
def techpanel():
    return redirect(url_for('techpanel.techpanel'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))