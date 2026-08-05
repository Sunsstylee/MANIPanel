from flask import Blueprint, render_template, request, session, redirect, url_for

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
def logs():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
        
    filter_status = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()

    # Пример структуры данных логов (замените на реальный запрос к БД при необходимости)
    sample_logs = [
        {
            "id": 11820,
            "items": ["MAG-7 | Copper Oxide (Minimal Wear)", "StatTrak™ AWP | Duality (Field-Tested)"],
            "extra_items_count": 23,
            "price": 373.30,
            "status": "accepted",
            "hold_time": "1d21h",
            "game": "CS",
            "offer_id": "9271032200",
            "steam_id": "76561198441151720",
            "spamer": "Sunsstylee",
            "payout_status": "none",
            "date": "31.07.2026 | 19:28:04"
        },
        {
            "id": 11531,
            "items": ["MP9 | Buff Blue (Field-Tested)", "Kilowatt Case"],
            "extra_items_count": 84,
            "price": 241.48,
            "status": "accepted",
            "hold_time": None,
            "game": "CS",
            "offer_id": "9259800265",
            "steam_id": "76561198816312097",
            "spamer": "Sunsstylee",
            "payout_status": "unpaid",
            "date": "26.07.2026 | 16:25:46"
        },
        {
            "id": 11415,
            "items": ["Galil AR | Chromatic Aberration (Well-Worn)", "Tec-9 | Brother (Well-Worn)"],
            "extra_items_count": 93,
            "price": 238.32,
            "status": "accepted",
            "hold_time": None,
            "game": "CS",
            "offer_id": "9254199107",
            "steam_id": "76561199518513741",
            "spamer": "Sunsstylee",
            "payout_status": "paid",
            "date": "24.07.2026 | 01:05:20"
        }
    ]

    return render_template(
        'logs/logs.html', 
        logs=sample_logs, 
        current_filter=filter_status,
        search_query=search_query,
        active_page='logs'
    )