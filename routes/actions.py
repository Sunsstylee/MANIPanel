from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify
from datetime import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import re
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

    url = "https://market.csgo.com/api/v2/prices/USD.json"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('success') and 'items' in data:
                cache = {}
                for item in data['items']:
                    name = item.get('market_hash_name')
                    price_str = item.get('price')
                    if name and price_str:
                        try:
                            cache[name] = float(price_str)
                        except ValueError:
                            pass
                
                GLOBAL_PRICE_CACHE = cache
                LAST_CACHE_UPDATE = now
    except Exception as e:
        print(f"[PRICE CACHE ERROR] Ошибка загрузки базы цен (Market API): {e}")
        
    return GLOBAL_PRICE_CACHE

def resolve_steam_profile(raw_steam_id):
    default_avatar = 'https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg'
    clean_id = str(raw_steam_id).strip()
    
    if 'steamcommunity.com/profiles/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/profiles/')[1].strip('/').split('/')[0]
    elif 'steamcommunity.com/id/' in clean_id:
        clean_id = clean_id.split('steamcommunity.com/id/')[1].strip('/').split('/')[0]

    steam64 = clean_id
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

    if not (clean_id.isdigit() and len(clean_id) == 17):
        encoded_id = urllib.parse.quote(clean_id)
        try:
            url = f"https://steamcommunity.com/id/{encoded_id}/?xml=1"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                root = ET.fromstring(resp.read())
                sid64_node = root.find('steamID64')
                if sid64_node is not None and sid64_node.text:
                    steam64 = sid64_node.text.strip()
        except Exception:
            pass

        if not (steam64.isdigit() and len(steam64) == 17):
            try:
                url = f"https://steamcommunity.com/id/{encoded_id}/"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    match = re.search(r'g_steamID\s*=\s*"(\d{17})"', html)
                    if match:
                        steam64 = match.group(1)
            except Exception:
                pass

    encoded_64 = urllib.parse.quote(steam64)
    profile_urls = [
        f"https://steamcommunity.com/profiles/{encoded_64}/?xml=1",
        f"https://steamcommunity.com/id/{encoded_64}/?xml=1"
    ]
    
    steam_name = clean_id
    avatar_url = default_avatar
    
    for url in profile_urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                root = ET.fromstring(response.read())
                name_node = root.find('steamID')
                avatar_node = root.find('avatarFull')
                
                if name_node is not None and name_node.text:
                    steam_name = name_node.text.strip()
                if avatar_node is not None and avatar_node.text:
                    avatar_url = avatar_node.text.strip()
                break
        except Exception:
            continue

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
    detected_games = ['csgo']
    
    if not (steam64.isdigit() and len(steam64) == 17):
        return steam64, steam_name, avatar_url, "0.00", "0.00", "csgo"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://steamcommunity.com/profiles/{steam64}/inventory/'
    }
    
    try:
        inv_url = f"https://steamcommunity.com/inventory/{steam64}/730/2?l=english&count=2000"
        req = urllib.request.Request(inv_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
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
    except Exception:
        pass

    games_str = ','.join(detected_games)
    result = (steam64, steam_name, avatar_url, f"{tradable_total:.2f}", f"{non_tradable_total:.2f}", games_str)
    INVENTORY_MEMORY_CACHE[steam64] = (result, now)
    return result

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

    steam64, steam_name, avatar_url, inv_tradable, inv_sub, games = fetch_steam_info_and_inventory(raw_steam_id, force=True)

    existing = Replacement.query.filter_by(steam_id=steam64).first()
    
    if existing:
        if existing.spammer and existing.spammer != current_user:
            return jsonify({'success': False, 'message': t('err_steamid_already_claimed', lang)}), 400
        elif existing.spammer == current_user:
            existing.steam_name = steam_name
            existing.avatar_url = avatar_url
            existing.games = games
            
            if not (inv_tradable == "0.00" and inv_sub == "0.00" and (float(existing.inv_tradable) > 0 or float(existing.inv_sub) > 0)):
                existing.inv_tradable = inv_tradable
                existing.inv_sub = inv_sub

            db.session.commit()
            return jsonify({'success': True, 'message': t('msg_pin_success', lang)})

    now = datetime.now()
    new_item = Replacement(
        steam_id=steam64,
        steam_name=steam_name,
        steam_url=f"https://steamcommunity.com/profiles/{steam64}",
        avatar_url=avatar_url,
        inv_tradable=inv_tradable,
        inv_sub=inv_sub,
        games=games,
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
    return jsonify({'success': True, 'message': t('msg_pin_success', lang)})