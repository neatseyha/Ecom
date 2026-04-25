from datetime import datetime
from sqlalchemy import func


def init_product_model(db):
    """Initialize Product model"""
    
    class Product(db.Model):
        __tablename__ = 'product'
        
        id = db.Column(db.Integer, primary_key=True)
        product_name = db.Column(db.String(80), unique=True, nullable=False)
        sku = db.Column(db.String(50), unique=True, nullable=True)  # Stock Keeping Unit
        brand = db.Column(db.String(80), nullable=True)
        color = db.Column(db.String(100), nullable=True)
        size = db.Column(db.String(100), nullable=True)
        price = db.Column(db.Float, nullable=False)
        discount_percentage = db.Column(db.Float, default=0)
        discount_price = db.Column(db.Float, nullable=True)
        stock = db.Column(db.Integer, nullable=False)
        category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
        image = db.Column(db.String(120), nullable=True)
        image_medium = db.Column(db.String(120), nullable=True)  # 400x400
        image_small = db.Column(db.String(120), nullable=True)   # 200x200
        description = db.Column(db.String(500), nullable=True)
        weight = db.Column(db.Float, nullable=True)
        dimensions = db.Column(db.String(100), nullable=True)
        rating_avg = db.Column(db.Float, default=0)
        review_count = db.Column(db.Integer, default=0)
        is_featured = db.Column(db.Boolean, default=False)
        is_new = db.Column(db.Boolean, default=False)
        view_count = db.Column(db.Integer, default=0)
        status = db.Column(db.String(20), nullable=False, default='instock')
        meta_description = db.Column(db.String(160), nullable=True)
        meta_keywords = db.Column(db.String(200), nullable=True)
        create_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        update_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        # Relationship to Category
        category = db.relationship('Category', backref='products', lazy=True)

        def __repr__(self):
            return f'<Product {self.product_name}>'
    
    return Product