"""
Dashboard Alerts & Notifications System
Real-time alerts for inventory, orders, payments, and reviews
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime, timedelta
from sqlalchemy import func

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

# ============ LOW STOCK ALERTS ============
def get_low_stock_alerts(threshold=10):
    """Get products with low stock levels"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    
    try:
        low_stock = db.session.query(Product).filter(
            Product.stock <= threshold,
            Product.stock > 0
        ).all()
        
        return [{
            'id': p.id,
            'product_name': p.product_name,
            'stock': p.stock,
            'threshold': threshold,
            'severity': 'critical' if p.stock <= 3 else 'warning',
            'message': f'{p.product_name} has only {p.stock} items left'
        } for p in low_stock]
    except Exception as e:
        print(f"Error getting low stock alerts: {e}")
        return []

# ============ OUT OF STOCK ALERTS ============
def get_out_of_stock_alerts():
    """Get products that are out of stock"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    
    try:
        out_of_stock = db.session.query(Product).filter(
            Product.stock == 0
        ).all()
        
        return [{
            'id': p.id,
            'product_name': p.product_name,
            'stock': 0,
            'severity': 'critical',
            'message': f'{p.product_name} is OUT OF STOCK'
        } for p in out_of_stock]
    except Exception as e:
        print(f"Error getting out of stock alerts: {e}")
        return []

# ============ PENDING ORDERS ALERTS ============
def get_pending_orders_alerts():
    """Get orders pending payment or processing"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        pending = db.session.query(Order).filter(
            Order.status.in_(['pending', 'processing'])
        ).order_by(Order.order_date.desc()).limit(10).all()
        
        alerts = []
        for order in pending:
            user = db.session.query(User).get(order.user_id)
            customer_name = user.username if user else 'Unknown'
            
            alerts.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer': customer_name,
                'amount': f'${order.grand_total:,.2f}',
                'status': order.status,
                'severity': 'warning',
                'message': f'Order #{order.order_number} ({order.status})',
                'time': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else None
            })
        
        return alerts
    except Exception as e:
        print(f"Error getting pending orders: {e}")
        return []

# ============ PENDING REVIEWS ALERTS ============
def get_pending_reviews_alerts():
    """Get reviews waiting for approval"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Rating = current_app.rating_model_class
    Product = current_app.product_model_class
    User = current_app.user_model_class
    
    try:
        pending = db.session.query(Rating).filter(
            Rating.status == 'pending'
        ).limit(10).all()
        
        alerts = []
        for review in pending:
            product = db.session.query(Product).get(review.product_id)
            user = db.session.query(User).get(review.user_id)
            
            alerts.append({
                'id': review.id,
                'product_name': product.product_name if product else 'Unknown',
                'reviewer': user.username if user else 'Anonymous',
                'rating': review.rating,
                'severity': 'info',
                'message': f'New review for {product.product_name if product else "Unknown"}',
                'time': review.created_at.strftime('%Y-%m-%d %H:%M:%S') if review.created_at else None
            })
        
        return alerts
    except Exception as e:
        print(f"Error getting pending reviews: {e}")
        return []

# ============ HIGH VALUE ORDERS ALERTS ============
def get_high_value_orders_alerts(threshold=500):
    """Get high-value orders placed recently"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        recent_high_value = db.session.query(Order).filter(
            Order.grand_total >= threshold,
            Order.order_date >= datetime.utcnow() - timedelta(days=1)
        ).order_by(Order.grand_total.desc()).limit(10).all()
        
        alerts = []
        for order in recent_high_value:
            user = db.session.query(User).get(order.user_id)
            customer_name = user.username if user else 'Unknown'
            
            alerts.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer': customer_name,
                'amount': f'${order.grand_total:,.2f}',
                'severity': 'success',
                'message': f'High-value order: ${order.grand_total:,.2f}',
                'time': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else None
            })
        
        return alerts
    except Exception as e:
        print(f"Error getting high value orders: {e}")
        return []

