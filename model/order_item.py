from datetime import datetime
from sqlalchemy import func


def init_order_item_model(db):
    """Initialize OrderItem model - for multiple items per order"""

    class OrderItem(db.Model):
        __tablename__ = 'order_item'

        id = db.Column(db.Integer, primary_key=True)
        order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
        product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
        product_name = db.Column(db.String(255), nullable=False)
        quantity = db.Column(db.Integer, nullable=False)
        unit_price = db.Column(db.Float, nullable=False)
        discount = db.Column(db.Float, default=0)
        total = db.Column(db.Float, nullable=False)
        size = db.Column(db.String(50), nullable=True)
        color = db.Column(db.String(100), nullable=True)

        # Relationships
        order = db.relationship('Order', backref='order_items', lazy=True)
        product = db.relationship('Product', backref='order_items', lazy=True)

        def __repr__(self):
            return f'<OrderItem Order {self.order_id} - Product {self.product_id}>'

    return OrderItem
