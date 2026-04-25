from functools import wraps

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for


auth_bp = Blueprint('auth', __name__, url_prefix='')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('auth.login', next=request.path, message='Please login to access this page', type='info'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class

    message = request.args.get('message')
    msg_type = request.args.get('type', 'info')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        next_url = request.form.get('next') or request.args.get('next')

        user = db.session.execute(
            db.select(User).filter((User.username == username) | (User.email == username))
        ).scalar_one_or_none()

        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['user_name'] = user.username
            session['user_role'] = user.role
            if remember:
                session.permanent = True
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('admin.dashboard_route', message='Logged in successfully', type='success'))

        message = 'Invalid credentials or inactive user'
        msg_type = 'error'

    return render_template('auth/login_new.html', message=message, message_type=msg_type)


@auth_bp.route('/logout')
@auth_bp.route('/admin/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_role', None)
    return redirect(url_for('auth.login', message='Logged out', type='info'))
