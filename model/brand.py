from datetime import datetime
from sqlalchemy import func


def init_brand_model(db):
    """Initialize Brand model - for product brands/manufacturers"""

    class Brand(db.Model):
        __tablename__ = 'brand'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), unique=True, nullable=False)
        slug = db.Column(db.String(100), unique=True, nullable=False)
        description = db.Column(db.String(500), nullable=True)
        logo = db.Column(db.String(120), nullable=True)
        website = db.Column(db.String(200), nullable=True)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
        updated_at = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

        def __repr__(self):
            return f'<Brand {self.name}>'

    return Brand
