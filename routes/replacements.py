from flask import Blueprint, render_template, session
from locales.i18n import t
from routes.auth import login_required

replacements_bp = Blueprint('replacements', __name__)

@replacements_bp.route('/replacements')
@login_required
def replacements():
    lang = session.get('lang', 'ru')
    # Достаем ник текущего пользователя из сессии
    current_username = session.get('username', '')

    all_items = [
        {
            'id': 1,
            'steam_id': 'SBY139',
            'steam_url': 'https://steamcommunity.com/profiles/76561198000000001',
            'avatar_url': 'https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg',
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
            'steam_url': 'https://steamcommunity.com/profiles/76561198000000002',
            'avatar_url': 'https://avatars.steamstatic.com/b5bd569220fa447289659b967d26425032a4e9ef_full.jpg',
            'inv_tradable': '236.91',
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
            'steam_url': 'https://steamcommunity.com/profiles/76561198000000003',
            'avatar_url': 'https://avatars.steamstatic.com/a9c1ef34d28471131ef78f24419b45123d508499_full.jpg',
            'inv_tradable': '1.63',
            'inv_sub': '0.69',
            'games': ['csgo'],
            'swapped_offers': 1,
            'algorithm': 4,
            'min_dep': 50,
            'time': '0:54:58',
            'date': '24.7.2026',
            'spammer': 'OtherUser',
            'note': ''
        }
    ]
    
    # Отфильтровываем подмены строго для текущего воркера
    user_items = [item for item in all_items if item['spammer'] == current_username]
    
    return render_template('replacements/replacements.html', items=user_items, t=lambda key: t(key, lang))