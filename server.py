from flask import Flask, redirect, url_for, session, request, render_template
from routes.auth import auth_bp
from routes.techpanel import techpanel_bp, VALID_ROLES
from locales.i18n import t
from database.database import load_settings, is_top_admin, get_user_roles

app = Flask(__name__)
app.secret_key = "mani_super_secret_key"

# Карта соответствия Flask-эндпоинтов и разделов в settings.json
ROUTE_PAGE_MAP = {
    'auth.dashboard': 'dashboard',
    'techpanel.techpanel': 'techpanel',
    'auth.logs': 'logs',
    'auth.actions': 'actions',
    'auth.replacements': 'replacements',
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
    
    # Если юзер авторизован и НЕ является верхушкой (Owner / Co-Owner / Developer)
    if username and not top_admin:
        page_key = ROUTE_PAGE_MAP.get(request.endpoint)
        
        if page_key and page_key in perms:
            user_roles = get_user_roles(username)
            if isinstance(user_roles, str):
                user_roles = [user_roles]
                
            allowed_roles = perms[page_key]
            if isinstance(allowed_roles, str):
                allowed_roles = [allowed_roles]

            # Сравнение множеств без учета регистра
            user_roles_set = {str(r).strip().lower() for r in user_roles}
            allowed_roles_set = {str(r).strip().lower() for r in allowed_roles}
            
            # Запрещаем доступ ТОЛЬКО если нет ни одной общей роли
            if not (user_roles_set & allowed_roles_set):
                access_denied = True

    return dict(
        t=lambda key: t(key, lang),
        is_top_admin=top_admin,
        access_denied=access_denied,
        site_settings=settings,
        all_roles=VALID_ROLES
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

app.register_blueprint(auth_bp)
app.register_blueprint(techpanel_bp)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)