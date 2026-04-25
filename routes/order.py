"""
Order Management Routes
View and manage orders
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app

order_bp = Blueprint('order', __name__, url_prefix='/order')

# ============ ORDER DETAIL ============
@order_bp.route('/<int:order_id>', methods=['GET'])
def order_detail(order_id):
    """Display order details"""
    from app import db
    
    user_id = session.get('user_id')
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    Product = current_app.product_model_class
    Shipping = current_app.shipping_model_class
    Payment = current_app.payment_model_class
    
    order = db.session.query(Order).get(order_id)
    if not order or order.user_id != user_id:
        flash('Order not found', 'error')
        return redirect(url_for('shop'))
    
    # Get order items
    items = db.session.query(OrderItem).filter_by(order_id=order_id).all()
    items_data = []
    for item in items:
        product = db.session.query(Product).get(item.product_id)
        items_data.append({
            'product_name': item.product_name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item.total,
            'size': item.size,
            'color': item.color,
            'image': product.image if product else None
        })
    
    # Get shipping info
    shipping = db.session.query(Shipping).filter_by(order_id=order_id).first()
    
    # Get payment info
    payment = db.session.query(Payment).filter_by(order_id=order_id).first()
    
    return render_template('order_detail.html',
                          order=order,
                          items=items_data,
                          shipping=shipping,
                          payment=payment)

# ============ ORDER HISTORY ============
@order_bp.route('/history', methods=['GET'])
def order_history():
    """Display user's order history"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Order = current_app.order_model_class
    
    orders = db.session.query(Order).filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'order_date': order.order_date,
            'grand_total': order.grand_total,
            'status': order.status,
            'payment_status': order.payment_status,
            'tracking_number': order.tracking_number
        })
    
    return render_template('order_history.html', orders=orders_data)

# ============ CANCEL ORDER ============
@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order"""
    from app import db
    from datetime import datetime
    
    user_id = session.get('user_id')
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    Product = current_app.product_model_class
    
    order = db.session.query(Order).get(order_id)
    if not order or order.user_id != user_id:
        flash('Order not found', 'error')
        return redirect(url_for('order.order_history'))
    
    if order.status == 'cancelled':
        flash('Order is already cancelled', 'warning')
        return redirect(url_for('order.order_detail', order_id=order_id))
    
    if order.status in ['shipped', 'delivered']:
        flash('Cannot cancel shipped or delivered orders', 'error')
        return redirect(url_for('order.order_detail', order_id=order_id))
    
    try:
        # Restore product stock
        items = db.session.query(OrderItem).filter_by(order_id=order_id).all()
        for item in items:
            product = db.session.query(Product).get(item.product_id)
            if product:
                product.stock += item.quantity
        
        order.status = 'cancelled'
        order.cancel_reason = request.form.get('reason', 'Cancelled by user')
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Order cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling order: {str(e)}', 'error')
    
    return redirect(url_for('order.order_detail', order_id=order_id))

# ============ TRACK ORDER ============
@order_bp.route('/<int:order_id>/track', methods=['GET'])
def track_order(order_id):
    """Track order shipping"""
    from app import db
    
    user_id = session.get('user_id')
    Order = current_app.order_model_class
    Shipping = current_app.shipping_model_class
    
    order = db.session.query(Order).get(order_id)
    if not order or order.user_id != user_id:
        flash('Order not found', 'error')
        return redirect(url_for('shop'))
    
    shipping = db.session.query(Shipping).filter_by(order_id=order_id).first()
    
    return render_template('track_order.html', order=order, shipping=shipping)

# ============ ORDER SUMMARY ============
@order_bp.route('/summary', methods=['GET'])
def get_order_summary():
    """Get user's order summary/statistics"""
    from app import db
    from sqlalchemy import func
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    
    # Get order statistics
    total_orders = db.session.query(Order).filter_by(user_id=user_id).count()
    total_spent = db.session.query(func.sum(Order.grand_total)).filter_by(user_id=user_id).scalar() or 0
    
    # Get status breakdown
    pending_count = db.session.query(Order).filter_by(user_id=user_id, status='pending').count()
    processing_count = db.session.query(Order).filter_by(user_id=user_id, status='processing').count()
    shipped_count = db.session.query(Order).filter_by(user_id=user_id, status='shipped').count()
    delivered_count = db.session.query(Order).filter_by(user_id=user_id, status='delivered').count()
    cancelled_count = db.session.query(Order).filter_by(user_id=user_id, status='cancelled').count()
    
    # Get items purchased
    total_items = db.session.query(func.sum(OrderItem.quantity)).join(
        Order, OrderItem.order_id == Order.id
    ).filter(Order.user_id == user_id).scalar() or 0
    
    # Get average order value
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0
    
    # Get recent orders
    recent_orders = db.session.query(Order).filter_by(
        user_id=user_id
    ).order_by(Order.order_date.desc()).limit(5).all()
    
    recent_orders_data = [{
        'id': order.id,
        'order_number': order.order_number,
        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else None,
        'grand_total': order.grand_total,
        'status': order.status
    } for order in recent_orders]
    
    return jsonify({
        'success': True,
        'summary': {
            'total_orders': total_orders,
            'total_spent': round(float(total_spent), 2),
            'average_order_value': round(float(avg_order_value), 2),
            'total_items_purchased': int(total_items),
            'status_breakdown': {
                'pending': pending_count,
                'processing': processing_count,
                'shipped': shipped_count,
                'delivered': delivered_count,
                'cancelled': cancelled_count
            },
            'recent_orders': recent_orders_data
        }
    })

