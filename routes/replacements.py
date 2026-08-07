from flask import Blueprint, render_template, session, jsonify, request, current_app
import urllib.request
import urllib.parse
import json
import time
import re
import threading
from datetime import datetime
from locales.i18n import t
from routes.auth import login_required
from database.database import db, Replacement

replacements_bp = Blueprint('replacements', __name__)

GLOBAL_PRICE_CACHE = {}
LAST_CACHE_UPDATE = 0
CACHE_TTL = 3600

INVENTORY_MEMORY_CACHE = {}
INVENTORY_COOLDOWN = 300

def load_global_price_cache():
    global GLOBAL_PRICE_CACHE, LAST_CACHE_UPDATE
    now = time.time()
    if now - LAST_CACHE_UPDATE < CACHE_TTL and GLOBAL_PRICE_CACHE:
        return GLOBAL_PRICE_CACHE

    cache = {}
    url_market = "https://market.csgo.com/api/v2/prices/USD.json"
    try:
        req = urllib.request.Request(url_market, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('success') and 'items' in data:
                for item in data['items']:
                    name = item.get('market_hash_name')
                    price_str = item.get('price')
                    if name and price_str:
                        try:
                            cache[name] = float(price_str)
                        except ValueError:
                            pass
                print(f"[PRICE CACHE] База цен успешно загружена ({len(cache)} предметов)")
    except Exception as e:
        print(f"[PRICE CACHE ERROR] Ошибка загрузки базы цен: {e}")

    if cache:
        GLOBAL_PRICE_CACHE = cache
        LAST_CACHE_UPDATE = now
        
    return GLOBAL_PRICE_CACHE

def resolve_steam_profile(raw_steam_id):
    default_avatar = 'https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg'
    clean_id = str(raw_steam_id).strip()
    
    if 'steamcommunity.com/profiles/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/profiles/')[1].strip('/').split('/')[0]
    elif 'steamcommunity.com/id/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/id/')[1].strip('/').split('/')[0]

    steam64 = clean_id
    steam_name = clean_id
    avatar_url = default_avatar
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    if clean_id.isdigit() and len(clean_id) == 17:
        profile_url = f"https://steamcommunity.com/profiles/{clean_id}/"
    else:
        profile_url = f"https://steamcommunity.com/id/{urllib.parse.quote(clean_id)}/"

    try:
        req = urllib.request.Request(profile_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            match_id = re.search(r'g_steamID\s*=\s*"(\d{17})"', html)
            if match_id:
                steam64 = match_id.group(1)
            
            match_name = re.search(r'"personaname"\s*:\s*"([^"]+)"', html)
            if match_name:
                raw_name = match_name.group(1)
                try:
                    steam_name = json.loads(f'"{raw_name}"')
                except Exception:
                    try:
                        steam_name = raw_name.encode().decode('unicode-escape')
                    except Exception:
                        steam_name = raw_name
            else:
                match_title = re.search(r'<title>[^<]*[:\s]([^<]+)</title>', html)
                if match_title:
                    steam_name = match_title.group(1).strip()

            match_avatar = re.search(r'"avatarfull"\s*:\s*"([^"]+)"', html)
            if match_avatar:
                avatar_url = match_avatar.group(1).replace('\\/', '/')
            else:
                match_img = re.search(r'<link rel="image_src" href="([^"]+)"', html)
                if match_img:
                    avatar_url = match_img.group(1)
    except Exception as e:
        print(f"[PROFILE RESOLVE ERROR] Не удалось получить профиль {raw_steam_id}: {e}")

    return steam64, steam_name, avatar_url

def fetch_steam_info_and_inventory(steam_id, force=False):
    global INVENTORY_MEMORY_CACHE
    
    steam64, steam_name, avatar_url = resolve_steam_profile(steam_id)
    
    now = time.time()
    if not force and steam64 in INVENTORY_MEMORY_CACHE:
        cached_data, timestamp = INVENTORY_MEMORY_CACHE[steam64]
        if now - timestamp < INVENTORY_COOLDOWN:
            return cached_data

    price_cache = load_global_price_cache()
    tradable_total = 0.0
    non_tradable_total = 0.0
    
    if not (steam64.isdigit() and len(steam64) == 17):
        print(f"[INVENTORY ERROR] Некорректный SteamID: {steam64}")
        return steam64, steam_name, avatar_url, "0.00", "0.00"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://steamcommunity.com/profiles/{steam64}/inventory/'
    }
    
    success_fetch = False
    for app_id in [730, 570, 252490]:
        for attempt in range(2):
            try:
                inv_url = f"https://steamcommunity.com/inventory/{steam64}/{app_id}/2?l=english&count=2000"
                req = urllib.request.Request(inv_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    assets = data.get('assets', [])
                    descriptions = data.get('descriptions', [])

                    desc_map = {f"{d.get('classid')}_{d.get('instanceid', '0')}": d for d in descriptions}

                    for asset in assets:
                        key = f"{asset.get('classid')}_{asset.get('instanceid', '0')}"
                        desc = desc_map.get(key, {})
                        
                        is_tradable = desc.get('tradable') == 1
                        is_marketable = desc.get('marketable') == 1
                        market_hash_name = desc.get('market_hash_name', '')

                        item_price = price_cache.get(market_hash_name, 0.0)

                        if is_tradable and is_marketable:
                            tradable_total += item_price
                        else:
                            non_tradable_total += item_price
                    success_fetch = True
                    break
                            
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"[INVENTORY WARNING] SteamID {steam64} (AppID {app_id}): Лимит (429), повтор...")
                    time.sleep(1.5)
                else:
                    break
            except Exception:
                break
        
        time.sleep(0.5)

    if not success_fetch and steam64 in INVENTORY_MEMORY_CACHE:
        return INVENTORY_MEMORY_CACHE[steam64][0]

    result = (steam64, steam_name, avatar_url, f"{tradable_total:.2f}", f"{non_tradable_total:.2f}")
    INVENTORY_MEMORY_CACHE[steam64] = (result, now)
    return result

