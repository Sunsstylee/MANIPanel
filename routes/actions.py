from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from datetime import datetime
from locales.i18n import t
from routes.auth import login_required
from database.database import db, Replacement

actions_bp = Blueprint('actions', __name__)

@actions_bp.route('/actions')
@login_required
def actions():
    lang = session.get('lang', 'ru')
    current_user = session.get('username')

    # Ищем последнюю запись, которую закреплял именно текущий пользователь
    last_replacement = Replacement.query.filter_by(spammer=current_user).order_by(Replacement.id.desc()).first()
    last_steam_id = last_replacement.steam_id if last_replacement else ''

    return render_template(
        'actions/actions.html', 
        active_page='actions',
        last_steam_id=last_steam_id,
        t=lambda key: t(key, lang)
    )

@actions_bp.route('/api/request_pin', methods=['POST'])
@login_required
def request_pin():
    lang = session.get('lang', 'ru')
    data = request.get_json() or {}
    steam_id = data.get('steam_id', '').strip()
    current_user = session.get('username')

    if not steam_id:
        return jsonify({'success': False, 'message': t('err_enter_steamid', lang)}), 400

    # Ищем существующую запись в базе данных
    existing = Replacement.query.filter(Replacement.steam_id.ilike(steam_id)).first()
    
    if existing:
        if existing.spammer and existing.spammer != current_user:
            return jsonify({'success': False, 'message': t('err_steamid_already_claimed', lang)}), 400
        elif existing.spammer == current_user:
            return jsonify({'success': True, 'message': t('msg_pin_success', lang)})

    now = datetime.now()
    if not existing:
        new_item = Replacement(
            steam_id=steam_id,
            steam_url=f"https://steamcommunity.com/profiles/{steam_id}",
            avatar_url='https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg',
            inv_tradable='0.00',
            inv_sub='0.00',
            games='csgo',
            swapped_offers=0,
            algorithm=4,
            min_dep=50,
            time=now.strftime('%H:%M:%S'),
            date=now.strftime('%d.%m.%Y'),
            spammer=current_user,
            note=''
        )
        db.session.add(new_item)
    else:
        existing.spammer = current_user

    db.session.commit()
    return jsonify({'success': True, 'message': t('msg_pin_success', lang)})