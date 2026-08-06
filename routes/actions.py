from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, current_app
from datetime import datetime
import urllib.request
import urllib.parse
import json
import time
import re
import threading
import cloudscraper
from locales.i18n import t
from routes.auth import login_required
from database.database import db, Replacement

actions_bp = Blueprint('actions', __name__)

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
    
    url_tradeit = "https://tradeit.gg/api/v2/inventory/data"
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url_tradeit, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items_list = data if isinstance(data, list) else data.get('items', [])
            for item in items_list:
                name = item.get('name') or item.get('market_hash_name')
                price_str = item.get('price') or item.get('buffPrice') or item.get('value')
                if name and price_str is not None:
                    try:
                        cache[name] = float(price_str)
                    except ValueError:
                        pass
            if cache:
                print(f"[PRICE CACHE] Цены с Tradeit успешно загружены ({len(cache)} предметов)")
        else:
            print(f"[PRICE CACHE WARNING] Tradeit вернул статус {response.status_code}, переключение на резерв...")
    except Exception as e:
        print(f"[PRICE CACHE WARNING] Tradeit API недоступен ({e}), переключение на резервный источник...")

    if not cache:
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
                    print(f"[PRICE CACHE] База цен успешно загружена из резерва ({len(cache)} предметов)")
        except Exception as e2:
            print(f"[PRICE CACHE ERROR] Ошибка резервного источника цен: {e2}")

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
    detected_games = []
    
    if not (steam64.isdigit() and len(steam64) == 17):
        return steam64, steam_name, avatar_url, "0.00", "0.00", "csgo"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://steamcommunity.com/profiles/{steam64}/inventory/'
    }
    
    apps = [
        {'id': 730, 'code': 'csgo'},
        {'id': 570, 'code': 'dota2'},
        {'id': 252490, 'code': 'rust'}
    ]

    for app in apps:
        try:
            inv_url = f"https://steamcommunity.com/inventory/{steam64}/{app['id']}/2?l=english&count=2000"
            req = urllib.request.Request(inv_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                assets = data.get('assets', [])
                descriptions = data.get('descriptions', [])

                if assets and app['code'] not in detected_games:
                    detected_games.append(app['code'])

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
        except Exception:
            pass
        time.sleep(0.3)

    games_str = ','.join(detected_games) if detected_games else 'csgo'
    result = (steam64, steam_name, avatar_url, f"{tradable_total:.2f}", f"{non_tradable_total:.2f}", games_str)
    INVENTORY_MEMORY_CACHE[steam64] = (result, now)
    return result

def background_update_inventory_action(app, steam64):
    with app.app_context():
        try:
            _, s_name, a_url, inv_tr, inv_sb, games = fetch_steam_info_and_inventory(steam64, force=True)
            item = Replacement.query.filter_by(steam_id=steam64).first()
            if item:
                item.steam_name = s_name
                item.avatar_url = a_url
                item.games = games
                item.inv_tradable = inv_tr
                item.inv_sub = inv_sb
                db.session.commit()
        except Exception as e:
            print(f"[BACKGROUND ERROR] Не удалось обновить инвентарь для {steam64}: {e}")

@actions_bp.route('/actions')
@login_required
def actions():
    lang = session.get('lang', 'ru')
    current_user = session.get('username')

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
    raw_steam_id = data.get('steam_id', '').strip()
    current_user = session.get('username')

    if not raw_steam_id:
        return jsonify({'success': False, 'message': t('err_enter_steamid', lang)}), 400

    clean_id = str(raw_steam_id).strip()
    if 'steamcommunity.com/profiles/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/profiles/')[1].strip('/').split('/')[0]
    elif 'steamcommunity.com/id/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/id/')[1].strip('/').split('/')[0]

    if clean_id.isdigit() and len(clean_id) == 17:
        existing_check = Replacement.query.filter_by(steam_id=clean_id).first()
        if existing_check and existing_check.spammer and existing_check.spammer != current_user:
            return jsonify({'success': False, 'message': t('err_steamid_already_claimed', lang)}), 400

    steam64, steam_name, avatar_url = resolve_steam_profile(raw_steam_id)

    if not (steam64.isdigit() and len(steam64) == 17):
        return jsonify({'success': False, 'message': t('err_enter_steamid', lang)}), 400

    existing = Replacement.query.filter_by(steam_id=steam64).first()
    
    if existing:
        if existing.spammer and existing.spammer != current_user:
            return jsonify({'success': False, 'message': t('err_steamid_already_claimed', lang)}), 400
        elif existing.spammer == current_user:
            existing.steam_name = steam_name
            existing.avatar_url = avatar_url
            db.session.commit()
            
            app = current_app._get_current_object()
            threading.Thread(target=background_update_inventory_action, args=(app, steam64)).start()

            return jsonify({'success': True, 'message': t('msg_pin_success', lang)})

    now = datetime.now()
    new_item = Replacement(
        steam_id=steam64,
        steam_name=steam_name,
        steam_url=f"https://steamcommunity.com/profiles/{steam64}",
        avatar_url=avatar_url,
        inv_tradable="0.00",
        inv_sub="0.00",
        games="csgo",
        swapped_offers=0,
        algorithm=4,
        min_dep=50,
        time=now.strftime('%H:%M:%S'),
        date=now.strftime('%d.%m.%Y'),
        spammer=current_user,
        note=''
    )
    db.session.add(new_item)
    db.session.commit()

    app = current_app._get_current_object()
    threading.Thread(target=background_update_inventory_action, args=(app, steam64)).start()

    return jsonify({'success': True, 'message': t('msg_pin_success', lang)})