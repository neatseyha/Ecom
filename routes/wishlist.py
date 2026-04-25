"""
Wishlist Routes
Manage user wishlists and favorite items
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from datetime import datetime

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

# ============ VIEW WISHLIST ============
@wishlist_bp.route('/', methods=['GET'])
def view_wishlist():
    """Display user's wishlist"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Wishlist = current_app.wishlist_model_class
    Product = current_app.product_model_class
    
    wishlist_items = db.session.query(Wishlist).filter_by(user_id=user_id).all()
    
    items_data = []
    for item in wishlist_items:
        product = db.session.query(Product).get(item.product_id)
        if product:
            items_data.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': product.product_name,
                'product_price': product.price,
                'product_image': product.image,
                'discount_percentage': product.discount_percentage,
                'discount_price': product.discount_price,
                'priority': item.priority,
                'notes': item.notes,
                'category_type': item.category_type,
                'is_price_watch_enabled': item.is_price_watch_enabled,
                'target_price': item.target_price,
                'added_date': item.added_date.strftime('%Y-%m-%d %H:%M:%S') if item.added_date else None,
                'stock': product.stock
            })
    
    return render_template('wishlist.html', 
                          wishlist_items=items_data,
                          total_items=len(items_data))

# ============ ADD TO WISHLIST ============
@wishlist_bp.route('/add', methods=['POST'])
def add_to_wishlist():
    """Add product to wishlist"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json() if request.is_json else request.form
    product_id = data.get('product_id', type=int)
    priority = data.get('priority', 'medium')
    notes = data.get('notes', '')
    category_type = data.get('category_type', 'favorites')
    
    Product = current_app.product_model_class
    Wishlist = current_app.wishlist_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Check if already in wishlist
    existing = db.session.query(Wishlist).filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Product already in wishlist'}), 409
    
    wishlist_item = Wishlist(
        user_id=user_id,
        product_id=product_id,
        product_name=product.product_name,
        product_price=product.price,
        product_image=product.image,
        priority=priority,
        notes=notes,
        category_type=category_type
    )
    
    db.session.add(wishlist_item)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Added to wishlist', 'item_id': wishlist_item.id})
    else:
        flash(f'Added {product.product_name} to wishlist', 'success')
        return redirect(request.referrer or url_for('wishlist.view_wishlist'))

# ============ REMOVE FROM WISHLIST ============
@wishlist_bp.route('/remove/<int:wishlist_id>', methods=['POST', 'DELETE'])
def remove_from_wishlist(wishlist_id):
    """Remove product from wishlist"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Wishlist = current_app.wishlist_model_class
    
    wishlist_item = db.session.query(Wishlist).get(wishlist_id)
    if not wishlist_item:
        return jsonify({'success': False, 'message': 'Wishlist item not found'}), 404
    
    if wishlist_item.user_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Removed from wishlist'})
    else:
        flash('Removed from wishlist', 'success')
        return redirect(request.referrer or url_for('wishlist.view_wishlist'))

# ============ UPDATE WISHLIST ITEM ============
@wishlist_bp.route('/update/<int:wishlist_id>', methods=['POST', 'PUT'])
def update_wishlist_item(wishlist_id):
    """Update wishlist item details (priority, notes, etc)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Wishlist = current_app.wishlist_model_class
    
    wishlist_item = db.session.query(Wishlist).get(wishlist_id)
    if not wishlist_item:
        return jsonify({'success': False, 'message': 'Wishlist item not found'}), 404
    
    if wishlist_item.user_id != user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json() if request.is_json else request.form
    
    if 'priority' in data:
        wishlist_item.priority = data['priority']
    if 'notes' in data:
        wishlist_item.notes = data['notes']
    if 'category_type' in data:
        wishlist_item.category_type = data['category_type']
    if 'is_price_watch_enabled' in data:
        wishlist_item.is_price_watch_enabled = bool(data['is_price_watch_enabled'])
    if 'target_price' in data:
        wishlist_item.target_price = float(data['target_price']) if data['target_price'] else None
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Wishlist item updated'})

# ============ MOVE TO CART ============
@wishlist_bp.route('/to-cart/<int:wishlist_id>', methods=['POST'])
def wishlist_to_cart(wishlist_id):
    """Move item from wishlist to shopping cart"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Wishlist = current_app.wishlist_model_class
    CartItem = current_app.cart_item_model_class
    Product = current_app.product_model_class
    
    wishlist_item = db.session.query(Wishlist).get(wishlist_id)
    if not wishlist_item:
        flash('Wishlist item not found', 'error')
        return redirect(url_for('wishlist.view_wishlist'))
    
    if wishlist_item.user_id != user_id:
        flash('Unauthorized', 'error')
        return redirect(url_for('wishlist.view_wishlist'))
    
    product = db.session.query(Product).get(wishlist_item.product_id)
    if not product or product.stock < 1:
        flash('Product not available', 'error')
        return redirect(url_for('wishlist.view_wishlist'))
    
    # Check if already in cart
    existing_cart = db.session.query(CartItem).filter_by(
        user_id=user_id,
        product_id=wishlist_item.product_id
    ).first()
    
    if existing_cart:
        existing_cart.quantity += 1
    else:
        cart_item = CartItem(
            user_id=user_id,
            product_id=wishlist_item.product_id,
            quantity=1,
            price=product.price
        )
        db.session.add(cart_item)
    
    # Remove from wishlist
    db.session.delete(wishlist_item)
    db.session.commit()
    
    flash(f'Added {product.product_name} to cart', 'success')
    return redirect(url_for('cart.view_cart'))

# ============ GET WISHLIST COUNT ============
@wishlist_bp.route('/count', methods=['GET'])
def get_wishlist_count():
    """Get number of items in user's wishlist (API endpoint)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'count': 0})
    
    Wishlist = current_app.wishlist_model_class
    count = db.session.query(Wishlist).filter_by(user_id=user_id).count()
    
    return jsonify({'count': count})

# ============ CLEAR WISHLIST ============
@wishlist_bp.route('/clear', methods=['POST', 'DELETE'])
def clear_wishlist():
    """Clear entire wishlist"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Wishlist = current_app.wishlist_model_class
    
    db.session.query(Wishlist).filter_by(user_id=user_id).delete()
    db.session.commit()
    
    flash('Wishlist cleared', 'success')
    return redirect(url_for('wishlist.view_wishlist'))
