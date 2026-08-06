from flask import Blueprint, render_template, session
from locales.i18n import t
from routes.auth import login_required
from database.database import Replacement

replacements_bp = Blueprint('replacements', __name__)

@replacements_bp.route('/replacements')
@login_required
def replacements():
    lang = session.get('lang', 'ru')
    current_username = session.get('username', '')

    # Получаем подмены текущего пользователя из базы данных
    db_items = Replacement.query.filter_by(spammer=current_username).all()
    user_items = [item.to_dict() for item in db_items]
    
    return render_template('replacements/replacements.html', items=user_items, t=lambda key: t(key, lang))