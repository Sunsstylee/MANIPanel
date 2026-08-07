import json
import re
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session
from database.database import Replacement, db
from locales.i18n import t
from routes.auth import login_required

replacements_bp = Blueprint('replacements', __name__)

GLOBAL_PRICE_CACHE = {}
LAST_CACHE_UPDATE = 0
CACHE_TTL = 3600

INVENTORY_MEMORY_CACHE = {}
INVENTORY_COOLDOWN = 300

GAMES_METADATA = {
    '730': {
        'name': 'Counter-Strike 2',
        'icon': 'https://cdn.cloudflare.steamstatic.com/steam/apps/730/capsule_231x87.jpg',
    },
    '570': {
        'name': 'Dota 2',
        'icon': 'https://cdn.cloudflare.steamstatic.com/steam/apps/570/capsule_231x87.jpg',
    },
    '252490': {
        'name': 'Rust',
        'icon': 'https://cdn.cloudflare.steamstatic.com/steam/apps/252490/capsule_231x87.jpg',
    },
}


def create_default_breakdown():
    return {
        'tradable': {730: 0.0, 570: 0.0, 252490: 0.0},
        'non_tradable': {730: 0.0, 570: 0.0, 252490: 0.0},
        'updated_at': datetime.now().strftime('%H:%M:%S %d.%m.%Y'),
    }


def clean_steam_identifier(raw_input):
    clean_id = str(raw_input).strip()
    if 'steamcommunity.com/profiles/' in clean_id:
        clean_id = (
            clean_id.split('steamcommunity.com/profiles/')[1]
            .strip('/')
            .split('/')[0]
        )
    elif 'steamcommunity.com/id/' in clean_id:
        clean_id = (
            clean_id.split('steamcommunity.com/id/')[1].strip('/').split('/')[0]
        )
    return clean_id


def load_global_price_cache():
    global GLOBAL_PRICE_CACHE, LAST_CACHE_UPDATE
    now = time.time()
    if now - LAST_CACHE_UPDATE < CACHE_TTL and GLOBAL_PRICE_CACHE:
        return GLOBAL_PRICE_CACHE

    cache = {}
    urls = [
        'https://market.csgo.com/api/v2/prices/USD.json',
        'https://market.dota2.net/api/v2/prices/USD.json',
        'https://rust.tm/api/v2/prices/USD.json'
    ]
    
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        ' (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
                    ),
                    'Accept': 'application/json',
                },
            )
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
        except Exception as e:
            print(f'[PRICE CACHE ERROR] {url}: {e}')

    if cache:
        GLOBAL_PRICE_CACHE = cache
        LAST_CACHE_UPDATE = now

    return GLOBAL_PRICE_CACHE


