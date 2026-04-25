from datetime import datetime
from sqlalchemy import func


def init_coupon_model(db):
    """Initialize Coupon model - for promotional codes and discounts"""

    class Coupon(db.Model):
        __tablename__ = 'coupon'

        id = db.Column(db.Integer, primary_key=True)
        code = db.Column(db.String(50), unique=True, nullable=False)
        discount_percentage = db.Column(db.Float, nullable=True)
        discount_amount = db.Column(db.Float, nullable=True)
        max_uses = db.Column(db.Integer, nullable=True)
        used_count = db.Column(db.Integer, default=0)
        min_purchase = db.Column(db.Float, nullable=True)
        applicable_categories = db.Column(db.String(500), nullable=True)  # JSON or comma-separated
        start_date = db.Column(db.DateTime, nullable=False)
        end_date = db.Column(db.DateTime, nullable=False)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        def __repr__(self):
            return f'<Coupon {self.code}>'

    return Coupon
