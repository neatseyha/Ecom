from datetime import datetime
from sqlalchemy import func


def init_rating_model(db):
    """Initialize Rating model"""

    class Rating(db.Model):
        __tablename__ = 'rating'
        
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
        rating = db.Column(db.Float, nullable=False)  # 1-5 stars
        review_title = db.Column(db.String(200), nullable=True)
        review = db.Column(db.Text)  # Optional review text
        
        # Voting system
        helpful_yes_count = db.Column(db.Integer, default=0)
        helpful_no_count = db.Column(db.Integer, default=0)
        helpful_count = db.Column(db.Integer, default=0)  # For backward compatibility
        
        # Review media
        images = db.Column(db.String(500), nullable=True)  # Comma-separated paths
        
        # Moderation
        status = db.Column(db.String(50), default='approved')  # approved, pending, rejected
        verified_purchase = db.Column(db.Boolean, default=False)
        
        # Seller response
        is_seller_response = db.Column(db.Boolean, default=False)
        seller_response = db.Column(db.Text, nullable=True)
        seller_response_date = db.Column(db.DateTime, nullable=True)
        
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())
        
        def to_dict(self):
            return {
                'id': self.id,
                'user_id': self.user_id,
                'product_id': self.product_id,
                'rating': self.rating,
                'review_title': self.review_title,
                'review': self.review,
                'helpful_yes_count': self.helpful_yes_count,
                'helpful_no_count': self.helpful_no_count,
                'images': self.images,
                'status': self.status,
                'verified_purchase': self.verified_purchase,
                'is_seller_response': self.is_seller_response,
                'seller_response': self.seller_response,
                'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
                'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
            }
        
        def __repr__(self):
            return f'<Rating {self.rating}★ for Product {self.product_id}>'

    return Rating
