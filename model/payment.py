from datetime import datetime
from sqlalchemy import func


def init_payment_model(db):
    """Initialize Payment model - for payment tracking"""

    class Payment(db.Model):
        __tablename__ = 'payment'

        id = db.Column(db.Integer, primary_key=True)
        order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False, unique=True)
        amount = db.Column(db.Float, nullable=False)
        payment_method = db.Column(db.String(50), nullable=False)  # card, bank transfer, cash, etc
        payment_status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded
        transaction_id = db.Column(db.String(100), nullable=True)
        gateway_response = db.Column(db.Text, nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        # Relationships
        order = db.relationship('Order', backref='payment', uselist=False, lazy=True)

        def __repr__(self):
            return f'<Payment Order {self.order_id} - {self.payment_status}>'

    return Payment
