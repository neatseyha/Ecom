"""
Advanced KPI Metrics & Analytics
Comprehensive business intelligence metrics
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from sqlalchemy import func

kpi_bp = Blueprint('kpi', __name__, url_prefix='/api/kpi')

# ============ REVENUE METRICS ============
def get_revenue_metrics(period='month'):
    """Calculate revenue metrics for different time periods"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    if period == 'today':
        date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        date_from = datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        date_from = datetime.utcnow() - timedelta(days=30)
    else:  # all-time
        date_from = datetime.min
    
    try:
        current_revenue = db.session.query(func.sum(Order.grand_total)).filter(
            Order.order_date >= date_from
        ).scalar() or 0
        
        # Get previous period for comparison
        prev_period_days = 7 if period == 'today' else (30 if period == 'week' else 30)
        prev_date_from = date_from - timedelta(days=prev_period_days)
        prev_date_to = date_from
        
        prev_revenue = db.session.query(func.sum(Order.grand_total)).filter(
            Order.order_date >= prev_date_from,
            Order.order_date < prev_date_to
        ).scalar() or 0
        
        if prev_revenue > 0:
            change_percent = ((current_revenue - prev_revenue) / prev_revenue) * 100
        else:
            change_percent = 100 if current_revenue > 0 else 0
        
        return {
            'revenue': round(float(current_revenue), 2),
            'previous_period': round(float(prev_revenue), 2),
            'change': round(current_revenue - prev_revenue, 2),
            'change_percent': round(change_percent, 2),
            'formatted': f'${current_revenue:,.2f}',
            'trend': 'up' if change_percent > 0 else ('down' if change_percent < 0 else 'flat')
        }
    except Exception as e:
        print(f"Error calculating revenue: {e}")
        return {'revenue': 0, 'change': 0, 'change_percent': 0, 'formatted': '$0.00'}

# ============ ORDER METRICS ============
def get_order_metrics(period='month'):
    """Calculate order-related KPIs"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    if period == 'today':
        date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        date_from = datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        date_from = datetime.utcnow() - timedelta(days=30)
    else:
        date_from = datetime.min
    
    try:
        total_orders = db.session.query(Order).filter(
            Order.order_date >= date_from
        ).count()
        
        total_revenue = db.session.query(func.sum(Order.grand_total)).filter(
            Order.order_date >= date_from
        ).scalar() or 0
        
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Order status breakdown
        pending = db.session.query(Order).filter(
            Order.order_date >= date_from,
            Order.status == 'pending'
        ).count()
        
        processing = db.session.query(Order).filter(
            Order.order_date >= date_from,
            Order.status == 'processing'
        ).count()
        
        completed = db.session.query(Order).filter(
            Order.order_date >= date_from,
            Order.status == 'delivered'
        ).count()
        
        cancelled = db.session.query(Order).filter(
            Order.order_date >= date_from,
            Order.status == 'cancelled'
        ).count()
        
        return {
            'total_orders': total_orders,
            'avg_order_value': round(float(avg_order_value), 2),
            'total_revenue': round(float(total_revenue), 2),
            'status_breakdown': {
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'cancelled': cancelled
            }
        }
    except Exception as e:
        print(f"Error calculating order metrics: {e}")
        return {
            'total_orders': 0,
            'avg_order_value': 0,
            'status_breakdown': {}
        }

# ============ CUSTOMER METRICS ============
def get_customer_metrics(period='month'):
    """Calculate customer-related KPIs"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    Order = current_app.order_model_class
    
    if period == 'today':
        date_from = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        date_from = datetime.utcnow() - timedelta(days=7)
    elif period == 'month':
        date_from = datetime.utcnow() - timedelta(days=30)
    else:
        date_from = datetime.min
    
    try:
        # Total customers
        total_customers = db.session.query(User).filter(
            User.role == 'customer'
        ).count()
        
        # New customers in period
        new_customers = db.session.query(User).filter(
            User.create_at >= date_from,
            User.role == 'customer'
        ).count()
        
        # Returning customers (multiple orders)
        returning = db.session.query(func.count(func.distinct(Order.user_id))).filter(
            Order.order_date >= date_from
        ).scalar() or 0
        
        # One-time buyers
        one_time = total_customers - returning
        
        # Customer lifetime value (average)
        customer_ltv = db.session.query(func.avg(func.sum(Order.grand_total))).group_by(
            Order.user_id
        ).scalar() or 0
        
        return {
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning,
            'one_time_buyers': one_time,
            'avg_customer_ltv': round(float(customer_ltv), 2),
            'retention_rate': round((returning / total_customers * 100) if total_customers > 0 else 0, 2)
        }
    except Exception as e:
        print(f"Error calculating customer metrics: {e}")
        return {
            'total_customers': 0,
            'new_customers': 0,
            'returning_customers': 0,
            'avg_customer_ltv': 0,
            'retention_rate': 0
        }

