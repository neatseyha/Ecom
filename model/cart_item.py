from datetime import datetime
from sqlalchemy import func


def init_cart_item_model(db):
    """Initialize CartItem model"""

    class CartItem(db.Model):
        __tablename__ = 'cart_item'

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
        quantity = db.Column(db.Integer, nullable=False, default=1)
        price = db.Column(db.Float, nullable=False)  # Price at time of adding
        size = db.Column(db.String(50), nullable=True)  # Selected size
        color = db.Column(db.String(100), nullable=True)  # Selected color
        added_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

        # Relationships
        user = db.relationship('User', backref='cart_items', lazy=True)
        product = db.relationship('Product', backref='cart_items', lazy=True)

        def __repr__(self):
            return f'<CartItem User {self.user_id} - Product {self.product_id}>'

    return CartItem