def resolve_steam_profile(raw_steam_id):
    default_avatar = 'https://avatars.steamstatic.com/c578f307300c3a8122d20d7f25d3010b965f7c3c_full.jpg'
    clean_id = clean_steam_identifier(raw_steam_id)

    steam64 = clean_id
    steam_name = clean_id
    avatar_url = default_avatar

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
    }

    if clean_id.isdigit() and len(clean_id) == 17:
        profile_url = f'https://steamcommunity.com/profiles/{clean_id}/'
    else:
        profile_url = (
            f'https://steamcommunity.com/id/{urllib.parse.quote(clean_id)}/'
        )

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
        print(f'[PROFILE RESOLVE ERROR] {raw_steam_id}: {e}')

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
    breakdown = create_default_breakdown()
    detected_games = []

    if not (steam64.isdigit() and len(steam64) == 17):
        return steam64, steam_name, avatar_url, '0.00', '0.00', 'csgo', breakdown

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ' (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://steamcommunity.com/profiles/{steam64}/inventory/',
    }

    apps = [
        {'id': 730, 'code': 'csgo'},
        {'id': 570, 'code': 'dota2'},
        {'id': 252490, 'code': 'rust'},
    ]

    for app in apps:
        app_id = app['id']
        app_code = app['code']
        for _ in range(2):
            try:
                inv_url = f'https://steamcommunity.com/inventory/{steam64}/{app_id}/2?l=english&count=2000'
                req = urllib.request.Request(inv_url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    assets = data.get('assets', [])
                    descriptions = data.get('descriptions', [])

                    if assets and app_code not in detected_games:
                        detected_games.append(app_code)

                    desc_map = {
                        f"{d.get('classid')}_{d.get('instanceid', '0')}": d
                        for d in descriptions
                    }

                    for asset in assets:
                        key = f"{asset.get('classid')}_{asset.get('instanceid', '0')}"
                        desc = desc_map.get(key, {})

                        is_tradable = desc.get('tradable') == 1
                        is_marketable = desc.get('marketable') == 1
                        market_hash_name = desc.get('market_hash_name', '')
                        item_price = price_cache.get(market_hash_name, 0.0)

                        if is_tradable and is_marketable:
                            tradable_total += item_price
                            breakdown['tradable'][app_id] = (
                                breakdown['tradable'].get(app_id, 0.0) + item_price
                            )
                        else:
                            non_tradable_total += item_price
                            breakdown['non_tradable'][app_id] = (
                                breakdown['non_tradable'].get(app_id, 0.0) + item_price
                            )

                    break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    time.sleep(1.5)
                else:
                    break
            except Exception:
                break

        time.sleep(0.3)

    games_str = ','.join(detected_games) if detected_games else 'csgo'
    result = (
        steam64,
        steam_name,
        avatar_url,
        f'{tradable_total:.2f}',
        f'{non_tradable_total:.2f}',
        games_str,
        breakdown,
    )
    INVENTORY_MEMORY_CACHE[steam64] = (result, now)
    return result


def background_update_item(app_ctx, item_id, steam64):
    with app_ctx:
        try:
            res = fetch_steam_info_and_inventory(steam64, force=True)
            _, final_steam_name, final_avatar_url, inv_tr, inv_sb, games_str, breakdown = res

            item = Replacement.query.get(item_id)
            if item:
                item.steam_name = final_steam_name
                item.avatar_url = final_avatar_url
                item.inv_tradable = inv_tr
                item.inv_sub = inv_sb
                item.breakdown_json = json.dumps(breakdown)
                item.games = games_str
                db.session.commit()
        except Exception as e:
            print(f'[BACKGROUND UPDATE ERROR] Item ID {item_id}: {e}')


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
        t=lambda key: t(key, lang),
    )


@replacements_bp.route('/api/replacements/add', methods=['POST'])
@login_required
def add_replacement():
    current_username = session.get('username', '')
    data = request.json or {}

    raw_steam_id = data.get('steam_id', '').strip()
    if not raw_steam_id:
        return jsonify({'success': False, 'error': 'SteamID is required'}), 400

    clean_id = clean_steam_identifier(raw_steam_id)

    if clean_id.isdigit() and len(clean_id) == 17:
        existing = Replacement.query.filter_by(steam_id=clean_id).first()
        if existing:
            if existing.spammer == current_username:
                return (
                    jsonify({
                        'success': False,
                        'error': 'Этот SteamID уже закреплен за вами!',
                    }),
                    400,
                )
            return (
                jsonify({
                    'success': False,
                    'error': 'This SteamID is already claimed by another user',
                }),
                400,
            )

    steam64, steam_name, avatar_url = resolve_steam_profile(raw_steam_id)

    if not (steam64.isdigit() and len(steam64) == 17):
        return jsonify({'success': False, 'error': 'Invalid SteamID'}), 400

    existing_item = Replacement.query.filter_by(steam_id=steam64).first()
    if existing_item:
        if existing_item.spammer == current_username:
            return (
                jsonify({
                    'success': False,
                    'error': 'Этот SteamID уже закреплен за вами!',
                }),
                400,
            )
        return (
            jsonify({
                'success': False,
                'error': 'This SteamID is already claimed by another user',
            }),
            400,
        )

    now = datetime.now()

    new_item = Replacement(
        steam_id=steam64,
        steam_name=steam_name if steam_name else steam64,
        steam_url=f'https://steamcommunity.com/profiles/{steam64}',
        avatar_url=avatar_url,
        inv_tradable='0.00',
        inv_sub='0.00',
        breakdown_json=json.dumps(create_default_breakdown()),
        games='csgo',
        algorithm=data.get('algorithm', 4),
        min_dep=data.get('min_dep', 50),
        time=now.strftime('%H:%M:%S'),
        date=now.strftime('%d.%m.%Y'),
        spammer=current_username,
        note=data.get('note', ''),
    )

    db.session.add(new_item)
    db.session.commit()

    from flask import current_app
    app_ctx = current_app.app_context()
    threading.Thread(target=background_update_item, args=(app_ctx, new_item.id, steam64)).start()

    return jsonify({'success': True, 'item': new_item.to_dict()})


