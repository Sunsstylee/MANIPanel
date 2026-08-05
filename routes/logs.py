from flask import Blueprint, render_template, request, session, redirect, url_for

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
def logs():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
        
    current_user = session.get('username')
    filter_status = request.args.get('filter', 'all')
    search_query = request.args.get('search', '').strip()

    # Общий список логов из базы данных
    all_logs = [
        {
            'id': 11820,
            'items': [
                'MAG-7 | Copper Oxide (Minimal Wear)',
                'StatTrak™ AWP | Duality (Field-Tested)'
            ],
            'extra_items': [f'Дополнительный предмет #{i}' for i in range(1, 24)],
            'price': 373.3,
            'status': 'accepted',
            'hold_time': '1d20h',
            'game': 'CS',
            'offer_id': '9271032200',
            'steam_id': '76561198441151720',
            'spamer': 'Sunix',
            'payout_status': None,
            'date': '31.07.2026 | 19:28:04'
        },
        {
            'id': 11821,
            'items': ['AK-47 | Redline (Field-Tested)'],
            'extra_items': [],
            'price': 15.0,
            'status': 'sent',
            'hold_time': None,
            'game': 'CS',
            'offer_id': '9271032201',
            'steam_id': '76561198000000000',
            'spamer': 'OtherUser',
            'payout_status': 'unpaid',
            'date': '01.08.2026 | 12:10:00'
        }
    ]

    # Фильтрация: выборка логов только текущего воркера
    user_logs = [log for log in all_logs if log['spamer'].lower() == str(current_user).lower()]

    # Фильтрация по табам (статусам)
    if filter_status == 'accepted':
        user_logs = [l for l in user_logs if l['status'] == 'accepted']
    elif filter_status == 'sent':
        user_logs = [l for l in user_logs if l['status'] == 'sent']
    elif filter_status == 'unpaid':
        user_logs = [l for l in user_logs if l['payout_status'] == 'unpaid']
    elif filter_status == 'hold':
        user_logs = [l for l in user_logs if l['hold_time'] is not None]
    elif filter_status == 'cs':
        user_logs = [l for l in user_logs if l['game'] == 'CS']

    # Фильтрация по поисковой строке (по ID, SteamID или OfferID)
    if search_query:
        user_logs = [
            l for l in user_logs 
            if search_query in str(l['id']) or search_query in l['steam_id'] or search_query in l['offer_id']
        ]

    return render_template(
        'logs/logs.html', 
        logs=user_logs, 
        current_filter=filter_status,
        search_query=search_query,
        active_page='logs'
    )