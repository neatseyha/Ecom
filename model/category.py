from datetime import datetime
from sqlalchemy import func


def init_category_model(db):
    """Initialize Category model"""
    
    class Category(db.Model):
        __tablename__ = 'category'
        
        id = db.Column(db.Integer, primary_key=True)
        category_name = db.Column(db.String(80), unique=True, nullable=False)
        slug = db.Column(db.String(100), unique=True, nullable=True)
        description = db.Column(db.String(500), nullable=True)
        parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)  # For subcategories
        icon = db.Column(db.String(100), nullable=True)
        image = db.Column(db.String(120), nullable=True)
        display_order = db.Column(db.Integer, default=0)
        status = db.Column(db.String(20), default='active')
        meta_description = db.Column(db.String(160), nullable=True)
        meta_keywords = db.Column(db.String(200), nullable=True)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())

        # Self-referential relationship for subcategories
        parent = db.relationship('Category', remote_side=[id], backref='subcategories', lazy=True)

        def __repr__(self):
            return f'<Category {self.category_name}>'
    
    return Category