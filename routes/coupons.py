"""
Coupon and Discount Routes
Manage promotional codes and discount validation
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime

coupon_bp = Blueprint('coupon', __name__, url_prefix='/coupon')

# ============ VALIDATE COUPON ============
@coupon_bp.route('/validate', methods=['POST'])
def validate_coupon():
    """Validate a coupon code and get discount details"""
    from app import db
    
    data = request.get_json()
    coupon_code = data.get('code', '').upper().strip()
    cart_total = data.get('cart_total', type=float)
    
    if not coupon_code:
        return jsonify({'success': False, 'message': 'Coupon code is required'}), 400
    
    Coupon = current_app.coupon_model_class
    
    coupon = db.session.query(Coupon).filter_by(code=coupon_code).first()
    
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'}), 404
    
    if not coupon.is_active:
        return jsonify({'success': False, 'message': 'Coupon is not active'}), 400
    
    now = datetime.utcnow()
    if coupon.start_date > now:
        return jsonify({'success': False, 'message': 'Coupon is not yet valid'}), 400
    
    if coupon.end_date < now:
        return jsonify({'success': False, 'message': 'Coupon has expired'}), 400
    
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        return jsonify({'success': False, 'message': 'Coupon usage limit reached'}), 400
    
    if coupon.min_purchase and cart_total < coupon.min_purchase:
        return jsonify({
            'success': False,
            'message': f'Minimum purchase of ${coupon.min_purchase:.2f} required'
        }), 400
    
    # Calculate discount
    discount_amount = 0
    if coupon.discount_percentage:
        discount_amount = cart_total * (coupon.discount_percentage / 100)
    elif coupon.discount_amount:
        discount_amount = coupon.discount_amount
    
    discount_amount = min(discount_amount, cart_total)  # Can't discount more than total
    
    return jsonify({
        'success': True,
        'coupon_id': coupon.id,
        'code': coupon.code,
        'discount_type': 'percentage' if coupon.discount_percentage else 'fixed',
        'discount_value': coupon.discount_percentage or coupon.discount_amount,
        'discount_amount': round(discount_amount, 2),
        'final_total': round(cart_total - discount_amount, 2)
    })

# ============ APPLY COUPON TO ORDER ============
@coupon_bp.route('/apply', methods=['POST'])
def apply_coupon_to_order():
    """Apply coupon to current order/checkout"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    coupon_code = data.get('code', '').upper().strip()
    cart_total = data.get('cart_total', type=float)
    
    if not coupon_code:
        return jsonify({'success': False, 'message': 'Coupon code is required'}), 400
    
    Coupon = current_app.coupon_model_class
    
    coupon = db.session.query(Coupon).filter_by(code=coupon_code).first()
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code'}), 404
    
    # Validate coupon
    validation_response = validate_coupon()
    if validation_response.json.get('success'):
        # Increment usage count
        coupon.used_count += 1
        db.session.commit()
        
        discount_info = validation_response.json
        return jsonify({
            'success': True,
            'message': f'Coupon "{coupon_code}" applied successfully',
            **discount_info
        })
    else:
        return validation_response

# ============ GET ACTIVE COUPONS ============
@coupon_bp.route('/active', methods=['GET'])
def get_active_coupons():
    """Get list of currently active coupons"""
    from app import db
    
    Coupon = current_app.coupon_model_class
    
    now = datetime.utcnow()
    
    coupons = db.session.query(Coupon).filter(
        Coupon.is_active == True,
        Coupon.start_date <= now,
        Coupon.end_date >= now
    ).all()
    
    coupons_data = []
    for coupon in coupons:
        coupons_data.append({
            'code': coupon.code,
            'discount_type': 'percentage' if coupon.discount_percentage else 'fixed',
            'discount_value': coupon.discount_percentage or coupon.discount_amount,
            'min_purchase': coupon.min_purchase,
            'max_uses': coupon.max_uses,
            'used_count': coupon.used_count,
            'remaining_uses': coupon.max_uses - coupon.used_count if coupon.max_uses else None,
            'expires_at': coupon.end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'applicable_categories': coupon.applicable_categories
        })
    
    return jsonify({
        'success': True,
        'total_coupons': len(coupons_data),
        'coupons': coupons_data
    })

# ============ CREATE COUPON (ADMIN) ============
@coupon_bp.route('/create', methods=['POST'])
def create_coupon():
    """Create a new coupon (Admin only)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    Coupon = current_app.coupon_model_class
    
    try:
        new_coupon = Coupon(
            code=data.get('code', '').upper(),
            discount_percentage=data.get('discount_percentage'),
            discount_amount=data.get('discount_amount'),
            max_uses=data.get('max_uses'),
            min_purchase=data.get('min_purchase'),
            applicable_categories=data.get('applicable_categories'),
            start_date=datetime.fromisoformat(data.get('start_date')) if data.get('start_date') else datetime.utcnow(),
            end_date=datetime.fromisoformat(data.get('end_date')) if data.get('end_date') else None,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_coupon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Coupon created successfully',
            'coupon_id': new_coupon.id,
            'code': new_coupon.code
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# ============ DELETE COUPON (ADMIN) ============
@coupon_bp.route('/<int:coupon_id>', methods=['DELETE'])
def delete_coupon(coupon_id):
    """Delete a coupon (Admin only)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    Coupon = current_app.coupon_model_class
    
    coupon = db.session.query(Coupon).get(coupon_id)
    if not coupon:
        return jsonify({'success': False, 'message': 'Coupon not found'}), 404
    
    db.session.delete(coupon)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon deleted successfully'})

# ============ UPDATE COUPON (ADMIN) ============
@coupon_bp.route('/<int:coupon_id>/update', methods=['PUT', 'POST'])
def update_coupon(coupon_id):
    """Update coupon details (Admin only)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    User = current_app.user_model_class
    user = db.session.query(User).get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    Coupon = current_app.coupon_model_class
    
    coupon = db.session.query(Coupon).get(coupon_id)
    if not coupon:
        return jsonify({'success': False, 'message': 'Coupon not found'}), 404
    
    data = request.get_json()
    
    if 'code' in data:
        coupon.code = data['code'].upper()
    if 'discount_percentage' in data:
        coupon.discount_percentage = data['discount_percentage']
    if 'discount_amount' in data:
        coupon.discount_amount = data['discount_amount']
    if 'max_uses' in data:
        coupon.max_uses = data['max_uses']
    if 'min_purchase' in data:
        coupon.min_purchase = data['min_purchase']
    if 'applicable_categories' in data:
        coupon.applicable_categories = data['applicable_categories']
    if 'is_active' in data:
        coupon.is_active = data['is_active']
    if 'start_date' in data:
        coupon.start_date = datetime.fromisoformat(data['start_date'])
    if 'end_date' in data:
        coupon.end_date = datetime.fromisoformat(data['end_date'])
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Coupon updated successfully'})