def background_update_inventory_replacement(app, steam64):
    with app.app_context():
        try:
            _, s_name, a_url, inv_tr, inv_sb = fetch_steam_info_and_inventory(steam64, force=True)
            item = Replacement.query.filter_by(steam_id=steam64).first()
            if item:
                item.steam_name = s_name
                item.avatar_url = a_url
                item.inv_tradable = inv_tr
                item.inv_sub = inv_sb
                db.session.commit()
        except Exception as e:
            print(f"[BACKGROUND ERROR] Не удалось обновить инвентарь для {steam64}: {e}")

@replacements_bp.route('/replacements')
@login_required
def replacements():
    lang = session.get('lang', 'ru')
    current_username = session.get('username', '')

    db_items = Replacement.query.filter_by(spammer=current_username).all()
    user_items = [item.to_dict() for item in db_items]
    
    return render_template(
        'replacements/replacements.html', 
        active_page='replacements',
        items=user_items, 
        t=lambda key: t(key, lang)
    )

@replacements_bp.route('/api/replacements/add', methods=['POST'])
@login_required
def add_replacement():
    current_username = session.get('username', '')
    data = request.json
    
    raw_steam_id = data.get('steam_id', '').strip()
    if not raw_steam_id:
        return jsonify({'success': False, 'error': 'SteamID is required'}), 400

    clean_id = str(raw_steam_id).strip()
    if 'steamcommunity.com/profiles/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/profiles/')[1].strip('/').split('/')[0]
    elif 'steamcommunity.com/id/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/id/')[1].strip('/').split('/')[0]

    # Быстрая проверка
    if clean_id.isdigit() and len(clean_id) == 17:
        any_existing = Replacement.query.filter_by(steam_id=clean_id).first()
        if any_existing:
            if any_existing.spammer and any_existing.spammer != current_username:
                return jsonify({'success': False, 'error': 'This SteamID is already claimed by another user'}), 400
            elif any_existing.spammer == current_username:
                return jsonify({'success': False, 'error': 'Этот SteamID уже закреплен за вами!'}), 400

    # Разрешаем профиль для получения 100% steam64
    steam64, steam_name, avatar_url = resolve_steam_profile(raw_steam_id)

    if not (steam64.isdigit() and len(steam64) == 17):
        return jsonify({'success': False, 'error': 'Invalid SteamID'}), 400

    # Точная проверка по разрешенному steam64
    existing_item = Replacement.query.filter_by(steam_id=steam64).first()
    if existing_item:
        if existing_item.spammer and existing_item.spammer != current_username:
            return jsonify({'success': False, 'error': 'This SteamID is already claimed by another user'}), 400
        elif existing_item.spammer == current_username:
            return jsonify({'success': False, 'error': 'Этот SteamID уже закреплен за вами!'}), 400

    # Моментально закрепляем в БД с нулевым инвентарем
    new_item = Replacement(
        steam_id=steam64,
        steam_name=steam_name,
        steam_url=f"https://steamcommunity.com/profiles/{steam64}",
        avatar_url=avatar_url,
        inv_tradable="0.00",
        inv_sub="0.00",
        games=data.get('games', 'csgo'),
        algorithm=data.get('algorithm', 4),
        min_dep=data.get('min_dep', 50),
        time=datetime.now().strftime("%H:%M:%S"),
        date=datetime.now().strftime("%d.%m.%Y"),
        spammer=current_username,
        note=data.get('note', '')
    )

    db.session.add(new_item)
    db.session.commit()

    # Запускаем парсинг инвентаря в фоне
    app = current_app._get_current_object()
    threading.Thread(target=background_update_inventory_replacement, args=(app, steam64)).start()

    return jsonify({'success': True, 'item': new_item.to_dict()})

@replacements_bp.route('/api/replacements/refresh/<int:item_id>', methods=['POST'])
@login_required
def refresh_item(item_id):
    current_username = session.get('username', '')
    item = Replacement.query.filter_by(id=item_id, spammer=current_username).first()
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

    steam64, s_name, a_url, inv_tr, inv_sb = fetch_steam_info_and_inventory(item.steam_id, force=True)
    
    if inv_tr == "0.00" and inv_sb == "0.00" and (float(item.inv_tradable) > 0 or float(item.inv_sub) > 0):
        pass
    else:
        item.inv_tradable = inv_tr
        item.inv_sub = inv_sb

    item.steam_name = s_name
    item.avatar_url = a_url
    db.session.commit()

    return jsonify({
        'success': True,
        'item': item.to_dict()
    })