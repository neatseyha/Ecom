from datetime import datetime
from sqlalchemy import func


def init_address_model(db):
    """Initialize Address model - for multiple addresses per user"""

    class Address(db.Model):
        __tablename__ = 'address'

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        type = db.Column(db.String(50), default='shipping')  # shipping or billing
        full_name = db.Column(db.String(120), nullable=False)
        phone = db.Column(db.String(20), nullable=False)
        street_address = db.Column(db.String(255), nullable=False)
        city = db.Column(db.String(50), nullable=False)
        state = db.Column(db.String(50), nullable=True)
        zip_code = db.Column(db.String(20), nullable=False)
        country = db.Column(db.String(50), nullable=False)
        is_default = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

        # Relationships
        user = db.relationship('User', backref='addresses', lazy=True)

        def __repr__(self):
            return f'<Address {self.type} - {self.full_name}>'

    return Address
