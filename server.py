import socket
import os
import sys
import traceback
from datetime import datetime
from flask import Flask, redirect, url_for, session, request, render_template
from werkzeug.exceptions import HTTPException
from routes.auth import auth_bp
from routes.techpanel import techpanel_bp, VALID_ROLES
from routes.logs import logs_bp
from routes.actions import actions_bp
from routes.replacements import replacements_bp
from locales.i18n import t
from database.database import load_settings, is_top_admin, get_user_roles, get_sidebar_stats, db, init_db

app = Flask(__name__)
app.secret_key = "mani_super_secret_key"

# Настройка SQLite базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manipanel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализируем БД
init_db(app)

# Карта соответствия Flask-эндпоинтов и разделов в settings.json
ROUTE_PAGE_MAP = {
    'auth.dashboard': 'dashboard',
    'techpanel.techpanel': 'techpanel',
    'logs.logs': 'logs',
    'actions.actions': 'actions',
    'replacements.replacements': 'replacements',
    'auth.clients': 'clients'
}

@app.context_processor
def inject_globals():
    lang = session.get('lang', 'ru')
    username = session.get('username')
    top_admin = is_top_admin(username) if username else False
    
    settings = load_settings()
    perms = settings.get('page_permissions', {})
    
    access_denied = False
    
    if username and not top_admin:
        page_key = ROUTE_PAGE_MAP.get(request.endpoint)
        
        if page_key and page_key in perms:
            user_roles = get_user_roles(username)
            if isinstance(user_roles, str):
                user_roles = [user_roles]
                
            allowed_roles = perms[page_key]
            if isinstance(allowed_roles, str):
                allowed_roles = [allowed_roles]

            user_roles_set = {str(r).strip().lower() for r in user_roles}
            allowed_roles_set = {str(r).strip().lower() for r in allowed_roles}
            
            if not (user_roles_set & allowed_roles_set):
                access_denied = True

    return dict(
        t=lambda key: t(key, lang),
        is_top_admin=top_admin,
        access_denied=access_denied,
        site_settings=settings,
        all_roles=VALID_ROLES,
        sidebar_stats=get_sidebar_stats()
    )

@app.before_request
def check_site_status():
    if request.path.startswith('/static') or request.path.startswith('/set_lang'):
        return None

    settings = load_settings()
    
    if settings.get('site_closed', False):
        current_user = session.get('username')
        
        if current_user and is_top_admin(current_user):
            return None
        
        if request.endpoint in ['auth.login', 'auth.logout']:
            if request.endpoint == 'auth.login' and current_user and not is_top_admin(current_user):
                session.clear()
            return None
        
        lang = session.get('lang', 'ru')
        return render_template('site_closed.html', t=lambda key: t(key, lang)), 503

@app.route('/set_lang/<lang>')
def set_language(lang):
    if lang in ['ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return '', 204

app.register_blueprint(auth_bp)
app.register_blueprint(techpanel_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(actions_bp)
app.register_blueprint(replacements_bp)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

@app.after_request
def log_request(response):
    if not request.path.startswith('/static') and request.path != '/favicon.ico':
        now = datetime.now().strftime("%H:%M:%S")
        ip = request.remote_addr
        username = session.get('username', 'Гость')
        status = response.status_code
        print(f"[{now}] [USER: {username}] ({ip}) -> {request.method} {request.path} [{status}]")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    username = session.get('username', 'Гость')
    
    print("\n" + "=" * 60)
    print(f"  [КРИТИЧЕСКАЯ ОШИБКА СЕРВЕРА] {now}")
    print(f"  Пользователь: {username} ({request.remote_addr})")
    print(f"  Запрос:       {request.method} {request.path}")
    print("=" * 60)
    traceback.print_exc()
    print("=" * 60 + "\n")
    
    if app.debug:
        raise e
    
    return f"<h1>500 — Внутренняя ошибка сервера</h1><p>{e}</p>", 500

def show_server_info(host='0.0.0.0', port=5000, debug=True):
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        return

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = "127.0.0.1"

    hostname = socket.gethostname()
    py_version = sys.version.split()[0]
    launch_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    print("\n" + "=" * 60)
    print("   [INFO] ВЕБ-СЕРВЕР MANIPanel УСПЕШНО ЗАПУЩЕН")
    print("=" * 60)
    print(f"  * Локальный адрес:     http://localhost:{port}")
    print(f"  * Сетевой адрес (LAN): http://{lan_ip}:{port}")
    print("-" * 60)
    print(f"  * Имя компьютера:      {hostname}")
    print(f"  * Версия Python:       {py_version}")
    print(f"  * Режим отладки:       {'ВКЛЮЧЕН (Debug)' if debug else 'ВЫКЛЮЧЕН'}")
    print(f"  * PID процесса:         {os.getpid()}")
    print(f"  * Время запуска:       {launch_time}")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    show_server_info(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)