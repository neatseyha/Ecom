from datetime import datetime
from sqlalchemy import func


def init_order_model(db):
    """Initialize Order model"""

    class Order(db.Model):
        __tablename__ = 'order'

        id = db.Column(db.Integer, primary_key=True)
        order_number = db.Column(db.String(20), unique=True, nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

        # Legacy single-item columns retained for compatibility with existing SQLite schema.
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
        product_name = db.Column(db.String(255), nullable=True)
        quantity = db.Column(db.Integer, nullable=True)
        price = db.Column(db.Float, nullable=True)
        total_price = db.Column(db.Float, nullable=True)
        
        # Pricing fields
        subtotal = db.Column(db.Float, nullable=False, default=0)
        discount_amount = db.Column(db.Float, nullable=False, default=0)
        tax_amount = db.Column(db.Float, nullable=False, default=0)
        shipping_cost = db.Column(db.Float, nullable=False, default=0)
        grand_total = db.Column(db.Float, nullable=False)
        
        # Customer information
        customer_name = db.Column(db.String(120), nullable=False)
        customer_email = db.Column(db.String(120), nullable=False)
        customer_phone = db.Column(db.String(20), nullable=True)
        
        # Addresses
        billing_address = db.Column(db.String(500), nullable=True)
        shipping_address = db.Column(db.String(500), nullable=True)
        
        # Shipping
        shipping_method = db.Column(db.String(50), nullable=True)
        tracking_number = db.Column(db.String(100), nullable=True)
        
        # Payment
        payment_method = db.Column(db.String(50), nullable=True)
        payment_status = db.Column(db.String(50), default='pending')
        
        # Status tracking
        status = db.Column(db.String(50), nullable=False, default='pending')
        estimated_delivery = db.Column(db.DateTime, nullable=True)
        delivery_date = db.Column(db.DateTime, nullable=True)
        
        # Cancellation & Refunds
        cancel_reason = db.Column(db.String(500), nullable=True)
        refund_status = db.Column(db.String(50), default='none')
        refund_amount = db.Column(db.Float, nullable=True)
        
        # Additional info
        currency = db.Column(db.String(3), default='USD')
        notes = db.Column(db.Text, nullable=True)
        order_date = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        def __repr__(self):
            return f'<Order {self.order_number}>'

    return Order