@replacements_bp.route(
    '/api/replacements/refresh/<int:item_id>', methods=['POST']
)
@login_required
def refresh_item(item_id):
    current_username = session.get('username', '')
    item = Replacement.query.filter_by(
        id=item_id, spammer=current_username
    ).first()
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

    res = fetch_steam_info_and_inventory(item.steam_id, force=True)
    steam64, s_name, a_url, inv_tr, inv_sb, games_str, breakdown = (
        res[0],
        res[1],
        res[2],
        res[3],
        res[4],
        res[5],
        res[6],
    )

    if not (
        inv_tr == '0.00'
        and inv_sb == '0.00'
        and (float(item.inv_tradable or 0) > 0 or float(item.inv_sub or 0) > 0)
    ):
        item.inv_tradable = inv_tr
        item.inv_sub = inv_sb
        item.breakdown_json = json.dumps(breakdown)

    item.steam_name = s_name
    item.avatar_url = a_url
    item.games = games_str
    db.session.commit()

    return jsonify({'success': True, 'item': item.to_dict()})


@replacements_bp.route(
    '/api/replacements/delete/<int:item_id>', methods=['POST', 'DELETE']
)
@login_required
def delete_replacement(item_id):
    current_username = session.get('username', '')
    item = Replacement.query.filter_by(
        id=item_id, spammer=current_username
    ).first()

    if not item:
        return jsonify({'success': False, 'error': 'Подмена не найдена'}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True, 'id': item_id})


@replacements_bp.route(
    '/api/replacements/inventory_breakdown/<steam_id>', methods=['GET']
)
@login_required
def get_inventory_breakdown(steam_id):
    item = Replacement.query.filter_by(steam_id=steam_id).first()
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

    breakdown_data = {}
    if item.breakdown_json:
        try:
            breakdown_data = json.loads(item.breakdown_json)
        except Exception:
            breakdown_data = {}

    tradable_map = breakdown_data.get('tradable', {})
    non_tradable_map = breakdown_data.get('non_tradable', {})
    updated_at = breakdown_data.get(
        'updated_at',
        f'{item.time} {item.date}'
        if item.time and item.date
        else datetime.now().strftime('%H:%M:%S %d.%m.%Y'),
    )

    games_list = [g.strip() for g in (item.games or 'csgo').split(',') if g.strip()]
    code_by_appid = {'730': 'csgo', '570': 'dota2', '252490': 'rust'}

    def build_game_list(data_map, fallback_price):
        result = []
        for app_id, price in data_map.items():
            try:
                p_val = float(price)
            except (ValueError, TypeError):
                p_val = 0.0

            app_str = str(app_id)
            game_code = code_by_appid.get(app_str, '')

            if p_val > 0 or (game_code and game_code in games_list):
                meta = GAMES_METADATA.get(
                    app_str, {'name': f'App {app_str}', 'icon': ''}
                )
                result.append({
                    'app_id': app_str,
                    'name': meta['name'],
                    'icon': meta['icon'],
                    'price': f'{p_val:.2f}',
                })

        if not result and float(fallback_price or 0) > 0:
            result.append({
                'app_id': '730',
                'name': GAMES_METADATA['730']['name'],
                'icon': GAMES_METADATA['730']['icon'],
                'price': fallback_price,
            })
        return result

    return jsonify({
        'success': True,
        'steam_id': item.steam_id,
        'steam_name': item.steam_name or item.steam_id,
        'updated_at': updated_at,
        'tradable': build_game_list(tradable_map, item.inv_tradable),
        'non_tradable': build_game_list(non_tradable_map, item.inv_sub),
    })


@replacements_bp.route('/api/replacements/get_all_profiles', methods=['GET'])
@login_required
def get_all_profiles():
    current_username = session.get('username', '')
    db_items = Replacement.query.filter_by(spammer=current_username).all()
    
    profiles = [
        {
            'steam_name': item.steam_name or item.steam_id,
            'steam_id': item.steam_id,
            'avatar_url': item.avatar_url
        }
        for item in db_items
    ]
    
    return jsonify({
        'success': True,
        'profiles': profiles,
        'updated_at': datetime.now().strftime('%H:%M:%S %d.%m.%Y')
    })