import os

from flask import Blueprint, render_template, url_for, g, session, current_app
from blueprints.helper.siweman import SignInManager
from persistence.storage import Storage
from blueprints.helper.common import get_input
from functools import wraps

from werkzeug.utils import redirect

from blueprints.helper.common import db

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')

SERVICE_DOMAIN = os.getenv('SERVICE_DOMAIN', 'crude.1kloc.com')
SERVICE_URI = os.getenv('SERVICE_URI', 'http://crude.1kloc.com:5000')
ADMIN_WALLET = os.getenv('ADMIN_WALLET', '0x993a8C4EC5dF95C45A5929660062445391204fC7')
if ',' in ADMIN_WALLET:
    ADMIN_WALLET = ADMIN_WALLET.split(',')
else:
    ADMIN_WALLET = [ADMIN_WALLET]


@auth_blueprint.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@auth_blueprint.route('/logout', methods=['GET'])
def logout():
    session.pop('wallet', None)
    return redirect(url_for('auth.login'))


@auth_blueprint.route('/login/<wallet>', methods=['GET'])
def login_request(wallet):
    siwe = SignInManager(db().get_collection('_users'))
    siwe_message = siwe.createSiweMessage(SERVICE_DOMAIN, SERVICE_URI, wallet, 'You are requesting a login.')
    return {'message': 'Please sign this message', 'siwe_message': siwe_message}


@auth_blueprint.route('/login/<wallet>', methods=['POST'])
def authenticate(wallet):
    # get form data from body
    is_json, data = get_input()
    siwe = SignInManager(db().get_collection('_users'))
    if not siwe.validate_signature_message(data):
        return {'message': 'Invalid signature'}, 401
    # set the session to authenticated
    user_address = data['address']
    if user_address not in ADMIN_WALLET:
        print('Expected One of:', ADMIN_WALLET)
        print('Got:', user_address)
        return {'message': 'Invalid wallet'}, 401

    session['wallet'] = wallet
    return {'success': True, 'redirect': url_for('model.browse')}


def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet' not in session or not session['wallet']:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