# ============ FAILED PAYMENTS ALERTS ============
def get_failed_payments_alerts():
    """Get failed payment attempts"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Payment = current_app.payment_model_class
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        failed = db.session.query(Payment).filter(
            Payment.payment_status.in_(['failed', 'declined'])
        ).limit(10).all()
        
        alerts = []
        for payment in failed:
            order = db.session.query(Order).get(payment.order_id)
            user = db.session.query(User).get(order.user_id) if order else None
            customer_name = user.username if user else 'Unknown'
            
            alerts.append({
                'id': payment.id,
                'order_number': order.order_number if order else 'Unknown',
                'customer': customer_name,
                'severity': 'critical',
                'message': f'Payment failed for order #{order.order_number if order else "Unknown"}',
                'time': payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(payment, 'created_at') else None
            })
        
        return alerts
    except Exception as e:
        print(f"Error getting failed payments: {e}")
        return []

# ============ NEW CUSTOMER REGISTRATIONS ============
def get_new_customer_alerts(hours=24):
    """Get new customer registrations in the last N hours"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        new_customers = db.session.query(User).filter(
            User.create_at >= cutoff_time,
            User.role == 'customer'
        ).order_by(User.create_at.desc()).limit(10).all()
        
        return [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'severity': 'info',
            'message': f'New customer: {user.username}',
            'time': user.create_at.strftime('%Y-%m-%d %H:%M:%S') if user.create_at else None
        } for user in new_customers]
    except Exception as e:
        print(f"Error getting new customer alerts: {e}")
        return []

# ============ GET ALL ALERTS ============
def get_all_alerts():
    """Aggregate all alerts by severity"""
    alerts = {
        'critical': [],
        'warning': [],
        'success': [],
        'info': []
    }
    
    # Add all alert types
    for alert in get_low_stock_alerts() + get_out_of_stock_alerts():
        alerts[alert['severity']].append(alert)
    
    for alert in get_pending_orders_alerts():
        alerts[alert['severity']].append(alert)
    
    for alert in get_pending_reviews_alerts():
        alerts[alert['severity']].append(alert)
    
    for alert in get_high_value_orders_alerts():
        alerts[alert['severity']].append(alert)
    
    for alert in get_failed_payments_alerts():
        alerts[alert['severity']].append(alert)
    
    for alert in get_new_customer_alerts():
        alerts[alert['severity']].append(alert)
    
    return alerts

# ============ API ENDPOINTS ============
@alerts_bp.route('/all')
def get_all_alerts_api():
    """Get all alerts (API endpoint)"""
    alerts = get_all_alerts()
    total_alerts = sum(len(alerts[severity]) for severity in alerts)
    
    return jsonify({
        'success': True,
        'total_alerts': total_alerts,
        'alerts': alerts
    })

@alerts_bp.route('/low-stock')
def low_stock_api():
    """Get low stock alerts"""
    threshold = request.args.get('threshold', 10, type=int)
    alerts = get_low_stock_alerts(threshold)
    
    return jsonify({
        'success': True,
        'total': len(alerts),
        'alerts': alerts
    })

@alerts_bp.route('/out-of-stock')
def out_of_stock_api():
    """Get out of stock alerts"""
    alerts = get_out_of_stock_alerts()
    
    return jsonify({
        'success': True,
        'total': len(alerts),
        'alerts': alerts
    })

@alerts_bp.route('/pending-orders')
def pending_orders_api():
    """Get pending orders"""
    alerts = get_pending_orders_alerts()
    
    return jsonify({
        'success': True,
        'total': len(alerts),
        'alerts': alerts
    })

@alerts_bp.route('/pending-reviews')
def pending_reviews_api():
    """Get pending reviews"""
    alerts = get_pending_reviews_alerts()
    
    return jsonify({
        'success': True,
        'total': len(alerts),
        'alerts': alerts
    })
