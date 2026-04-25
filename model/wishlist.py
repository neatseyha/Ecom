from datetime import datetime
from sqlalchemy import func


def init_wishlist_model(db):
    """Initialize Wishlist model"""

    class Wishlist(db.Model):
        __tablename__ = 'wishlist'

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
        
        # Denormalized fields for performance
        product_name = db.Column(db.String(255), nullable=False)
        product_price = db.Column(db.Float, nullable=False)
        product_image = db.Column(db.String(500), nullable=True)
        
        priority = db.Column(db.String(20), default='medium')  # high, medium, low
        notes = db.Column(db.String(500), nullable=True)
        category_type = db.Column(db.String(50), default='favorites')  # favorites, watch-later, gift-ideas
        is_price_watch_enabled = db.Column(db.Boolean, default=False)
        target_price = db.Column(db.Float, nullable=True)
        
        added_date = db.Column(db.DateTime, nullable=False, server_default=func.now())

        # Relationships
        user = db.relationship('User', backref='wishlists', lazy=True)
        product = db.relationship('Product', backref='wishlists', lazy=True)

        def __repr__(self):
            return f'<Wishlist {self.user_id} - {self.product_id}>'

    return Wishlist
