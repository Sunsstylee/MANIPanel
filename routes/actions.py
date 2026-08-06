from flask import Blueprint, render_template, session, redirect, url_for

actions_bp = Blueprint('actions', __name__)

@actions_bp.route('/actions')
def actions():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
        
    return render_template(
        'actions/actions.html', 
        active_page='actions'
    )