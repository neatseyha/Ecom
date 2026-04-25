"""
Product Recommendations Engine Routes
Generate personalized product recommendations
"""

from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, desc

recommend_bp = Blueprint('recommend', __name__, url_prefix='/recommend')

# ============ GET PERSONALIZED RECOMMENDATIONS ============
@recommend_bp.route('/personalized', methods=['GET'])
def get_personalized_recommendations():
    """Get recommendations based on user's purchase and browsing history"""
    from app import db
    
    user_id = session.get('user_id')
    limit = request.args.get('limit', 10, type=int)
    
    Product = current_app.product_model_class
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    
    recommendations = []
    
    if user_id:
        # Get categories from user's past purchases
        user_orders = db.session.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(Order.user_id == user_id).all()
        
        purchased_category_ids = set([item.product_id for item in user_orders])
        
        # Get products from similar categories
        similar_products = db.session.query(Product).filter(
            ~Product.id.in_(purchased_category_ids),
            Product.stock > 0
        ).order_by(desc(Product.rating_avg)).limit(limit).all()
        
        recommendations = [product_to_dict(p) for p in similar_products]
    else:
        # For non-logged-in users, return trending products
        trending = db.session.query(Product).filter(
            Product.stock > 0
        ).order_by(desc(Product.view_count)).limit(limit).all()
        
        recommendations = [product_to_dict(p) for p in trending]
    
    return jsonify({
        'success': True,
        'type': 'personalized',
        'total': len(recommendations),
        'products': recommendations
    })

# ============ GET TRENDING PRODUCTS ============
@recommend_bp.route('/trending', methods=['GET'])
def get_trending_products():
    """Get trending products by view count and sales"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    time_period = request.args.get('period', '30d')  # 7d, 30d, 90d, all
    
    Product = current_app.product_model_class
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    
    # Determine date range
    if time_period == '7d':
        date_from = datetime.utcnow() - timedelta(days=7)
    elif time_period == '90d':
        date_from = datetime.utcnow() - timedelta(days=90)
    elif time_period == '30d':
        date_from = datetime.utcnow() - timedelta(days=30)
    else:
        date_from = datetime.utcnow() - timedelta(days=365)
    
    # Get products with sales in period
    sales_subquery = db.session.query(
        OrderItem.product_id,
        func.count(OrderItem.id).label('sales_count')
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.order_date >= date_from
    ).group_by(OrderItem.product_id).subquery()
    
    trending = db.session.query(Product).outerjoin(
        sales_subquery, Product.id == sales_subquery.c.product_id
    ).filter(
        Product.stock > 0
    ).order_by(
        desc(func.coalesce(sales_subquery.c.sales_count, 0)),
        desc(Product.view_count)
    ).limit(limit).all()
    
    products = []
    for product in trending:
        prod_dict = product_to_dict(product)
        # Get sales count for this product in period
        sales = db.session.query(func.count(OrderItem.id)).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product.id,
            Order.order_date >= date_from
        ).scalar() or 0
        prod_dict['sales_in_period'] = sales
        products.append(prod_dict)
    
    return jsonify({
        'success': True,
        'type': 'trending',
        'period': time_period,
        'total': len(products),
        'products': products
    })

# ============ GET SIMILAR PRODUCTS ============
@recommend_bp.route('/similar/<int:product_id>', methods=['GET'])
def get_similar_products(product_id):
    """Get products similar to the specified product"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    
    Product = current_app.product_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Get products from same category with similar price range
    similar = db.session.query(Product).filter(
        Product.id != product_id,
        Product.category_id == product.category_id,
        Product.stock > 0,
        Product.price >= product.price * 0.7,  # 70% to 130% of original price
        Product.price <= product.price * 1.3
    ).order_by(
        desc(Product.rating_avg)
    ).limit(limit).all()
    
    # If not enough, get products from same category
    if len(similar) < limit:
        additional = db.session.query(Product).filter(
            Product.id != product_id,
            Product.category_id == product.category_id,
            Product.stock > 0,
            ~Product.id.in_([p.id for p in similar])
        ).order_by(
            desc(Product.rating_avg)
        ).limit(limit - len(similar)).all()
        similar.extend(additional)
    
    products = [product_to_dict(p) for p in similar]
    
    return jsonify({
        'success': True,
        'type': 'similar',
        'reference_product': product_to_dict(product),
        'total': len(products),
        'products': products
    })

