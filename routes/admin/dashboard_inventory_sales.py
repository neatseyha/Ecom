"""
Inventory Management & Sales Performance Analytics
Detailed insights for products and sales
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func, desc

inventory_sales_bp = Blueprint('inventory_sales', __name__, url_prefix='/api/inventory')

# ============ TOP SELLING PRODUCTS ============
def get_top_selling_products(limit=10, period='month'):
    """Get top-selling products by quantity"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    OrderItem = current_app.order_item_model_class
    Order = current_app.order_model_class
    
    if period == 'week':
        date_from = datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        date_from = datetime.utcnow() - timedelta(days=30)
    else:
        date_from = datetime.min
    
    try:
        top_products = db.session.query(
            Product.id,
            Product.product_name,
            Product.price,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.total).label('total_revenue')
        ).join(
            OrderItem, Product.id == OrderItem.product_id
        ).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            Order.order_date >= date_from
        ).group_by(Product.id).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit).all()
        
        return [{
            'id': p.id,
            'name': p.product_name,
            'price': float(p.price),
            'quantity_sold': p.total_quantity or 0,
            'revenue': float(p.total_revenue or 0)
        } for p in top_products]
    except Exception as e:
        print(f"Error getting top selling products: {e}")
        return []

# ============ SLOW MOVING PRODUCTS ============
def get_slow_moving_products(limit=10):
    """Get products with low sales velocity"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    OrderItem = current_app.order_item_model_class
    
    try:
        slow_movers = db.session.query(
            Product.id,
            Product.product_name,
            func.count(OrderItem.id).label('total_sales')
        ).outerjoin(
            OrderItem, Product.id == OrderItem.product_id
        ).group_by(Product.id).order_by(
            func.count(OrderItem.id).asc()
        ).limit(limit).all()
        
        return [{
            'id': p.id,
            'name': p.product_name,
            'total_sales': p.total_sales or 0,
            'severity': 'critical' if p.total_sales == 0 or p.total_sales is None else 'warning'
        } for p in slow_movers]
    except Exception as e:
        print(f"Error getting slow moving products: {e}")
        return []

# ============ REVENUE BY CATEGORY ============
def get_revenue_by_category():
    """Get revenue breakdown by product category"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Category = current_app.category_model_class
    Product = current_app.product_model_class
    OrderItem = current_app.order_item_model_class
    
    try:
        categories = db.session.query(
            Category.category_name,
            func.sum(OrderItem.total).label('total_revenue'),
            func.count(OrderItem.id).label('total_items')
        ).join(
            Product, Category.id == Product.category_id
        ).outerjoin(
            OrderItem, Product.id == OrderItem.product_id
        ).group_by(Category.id).all()
        
        return {
            'labels': [c.category_name for c in categories],
            'data': [float(c.total_revenue or 0) for c in categories],
            'items': [c.total_items or 0 for c in categories]
        }
    except Exception as e:
        print(f"Error getting revenue by category: {e}")
        return {'labels': [], 'data': [], 'items': []}

# ============ SALES BY PAYMENT METHOD ============
def get_sales_by_payment_method():
    """Get sales breakdown by payment method"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Payment = current_app.payment_model_class
    Order = current_app.order_model_class
    
    try:
        payment_methods = db.session.query(
            Payment.payment_method,
            func.count(Payment.id).label('transaction_count'),
            func.sum(Order.grand_total).label('total_amount')
        ).join(
            Order, Payment.order_id == Order.id
        ).group_by(Payment.payment_method).all()
        
        return {
            'labels': [p.payment_method or 'Unknown' for p in payment_methods],
            'count': [p.transaction_count for p in payment_methods],
            'revenue': [float(p.total_amount or 0) for p in payment_methods]
        }
    except Exception as e:
        print(f"Error getting sales by payment method: {e}")
        return {'labels': [], 'count': [], 'revenue': []}

# ============ HOURLY SALES TREND ============
def get_hourly_sales_trend(day_offset=0):
    """Get hourly sales trend for a specific day"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    try:
        target_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=day_offset)
        next_date = target_date + timedelta(days=1)
        
        hourly_sales = db.session.query(
            func.strftime('%H', Order.order_date).label('hour'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.grand_total).label('revenue')
        ).filter(
            Order.order_date >= target_date,
            Order.order_date < next_date
        ).group_by(func.strftime('%H', Order.order_date)).all()
        
        # Create full 24-hour array
        hours = {str(i).zfill(2): {'count': 0, 'revenue': 0} for i in range(24)}
        
        for sale in hourly_sales:
            if sale.hour:
                hours[sale.hour] = {
                    'count': sale.order_count,
                    'revenue': float(sale.revenue or 0)
                }
        
        return {
            'labels': [f'{i:02d}:00' for i in range(24)],
            'orders': [hours[f'{i:02d}']['count'] for i in range(24)],
            'revenue': [hours[f'{i:02d}']['revenue'] for i in range(24)]
        }
    except Exception as e:
        print(f"Error getting hourly sales: {e}")
        return {
            'labels': [f'{i:02d}:00' for i in range(24)],
            'orders': [0] * 24,
            'revenue': [0] * 24
        }

# ============ DAILY SALES TREND ============
def get_daily_sales_trend(days=30):
    """Get daily sales trend for last N days"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    try:
        date_from = datetime.utcnow() - timedelta(days=days)
        
        daily_sales = db.session.query(
            func.date(Order.order_date).label('date'),
            func.count(Order.id).label('order_count'),
            func.sum(Order.grand_total).label('revenue')
        ).filter(
            Order.order_date >= date_from
        ).group_by(func.date(Order.order_date)).order_by(
            func.date(Order.order_date).asc()
        ).all()
        
        return {
            'labels': [d.date.strftime('%m-%d') for d in daily_sales],
            'orders': [d.order_count for d in daily_sales],
            'revenue': [float(d.revenue or 0) for d in daily_sales]
        }
    except Exception as e:
        print(f"Error getting daily sales: {e}")
        return {'labels': [], 'orders': [], 'revenue': []}

# ============ API ENDPOINTS ============
@inventory_sales_bp.route('/top-products')
def top_products_api():
    """Get top selling products"""
    limit = request.args.get('limit', 10, type=int)
    period = request.args.get('period', 'month')
    data = get_top_selling_products(limit, period)
    
    return jsonify({
        'success': True,
        'total': len(data),
        'products': data
    })

@inventory_sales_bp.route('/slow-movers')
def slow_movers_api():
    """Get slow-moving products"""
    limit = request.args.get('limit', 10, type=int)
    data = get_slow_moving_products(limit)
    
    return jsonify({
        'success': True,
        'total': len(data),
        'products': data
    })

@inventory_sales_bp.route('/revenue-by-category')
def revenue_by_category_api():
    """Get revenue by category"""
    data = get_revenue_by_category()
    
    return jsonify({
        'success': True,
        'data': data
    })

@inventory_sales_bp.route('/payment-methods')
def payment_methods_api():
    """Get sales by payment method"""
    data = get_sales_by_payment_method()
    
    return jsonify({
        'success': True,
        'data': data
    })

@inventory_sales_bp.route('/hourly-trend')
def hourly_trend_api():
    """Get hourly sales trend"""
    day_offset = request.args.get('day_offset', 0, type=int)
    data = get_hourly_sales_trend(day_offset)
    
    return jsonify({
        'success': True,
        'data': data
    })

@inventory_sales_bp.route('/daily-trend')
def daily_trend_api():
    """Get daily sales trend"""
    days = request.args.get('days', 30, type=int)
    data = get_daily_sales_trend(days)
    
    return jsonify({
        'success': True,
        'data': data
    })
