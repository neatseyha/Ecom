"""
User Profile Management Routes
Manage user account settings, personal information, and security
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
import os

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

# ============ VIEW PROFILE ============
@profile_bp.route('/', methods=['GET'])
def view_profile():
    """Display user profile page"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    from app import db
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('home'))
    
    return render_template('profile/view_profile.html', user=user)

# ============ GET PROFILE DATA (API) ============
@profile_bp.route('/data', methods=['GET'])
def get_profile_data():
    """Get user profile data as JSON"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'profile_picture': user.profile_picture,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth.strftime('%Y-%m-%d') if user.date_of_birth else None,
            'bio': user.bio,
            'address': user.address,
            'city': user.city,
            'state': user.state,
            'zip_code': user.zip_code,
            'country': user.country,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'newsletter_subscribed': user.newsletter_subscribed,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            'created_at': user.create_at.strftime('%Y-%m-%d %H:%M:%S') if user.create_at else None
        }
    })

# ============ UPDATE PROFILE ============
@profile_bp.route('/update', methods=['POST', 'PUT'])
def update_profile():
    """Update user profile information"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    data = request.get_json() if request.is_json else request.form
    
    # Update allowed fields
    allowed_fields = [
        'first_name', 'last_name', 'phone', 'gender', 'date_of_birth',
        'bio', 'address', 'city', 'state', 'zip_code', 'country', 'newsletter_subscribed'
    ]
    
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field == 'date_of_birth' and value:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            elif field == 'newsletter_subscribed':
                value = bool(value)
            setattr(user, field, value)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

# ============ UPDATE PROFILE PICTURE ============
@profile_bp.route('/picture/update', methods=['POST'])
def update_profile_picture():
    """Update user profile picture"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    if 'profile_picture' not in request.files:
        return jsonify({'success': False, 'message': 'No image provided'}), 400
    
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No image selected'}), 400
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    if not file or '.' not in file.filename:
        return jsonify({'success': False, 'message': 'Invalid file'}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'success': False, 'message': f'Only {", ".join(ALLOWED_EXTENSIONS)} files allowed'}), 400
    
    if len(file.read()) > MAX_FILE_SIZE:
        file.seek(0)
        return jsonify({'success': False, 'message': 'File too large (max 5MB)'}), 400
    
    file.seek(0)
    
    filename = f'profile_{user_id}_{datetime.utcnow().timestamp()}.{ext}'
    filename = secure_filename(filename)
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/upload')
    os.makedirs(upload_folder, exist_ok=True)
    
    file.save(os.path.join(upload_folder, filename))
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    user.profile_picture = filename
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profile picture updated',
        'picture_url': f'/static/upload/{filename}'
    })

# ============ CHANGE PASSWORD ============
@profile_bp.route('/password/change', methods=['POST', 'PUT'])
def change_password():
    """Change user password"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    data = request.get_json() if request.is_json else request.form
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user or not user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

# ============ DELETE ACCOUNT ============
@profile_bp.route('/delete', methods=['POST', 'DELETE'])
def delete_account():
    """Delete user account (soft delete)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    data = request.get_json() if request.is_json else request.form
    password = data.get('password', '')
    confirm_delete = data.get('confirm_delete', False)
    
    if not password or not confirm_delete:
        return jsonify({'success': False, 'message': 'Confirm deletion and provide password'}), 400
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Incorrect password'}), 401
    
    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    db.session.commit()
    
    # Clear session
    session.clear()
    
    return jsonify({'success': True, 'message': 'Account deleted successfully'})

# ============ GET ACCOUNT STATS ============
@profile_bp.route('/stats', methods=['GET'])
def get_account_stats():
    """Get user account statistics"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    Order = current_app.order_model_class
    Wishlist = current_app.wishlist_model_class
    Rating = current_app.rating_model_class
    
    total_orders = db.session.query(Order).filter_by(user_id=user_id).count()
    total_spent = db.session.query(db.func.sum(Order.total_amount)).filter_by(
        user_id=user_id
    ).scalar() or 0
    wishlist_count = db.session.query(Wishlist).filter_by(user_id=user_id).count()
    reviews_count = db.session.query(Rating).filter_by(user_id=user_id).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_orders': total_orders,
            'total_spent': round(float(total_spent), 2),
            'wishlist_items': wishlist_count,
            'reviews_submitted': reviews_count
        }
    })

# ============ GET PREFERENCES ============
@profile_bp.route('/preferences', methods=['GET'])
def get_preferences():
    """Get user preferences and settings"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    return jsonify({
        'success': True,
        'preferences': {
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'newsletter_subscribed': user.newsletter_subscribed
        }
    })

# ============ UPDATE PREFERENCES ============
@profile_bp.route('/preferences/update', methods=['POST', 'PUT'])
def update_preferences():
    """Update user preferences"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    from app import db
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    data = request.get_json() if request.is_json else request.form
    
    if 'newsletter_subscribed' in data:
        user.newsletter_subscribed = bool(data['newsletter_subscribed'])
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Preferences updated'})