# ============ GET FEATURED PRODUCTS ============
@recommend_bp.route('/featured', methods=['GET'])
def get_featured_products():
    """Get featured products"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    
    Product = current_app.product_model_class
    
    featured = db.session.query(Product).filter(
        Product.is_featured == True,
        Product.stock > 0
    ).order_by(desc(Product.rating_avg)).limit(limit).all()
    
    products = [product_to_dict(p) for p in featured]
    
    return jsonify({
        'success': True,
        'type': 'featured',
        'total': len(products),
        'products': products
    })

# ============ GET NEW ARRIVALS ============
@recommend_bp.route('/new-arrivals', methods=['GET'])
def get_new_arrivals():
    """Get newest products added to store"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    days = request.args.get('days', 30, type=int)
    
    Product = current_app.product_model_class
    
    date_from = datetime.utcnow() - timedelta(days=days)
    
    new_products = db.session.query(Product).filter(
        Product.is_new == True,
        Product.stock > 0,
        Product.create_at >= date_from
    ).order_by(desc(Product.create_at)).limit(limit).all()
    
    products = [product_to_dict(p) for p in new_products]
    
    return jsonify({
        'success': True,
        'type': 'new_arrivals',
        'total': len(products),
        'products': products
    })

# ============ GET ON-SALE PRODUCTS ============
@recommend_bp.route('/on-sale', methods=['GET'])
def get_on_sale_products():
    """Get products currently on sale"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    
    Product = current_app.product_model_class
    
    on_sale = db.session.query(Product).filter(
        Product.discount_percentage > 0,
        Product.stock > 0
    ).order_by(
        desc(Product.discount_percentage)
    ).limit(limit).all()
    
    products = []
    for product in on_sale:
        prod_dict = product_to_dict(product)
        prod_dict['discount_percentage'] = product.discount_percentage
        prod_dict['discounted_price'] = product.discount_price or (product.price * (1 - product.discount_percentage / 100))
        products.append(prod_dict)
    
    return jsonify({
        'success': True,
        'type': 'on_sale',
        'total': len(products),
        'products': products
    })

# ============ GET TOP-RATED PRODUCTS ============
@recommend_bp.route('/top-rated', methods=['GET'])
def get_top_rated_products():
    """Get highest rated products"""
    from app import db
    
    limit = request.args.get('limit', 10, type=int)
    min_reviews = request.args.get('min_reviews', 5, type=int)
    
    Product = current_app.product_model_class
    
    top_rated = db.session.query(Product).filter(
        Product.rating_avg > 0,
        Product.review_count >= min_reviews,
        Product.stock > 0
    ).order_by(desc(Product.rating_avg)).limit(limit).all()
    
    products = [product_to_dict(p) for p in top_rated]
    
    return jsonify({
        'success': True,
        'type': 'top_rated',
        'min_reviews': min_reviews,
        'total': len(products),
        'products': products
    })

# ============ HELPER FUNCTION ============
def product_to_dict(p):
    """Convert product object to dictionary"""
    from flask import url_for
    
    image_url = p.image
    if image_url and not image_url.startswith('http'):
        image_url = url_for('static', filename='upload/' + image_url)
    elif not image_url:
        image_url = 'https://via.placeholder.com/400x500?text=No+Image'
    
    return {
        'id': p.id,
        'name': p.product_name,
        'price': float(p.price),
        'image': image_url,
        'description': p.description or 'No description available.',
        'stock': p.stock,
        'rating': p.rating_avg,
        'review_count': p.review_count,
        'is_featured': p.is_featured,
        'is_new': p.is_new
    }