# ============ REORDER ============
@order_bp.route('/<int:order_id>/reorder', methods=['POST'])
def reorder(order_id):
    """Create a new order with items from a previous order"""
    from app import db
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    CartItem = current_app.cart_item_model_class
    Product = current_app.product_model_class
    
    original_order = db.session.query(Order).get(order_id)
    if not original_order or original_order.user_id != user_id:
        flash('Order not found', 'error')
        return redirect(url_for('order.order_history'))
    
    try:
        # Add items from original order to cart
        order_items = db.session.query(OrderItem).filter_by(order_id=order_id).all()
        
        for item in order_items:
            product = db.session.query(Product).get(item.product_id)
            if not product or product.stock < 1:
                continue
            
            # Check if already in cart
            existing = db.session.query(CartItem).filter_by(
                user_id=user_id,
                product_id=item.product_id
            ).first()
            
            if existing:
                existing.quantity += item.quantity
            else:
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=product.price,
                    size=item.size,
                    color=item.color
                )
                db.session.add(cart_item)
        
        db.session.commit()
        flash(f'Items from order #{original_order.order_number} added to cart', 'success')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Items added to cart'})
        else:
            return redirect(url_for('cart.view_cart'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error reordering: {str(e)}', 'error')
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)}), 400
        else:
            return redirect(url_for('order.order_detail', order_id=order_id))

# ============ EXPORT ORDER HISTORY ============
@order_bp.route('/export/csv', methods=['GET'])
def export_order_history_csv():
    """Export order history as CSV"""
    from app import db
    from io import StringIO
    import csv
    from flask import send_file
    from io import BytesIO
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    
    orders = db.session.query(Order).filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Order Number', 'Order Date', 'Total Amount', 'Status', 'Payment Status'])
    
    for order in orders:
        writer.writerow([
            order.id,
            order.order_number,
            order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else '',
            order.grand_total,
            order.status,
            order.payment_status
        ])
    
    # Convert to bytes
    csv_bytes = BytesIO(output.getvalue().encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'order_history_{user_id}.csv'
    )

# ============ GET ORDER DETAILS (API) ============
@order_bp.route('/api/<int:order_id>', methods=['GET'])
def get_order_details_api(order_id):
    """Get order details as JSON (API endpoint)"""
    from app import db
    from flask import jsonify
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    Product = current_app.product_model_class
    Shipping = current_app.shipping_model_class
    Payment = current_app.payment_model_class
    
    order = db.session.query(Order).get(order_id)
    if not order or order.user_id != user_id:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    # Get order items
    items = db.session.query(OrderItem).filter_by(order_id=order_id).all()
    items_data = []
    for item in items:
        product = db.session.query(Product).get(item.product_id)
        items_data.append({
            'product_id': item.product_id,
            'product_name': item.product_name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'total': item.total,
            'size': item.size,
            'color': item.color
        })
    
    # Get shipping info
    shipping = db.session.query(Shipping).filter_by(order_id=order_id).first()
    shipping_data = {
        'tracking_number': shipping.tracking_number,
        'carrier': shipping.carrier,
        'shipping_status': shipping.shipping_status,
        'estimated_delivery': shipping.estimated_delivery.strftime('%Y-%m-%d') if shipping.estimated_delivery else None
    } if shipping else None
    
    # Get payment info
    payment = db.session.query(Payment).filter_by(order_id=order_id).first()
    payment_data = {
        'payment_method': payment.payment_method,
        'transaction_id': payment.transaction_id,
        'payment_status': payment.payment_status
    } if payment else None
    
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'order_number': order.order_number,
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else None,
            'status': order.status,
            'subtotal': order.subtotal,
            'tax': order.tax,
            'shipping_cost': order.shipping_cost,
            'grand_total': order.grand_total,
            'items': items_data,
            'shipping': shipping_data,
            'payment': payment_data
        }
    })
