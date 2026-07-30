from flask import Flask, redirect, url_for, session, request
from routes.auth import auth_bp
from locales.i18n import t

app = Flask(__name__)
app.secret_key = "mani_super_secret_key"

@app.context_processor
def inject_i18n():
    def translate(key):
        lang = session.get('lang', 'ru')
        return t(key, lang)
    return dict(t=translate)

@app.route('/set_lang/<lang>')
def set_language(lang):
    if lang in ['ru', 'en']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

app.register_blueprint(auth_bp)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)