from datetime import datetime
from sqlalchemy import func


def init_shipping_model(db):
    """Initialize Shipping model - for tracking shipments"""

    class Shipping(db.Model):
        __tablename__ = 'shipping'

        id = db.Column(db.Integer, primary_key=True)
        order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
        tracking_number = db.Column(db.String(100), nullable=True)
        carrier = db.Column(db.String(50), nullable=True)  # FedEx, UPS, DHL, etc
        status = db.Column(db.String(50), default='pending')  # pending, in_transit, delivered, failed
        shipped_date = db.Column(db.DateTime, nullable=True)
        delivered_date = db.Column(db.DateTime, nullable=True)
        estimated_delivery = db.Column(db.DateTime, nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        # Relationships
        order = db.relationship('Order', backref='shipping', uselist=False, lazy=True)

        def __repr__(self):
            return f'<Shipping Order {self.order_id} - {self.status}>'

    return Shipping
