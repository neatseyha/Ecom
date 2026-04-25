"""
Order Management API Routes
Endpoints for Order and OrderItem operations
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from decimal import Decimal

# Create Blueprint
order_bp = Blueprint('api_order', __name__, url_prefix='/api/order')

def get_db():
    """Get database session"""
    return current_app.extensions['sqlalchemy'].session

def get_models():
    """Get model classes from app context"""
    return {
        'Order': current_app.order_model_class,
        'OrderItem': current_app.order_item_model_class,
        'CartItem': current_app.cart_item_model_class,
        'Product': current_app.product_model_class,
        'User': current_app.user_model_class,
    }

# ============ CREATE ORDER FROM CART ============
@order_bp.route('/create', methods=['POST'])
def create_order():
    """Create order from cart"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        order_number = data.get('order_number')
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        customer_phone = data.get('customer_phone')
        shipping_address = data.get('shipping_address')
        billing_address = data.get('billing_address')
        shipping_method = data.get('shipping_method')
        payment_method = data.get('payment_method')
        coupon_id = data.get('coupon_id')
        notes = data.get('notes')

        if not all([user_id, customer_name, customer_email, shipping_address]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        models = get_models()
        Order = models['Order']
        OrderItem = models['OrderItem']
        CartItem = models['CartItem']
        Product = models['Product']
        User = models['User']
        db = get_db()

        # Verify user exists
        user = db.query(User).get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get cart items
        cart_items = db.query(CartItem).filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty'}), 400

        # Calculate totals
        subtotal = 0
        discount_amount = 0
        tax_percentage = 0.10  # 10% tax (configurable)

        for item in cart_items:
            product = db.query(Product).get(item.product_id)
            if not product:
                return jsonify({'success': False, 'message': f'Product {item.product_id} not found'}), 404
            
            item_total = item.price * item.quantity
            subtotal += item_total

            # Check stock
            if product.stock < item.quantity:
                return jsonify({
                    'success': False,
                    'message': f'Insufficient stock for {product.product_name}'
                }), 400

        # Apply coupon if provided
        if coupon_id:
            from routes.api_coupon import get_db as coupon_get_db, get_models as coupon_get_models
            Coupon = coupon_get_models()['Coupon']
            coupon = db.query(Coupon).get(coupon_id)
            if coupon:
                if coupon.discount_percentage:
                    discount_amount = (subtotal * coupon.discount_percentage) / 100
                else:
                    discount_amount = coupon.discount_amount

        tax_amount = (subtotal - discount_amount) * tax_percentage
        shipping_cost = data.get('shipping_cost', 0)
        grand_total = subtotal - discount_amount + tax_amount + shipping_cost

        # Create order
        order = Order(
            order_number=order_number,
            user_id=user_id,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            grand_total=grand_total,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            billing_address=billing_address or shipping_address,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            payment_method=payment_method,
            status='pending',
            payment_status='pending',
            order_date=datetime.utcnow(),
            notes=notes
        )
        db.add(order)
        db.flush()  # Get the order ID

        # Create order items from cart
        for cart_item in cart_items:
            product = db.query(Product).get(cart_item.product_id)
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=product.product_name,
                quantity=cart_item.quantity,
                unit_price=cart_item.price,
                discount=0,
                total=cart_item.price * cart_item.quantity,
                size=cart_item.size,
                color=cart_item.color
            )
            db.add(order_item)

            # Reduce product stock
            product.stock -= cart_item.quantity

        # Clear cart
        db.query(CartItem).filter_by(user_id=user_id).delete()

        db.commit()

        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'order_id': order.id,
            'order_number': order.order_number,
            'grand_total': order.grand_total
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ GET ORDER ============
@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order details with items"""
    try:
        models = get_models()
        Order = models['Order']
        OrderItem = models['OrderItem']
        Product = models['Product']
        db = get_db()

        order = db.query(Order).get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        # Get order items
        order_items = db.query(OrderItem).filter_by(order_id=order_id).all()
        items = []
        for item in order_items:
            product = db.query(Product).get(item.product_id)
            items.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total': item.total,
                'size': item.size,
                'color': item.color,
                'image': product.image if product else None
            })

        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'user_id': order.user_id,
                'subtotal': order.subtotal,
                'discount_amount': order.discount_amount,
                'tax_amount': order.tax_amount,
                'shipping_cost': order.shipping_cost,
                'grand_total': order.grand_total,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'status': order.status,
                'payment_status': order.payment_status,
                'shipping_method': order.shipping_method,
                'shipping_address': order.shipping_address,
                'tracking_number': order.tracking_number,
                'order_date': order.order_date.isoformat(),
                'estimated_delivery': order.estimated_delivery.isoformat() if order.estimated_delivery else None,
                'items': items,
                'item_count': len(items)
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ GET USER ORDERS ============
@order_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_orders(user_id):
    """Get all orders for a user"""
    try:
        models = get_models()
        Order = models['Order']
        db = get_db()

        orders = db.query(Order).filter_by(user_id=user_id).order_by(Order.order_date.desc()).all()

        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'grand_total': order.grand_total,
                'status': order.status,
                'payment_status': order.payment_status,
                'order_date': order.order_date.isoformat(),
                'tracking_number': order.tracking_number
            })

        return jsonify({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ UPDATE ORDER STATUS ============
@order_bp.route('/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.get_json()
        status = data.get('status')  # pending, confirmed, shipped, delivered, cancelled

        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status'}), 400

        models = get_models()
        Order = models['Order']
        db = get_db()

        order = db.query(Order).get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        order.status = status
        order.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Order status updated',
            'status': status
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ CANCEL ORDER ============
@order_bp.route('/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    """Cancel an order"""
    try:
        data = request.get_json()
        cancel_reason = data.get('cancel_reason', '')

        models = get_models()
        Order = models['Order']
        OrderItem = models['OrderItem']
        Product = models['Product']
        db = get_db()

        order = db.query(Order).get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        if order.status == 'cancelled':
            return jsonify({'success': False, 'message': 'Order is already cancelled'}), 400

        # Restore product stock
        order_items = db.query(OrderItem).filter_by(order_id=order_id).all()
        for item in order_items:
            product = db.query(Product).get(item.product_id)
            if product:
                product.stock += item.quantity

        order.status = 'cancelled'
        order.cancel_reason = cancel_reason
        order.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Order cancelled successfully'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ GET ORDER ITEMS ============
@order_bp.route('/<int:order_id>/items', methods=['GET'])
def get_order_items(order_id):
    """Get items in an order"""
    try:
        models = get_models()
        OrderItem = models['OrderItem']
        Product = models['Product']
        db = get_db()

        items = db.query(OrderItem).filter_by(order_id=order_id).all()

        items_data = []
        for item in items:
            product = db.query(Product).get(item.product_id)
            items_data.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'discount': item.discount,
                'total': item.total,
                'size': item.size,
                'color': item.color,
                'image': product.image if product else None
            })

        return jsonify({
            'success': True,
            'items': items_data,
            'count': len(items_data)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
