"""
Checkout & Order Routes
Handle checkout process and order management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime
import uuid

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

# ============ CHECKOUT PAGE ============
@checkout_bp.route('/', methods=['GET'])
def checkout():
    """Checkout page with address and payment options"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    CartItem = current_app.cart_item_model_class
    Address = current_app.address_model_class
    Coupon = current_app.coupon_model_class
    Product = current_app.product_model_class
    
    # Get cart items
    cart_items = db.session.query(CartItem).filter_by(user_id=user_id).all()
    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    # Calculate totals
    subtotal = 0
    items_data = []
    for item in cart_items:
        product = db.session.query(Product).get(item.product_id)
        if product:
            item_total = item.price * item.quantity
            subtotal += item_total
            items_data.append({
                'product_id': item.product_id,
                'product_name': product.product_name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item_total
            })
    
    # Get user's addresses
    addresses = db.session.query(Address).filter_by(user_id=user_id).all()
    
    # Calculate taxes and shipping
    tax_rate = 0.10  # 10% tax
    tax_amount = subtotal * tax_rate
    shipping_cost = 10.00  # Fixed shipping for now
    grand_total = subtotal + tax_amount + shipping_cost
    
    return render_template('checkout.html',
                          items=items_data,
                          subtotal=round(subtotal, 2),
                          tax_amount=round(tax_amount, 2),
                          shipping_cost=round(shipping_cost, 2),
                          grand_total=round(grand_total, 2),
                          addresses=addresses)

# ============ PROCESS CHECKOUT ============
@checkout_bp.route('/process', methods=['POST'])
def process_checkout():
    """Process checkout and create order"""
    from app import db, current_app
    
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    CartItem = current_app.cart_item_model_class
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    Product = current_app.product_model_class
    User = current_app.user_model_class
    Payment = current_app.payment_model_class
    
    # Get form data
    customer_name = request.form.get('customer_name')
    customer_email = request.form.get('customer_email')
    customer_phone = request.form.get('customer_phone')
    shipping_address = request.form.get('shipping_address')
    billing_address = request.form.get('billing_address') or shipping_address
    shipping_method = request.form.get('shipping_method', 'standard')
    payment_method = request.form.get('payment_method', 'credit_card')
    coupon_code = request.form.get('coupon_code')
    
    # Get cart
    cart_items = db.session.query(CartItem).filter_by(user_id=user_id).all()
    if not cart_items:
        flash('Cart is empty', 'error')
        return redirect(url_for('cart.view_cart'))
    
    try:
        # Calculate totals
        subtotal = 0
        discount_amount = 0
        
        for item in cart_items:
            product = db.session.query(Product).get(item.product_id)
            if not product or product.stock < item.quantity:
                flash(f'Insufficient stock for {product.product_name}', 'error')
                return redirect(url_for('checkout.checkout'))
            subtotal += item.price * item.quantity
        
        # Apply coupon if provided
        if coupon_code:
            from datetime import datetime
            Coupon = current_app.coupon_model_class
            coupon = db.session.query(Coupon).filter_by(code=coupon_code.upper(), is_active=True).first()
            if coupon and coupon.end_date >= datetime.utcnow():
                if coupon.discount_percentage:
                    discount_amount = (subtotal * coupon.discount_percentage) / 100
                else:
                    discount_amount = coupon.discount_amount
        
        # Calculate final total
        tax_rate = 0.10
        tax_amount = (subtotal - discount_amount) * tax_rate
        shipping_cost = 10.00
        grand_total = subtotal - discount_amount + tax_amount + shipping_cost
        
        # Create order
        order_number = f"ORD-{str(uuid.uuid4())[:8].upper()}"
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
            billing_address=billing_address,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            payment_method=payment_method,
            status='pending',
            payment_status='pending',
            order_date=datetime.utcnow()
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items from cart
        for cart_item in cart_items:
            product = db.session.query(Product).get(cart_item.product_id)
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=product.product_name,
                quantity=cart_item.quantity,
                unit_price=cart_item.price,
                total=cart_item.price * cart_item.quantity,
                size=cart_item.size,
                color=cart_item.color
            )
            db.session.add(order_item)
            
            # Reduce stock
            product.stock -= cart_item.quantity
        
        # Create payment record
        payment = Payment(
            order_id=order.id,
            amount=grand_total,
            payment_method=payment_method,
            payment_status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        
        # Clear cart
        db.session.query(CartItem).filter_by(user_id=user_id).delete()
        
        db.session.commit()
        
        flash('Order created successfully!', 'success')
        return redirect(url_for('order.order_detail', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating order: {str(e)}', 'error')
        return redirect(url_for('checkout.checkout'))
