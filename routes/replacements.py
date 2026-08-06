from flask import Blueprint, render_template, session
from locales.i18n import t
from routes.auth import login_required

replacements_bp = Blueprint('replacements', __name__)

@replacements_bp.route('/replacements')
@login_required
def replacements():
    lang = session.get('lang', 'ru')
    
    # Данные для таблицы подмен
    items = [
        {
            'id': 1,
            'steam_id': 'SBY139',
            'inv_tradable': '23.51',
            'inv_sub': '8.52',
            'games': ['dota2', 'csgo', 'rust'],
            'swapped_offers': 0,
            'algorithm': 4,
            'min_dep': 50,
            'time': '12:41:30',
            'date': '6.8.2026',
            'spammer': 'Sunsstylee',
            'note': ''
        },
        {
            'id': 2,
            'steam_id': 'cRaZyBaNaNツ',
            'inv_tradable': '234.91',
            'inv_sub': '0.85',
            'games': ['dota2', 'csgo'],
            'swapped_offers': 0,
            'algorithm': 4,
            'min_dep': 50,
            'time': '0:9:44',
            'date': '3.8.2026',
            'spammer': 'Sunsstylee',
            'note': ''
        },
        {
            'id': 3,
            'steam_id': 'vurdalaaakkk2000',
            'inv_tradable': '1.63',
            'inv_sub': '0.69',
            'games': ['csgo'],
            'swapped_offers': 1,
            'algorithm': 4,
            'min_dep': 50,
            'time': '0:54:58',
            'date': '24.7.2026',
            'spammer': 'Sunsstylee',
            'note': ''
        }
    ]
    
    return render_template('replacements/replacements.html', items=items, t=lambda key: t(key, lang))