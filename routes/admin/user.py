from flask import Blueprint, current_app, redirect, render_template, request, session, url_for


user_bp = Blueprint('user_module', __name__, url_prefix='')


@user_bp.route('/users')
def users_route():
    from routes.admin.auth import login_required

    @login_required
    def _users():
        db = current_app.extensions['sqlalchemy']
        User = current_app.user_model_class
        if session.get('user_role') != 'admin':
            return redirect(url_for('admin.dashboard_route', message='Unauthorized', type='error'))
        
        # Pagination settings
        per_page = 10
        page = request.args.get('page', 1, type=int)
        
        # Get total count
        total_users = db.session.query(User).count()
        total_pages = max(1, (total_users + per_page - 1) // per_page)
        
        # Ensure page is valid
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        # Get paginated users
        start = (page - 1) * per_page
        users = db.session.execute(
            db.select(User).order_by(User.username).offset(start).limit(per_page)
        ).scalars().all()
        
        return render_template('dashboard/users.html', users=users, module_name='Users', module_icon='fa-user-gear', 
                             page=page, total_pages=total_pages, per_page=per_page, total=total_users)

    return _users()


@user_bp.route('/users/add', methods=['POST'])
def add_user():
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class

    if session.get('user_role') != 'admin':
        return redirect(url_for('admin.dashboard_route', message='Unauthorized', type='error'))

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'staff')
    is_active = request.form.get('is_active') == 'on'

    if not username or not password:
        return redirect(url_for('user_module.users_route', message='Username and password are required', type='error'))

    existing = db.session.execute(db.select(User).filter((User.username == username) | (User.email == email))).scalar_one_or_none()
    if existing:
        return redirect(url_for('user_module.users_route', message='User with that username or email already exists', type='info'))

    user = User(username=username, email=email, role=role, is_active=is_active)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('user_module.users_route', message='User created', type='success'))


@user_bp.route('/users/edit/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class

    if session.get('user_role') != 'admin':
        return redirect(url_for('admin.dashboard_route', message='Unauthorized', type='error'))

    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for('user_module.users_route', message='User not found', type='error'))

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'staff')
    is_active = request.form.get('is_active') == 'on'

    existing = db.session.execute(db.select(User).filter((User.username == username) | (User.email == email)).filter(User.id != user_id)).scalar_one_or_none()
    if existing:
        return redirect(url_for('user_module.users_route', message='Username or email already exists', type='error'))

    user.username = username
    user.email = email
    user.role = role
    user.is_active = is_active
    if password:
        user.set_password(password)

    db.session.commit()
    return redirect(url_for('user_module.users_route', message='User updated', type='success'))


@user_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class

    if session.get('user_role') != 'admin':
        return redirect(url_for('admin.dashboard_route', message='Unauthorized', type='error'))

    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('user_module.users_route', message='User deleted', type='success'))
    return redirect(url_for('user_module.users_route', message='User not found', type='error'))
