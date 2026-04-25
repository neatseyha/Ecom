"""
Shopping Cart Routes
Display and manage shopping cart
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

# ============ VIEW CART ============
@cart_bp.route('/', methods=['GET'])
def view_cart():
    """Display shopping cart"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    CartItem = current_app.cart_item_model_class
    Product = current_app.product_model_class
    
    cart_items = db.session.query(CartItem).filter_by(user_id=user_id).all()
    
    total_price = 0
    items_data = []
    
    for item in cart_items:
        product = db.session.query(Product).get(item.product_id)
        if product:
            item_total = item.price * item.quantity
            total_price += item_total
            items_data.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': product.product_name,
                'quantity': item.quantity,
                'price': item.price,
                'item_total': item_total,
                'size': item.size,
                'color': item.color,
                'image': product.image,
                'stock': product.stock
            })
    
    return render_template('cart.html', 
                          cart_items=items_data,
                          total_price=round(total_price, 2),
                          item_count=len(items_data))

# ============ ADD TO CART ============
@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    from app import db, current_app
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    size = request.form.get('size')
    color = request.form.get('color')
    
    CartItem = current_app.cart_item_model_class
    Product = current_app.product_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(request.referrer or url_for('shop'))
    
    if product.stock < quantity:
        flash('Insufficient stock', 'error')
        return redirect(request.referrer or url_for('shop'))
    
    # Check if item already in cart
    existing = db.session.query(CartItem).filter_by(
        user_id=user_id,
        product_id=product_id,
        size=size,
        color=color
    ).first()
    
    if existing:
        existing.quantity += quantity
        db.session.commit()
        flash(f'Updated {product.product_name} quantity in cart', 'success')
    else:
        cart_item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            price=product.price,
            size=size,
            color=color,
            added_date=datetime.utcnow()
        )
        db.session.add(cart_item)
        db.session.commit()
        flash(f'Added {product.product_name} to cart', 'success')
    
    return redirect(request.referrer or url_for('view_cart'))

# ============ UPDATE CART QUANTITY ============
@cart_bp.route('/update/<int:cart_item_id>', methods=['POST'])
def update_quantity(cart_item_id):
    """Update cart item quantity"""
    from app import db, current_app
    
    quantity = request.form.get('quantity', type=int)
    CartItem = current_app.cart_item_model_class
    
    cart_item = db.session.query(CartItem).get(cart_item_id)
    if not cart_item:
        flash('Cart item not found', 'error')
        return redirect(url_for('cart.view_cart'))
    
    if quantity <= 0:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    else:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated', 'success')
    
    return redirect(url_for('cart.view_cart'))

# ============ REMOVE FROM CART ============
@cart_bp.route('/remove/<int:cart_item_id>', methods=['POST'])
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    from app import db, current_app
    
    CartItem = current_app.cart_item_model_class
    cart_item = db.session.query(CartItem).get(cart_item_id)
    
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    
    return redirect(url_for('cart.view_cart'))

# ============ CLEAR CART ============
@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    """Clear entire cart"""
    from app import db, current_app
    
    user_id = session.get('user_id')
    CartItem = current_app.cart_item_model_class
    
    db.session.query(CartItem).filter_by(user_id=user_id).delete()
    db.session.commit()
    flash('Cart cleared', 'success')
    
    return redirect(url_for('cart.view_cart'))
