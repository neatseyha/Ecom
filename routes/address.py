"""
Address Management Routes
Display and manage user addresses
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime

address_bp = Blueprint('address', __name__, url_prefix='/address')

# ============ ADDRESS LIST ============
@address_bp.route('/', methods=['GET'])
def address_list():
    """Display all user addresses"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Address = current_app.address_model_class
    addresses = db.session.query(Address).filter_by(user_id=user_id).all()
    
    return render_template('address_list.html', addresses=addresses)

# ============ ADD ADDRESS ============
@address_bp.route('/add', methods=['GET', 'POST'])
def add_address():
    """Add new address"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('add_address.html')
    
    # POST request
    Address = current_app.address_model_class
    
    address_type = request.form.get('type', 'shipping')
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    street_address = request.form.get('street_address')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')
    country = request.form.get('country')
    is_default = request.form.get('is_default') == 'on'
    
    if not all([full_name, phone, street_address, city, zip_code, country]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('address.add_address'))
    
    try:
        # If setting as default, unset other defaults of same type
        if is_default:
            db.session.query(Address).filter_by(
                user_id=user_id,
                type=address_type
            ).update({'is_default': False})
        
        address = Address(
            user_id=user_id,
            type=address_type,
            full_name=full_name,
            phone=phone,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            is_default=is_default,
            created_at=datetime.utcnow()
        )
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully', 'success')
        return redirect(url_for('address.address_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding address: {str(e)}', 'error')
        return redirect(url_for('address.add_address'))

# ============ EDIT ADDRESS ============
@address_bp.route('/<int:address_id>/edit', methods=['GET', 'POST'])
def edit_address(address_id):
    """Edit existing address"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Address = current_app.address_model_class
    address = db.session.query(Address).get(address_id)
    
    if not address or address.user_id != user_id:
        flash('Address not found', 'error')
        return redirect(url_for('address.address_list'))
    
    if request.method == 'GET':
        return render_template('edit_address.html', address=address)
    
    # POST request
    try:
        address.full_name = request.form.get('full_name')
        address.phone = request.form.get('phone')
        address.street_address = request.form.get('street_address')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.zip_code = request.form.get('zip_code')
        address.country = request.form.get('country')
        
        is_default = request.form.get('is_default') == 'on'
        if is_default:
            db.session.query(Address).filter_by(
                user_id=user_id,
                type=address.type
            ).update({'is_default': False})
            address.is_default = True
        
        db.session.commit()
        flash('Address updated successfully', 'success')
        return redirect(url_for('address.address_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating address: {str(e)}', 'error')
        return redirect(url_for('address.edit_address', address_id=address_id))

# ============ DELETE ADDRESS ============
@address_bp.route('/<int:address_id>/delete', methods=['POST'])
def delete_address(address_id):
    """Delete address"""
    from app import db
    
    user_id = session.get('user_id')
    Address = current_app.address_model_class
    
    address = db.session.query(Address).get(address_id)
    
    if address and address.user_id == user_id:
        db.session.delete(address)
        db.session.commit()
        flash('Address deleted successfully', 'success')
    else:
        flash('Address not found', 'error')
    
    return redirect(url_for('address.address_list'))

# ============ SET DEFAULT ADDRESS ============
@address_bp.route('/<int:address_id>/set-default', methods=['POST'])
def set_default_address(address_id):
    """Set address as default"""
    from app import db
    
    user_id = session.get('user_id')
    Address = current_app.address_model_class
    
    address = db.session.query(Address).get(address_id)
    
    if not address or address.user_id != user_id:
        flash('Address not found', 'error')
        return redirect(url_for('address.address_list'))
    
    # Unset other defaults of same type
    db.session.query(Address).filter_by(
        user_id=user_id,
        type=address.type
    ).update({'is_default': False})
    
    address.is_default = True
    db.session.commit()
    
    flash('Address set as default', 'success')
    return redirect(url_for('address.address_list'))