# ============ PRODUCT METRICS ============
def get_product_metrics():
    """Calculate product performance KPIs"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    OrderItem = current_app.order_item_model_class
    
    try:
        total_products = db.session.query(Product).count()
        in_stock = db.session.query(Product).filter(Product.stock > 0).count()
        out_of_stock = db.session.query(Product).filter(Product.stock == 0).count()
        low_stock = db.session.query(Product).filter(
            Product.stock > 0,
            Product.stock <= 10
        ).count()
        
        # Top selling products
        top_products = db.session.query(
            Product.product_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(
            OrderItem, Product.id == OrderItem.product_id
        ).group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()
        
        top_products_list = [{'name': p[0], 'quantity': p[1]} for p in top_products]
        
        # Average product rating
        avg_rating = db.session.query(func.avg(Product.rating_avg)).scalar() or 0
        
        return {
            'total_products': total_products,
            'in_stock': in_stock,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'avg_rating': round(float(avg_rating), 2),
            'top_products': top_products_list
        }
    except Exception as e:
        print(f"Error calculating product metrics: {e}")
        return {
            'total_products': 0,
            'in_stock': 0,
            'out_of_stock': 0,
            'top_products': []
        }

# ============ CONVERSION METRICS ============
def get_conversion_metrics():
    """Calculate conversion and sales funnel metrics"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    Order = current_app.order_model_class
    CartItem = current_app.cart_item_model_class
    
    try:
        # Total visitors/customers
        total_customers = db.session.query(User).filter(
            User.role == 'customer'
        ).count()
        
        # Customers with purchases
        customers_with_orders = db.session.query(func.count(func.distinct(Order.user_id))).scalar() or 0
        
        # Conversion rate
        conversion_rate = (customers_with_orders / total_customers * 100) if total_customers > 0 else 0
        
        # Cart abandonment
        carts_active = db.session.query(func.count(func.distinct(CartItem.user_id))).scalar() or 0
        abandonment_rate = ((carts_active - customers_with_orders) / carts_active * 100) if carts_active > 0 else 0
        
        return {
            'conversion_rate': round(conversion_rate, 2),
            'abandonment_rate': round(abandonment_rate, 2),
            'total_customers': total_customers,
            'customers_with_orders': customers_with_orders,
            'active_carts': carts_active
        }
    except Exception as e:
        print(f"Error calculating conversion metrics: {e}")
        return {
            'conversion_rate': 0,
            'abandonment_rate': 0,
            'total_customers': 0
        }

# ============ API ENDPOINTS ============
@kpi_bp.route('/revenue')
def revenue_kpi():
    """Get revenue KPIs"""
    period = request.args.get('period', 'month')
    data = get_revenue_metrics(period)
    
    return jsonify({
        'success': True,
        'period': period,
        'data': data
    })

@kpi_bp.route('/orders')
def orders_kpi():
    """Get order KPIs"""
    period = request.args.get('period', 'month')
    data = get_order_metrics(period)
    
    return jsonify({
        'success': True,
        'period': period,
        'data': data
    })

@kpi_bp.route('/customers')
def customers_kpi():
    """Get customer KPIs"""
    period = request.args.get('period', 'month')
    data = get_customer_metrics(period)
    
    return jsonify({
        'success': True,
        'period': period,
        'data': data
    })

@kpi_bp.route('/products')
def products_kpi():
    """Get product KPIs"""
    data = get_product_metrics()
    
    return jsonify({
        'success': True,
        'data': data
    })

@kpi_bp.route('/conversion')
def conversion_kpi():
    """Get conversion KPIs"""
    data = get_conversion_metrics()
    
    return jsonify({
        'success': True,
        'data': data
    })

@kpi_bp.route('/all')
def all_kpis():
    """Get all KPIs at once"""
    period = request.args.get('period', 'month')
    
    data = {
        'revenue': get_revenue_metrics(period),
        'orders': get_order_metrics(period),
        'customers': get_customer_metrics(period),
        'products': get_product_metrics(),
        'conversion': get_conversion_metrics()
    }
    
    return jsonify({
        'success': True,
        'period': period,
        'data': data
    })
