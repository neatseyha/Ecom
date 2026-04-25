from model.product import init_product_model
from model.category import init_category_model
from model.user import init_user_model
from model.order import init_order_model
from model.wishlist import init_wishlist_model
from model.rating import init_rating_model
from model.cart_item import init_cart_item_model
from model.order_item import init_order_item_model
from model.payment import init_payment_model
from model.address import init_address_model
from model.shipping import init_shipping_model
from model.coupon import init_coupon_model
from model.brand import init_brand_model


def init_models(db):
    """Initialize all models"""
    Product = init_product_model(db)
    Category = init_category_model(db)
    User = init_user_model(db)
    Order = init_order_model(db)
    Wishlist = init_wishlist_model(db)
    Rating = init_rating_model(db)
    CartItem = init_cart_item_model(db)
    OrderItem = init_order_item_model(db)
    Payment = init_payment_model(db)
    Address = init_address_model(db)
    Shipping = init_shipping_model(db)
    Coupon = init_coupon_model(db)
    Brand = init_brand_model(db)
    return Product, Category, User, Order, Wishlist, Rating, CartItem, OrderItem, Payment, Address, Shipping, Coupon, Brand


__all__ = [
    'init_models',
    'init_product_model',
    'init_category_model',
    'init_user_model',
    'init_order_model',
    'init_wishlist_model',
    'init_rating_model',
    'init_cart_item_model',
    'init_order_item_model',
    'init_payment_model',
    'init_address_model',
    'init_shipping_model',
    'init_coupon_model',
    'init_brand_model'
]