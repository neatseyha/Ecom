"""
Customer Analytics & Export/Reporting System
Customer insights and data export functionality
"""

from flask import Blueprint, jsonify, request, current_app, send_file
from datetime import datetime, timedelta
from sqlalchemy import func
import csv
from io import StringIO, BytesIO
import json

analytics_export_bp = Blueprint('analytics_export', __name__, url_prefix='/api/analytics')

# ============ CUSTOMER DEMOGRAPHICS ============
def get_customer_demographics():
    """Get customer demographic breakdown"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    
    try:
        # By gender
        gender_stats = db.session.query(
            User.gender,
            func.count(User.id).label('count')
        ).filter(User.role == 'customer', User.gender != None).group_by(User.gender).all()
        
        # By region
        region_stats = db.session.query(
            User.city,
            func.count(User.id).label('count')
        ).filter(User.role == 'customer', User.city != None).group_by(User.city).order_by(
            func.count(User.id).desc()
        ).limit(10).all()
        
        return {
            'by_gender': {
                'labels': [g.gender or 'Not specified' for g in gender_stats],
                'data': [g.count for g in gender_stats]
            },
            'by_region': {
                'labels': [r.city for r in region_stats],
                'data': [r.count for r in region_stats]
            }
        }
    except Exception as e:
        print(f"Error getting customer demographics: {e}")
        return {'by_gender': {}, 'by_region': {}}

# ============ CUSTOMER LIFECYCLE ============
def get_customer_lifecycle():
    """Get customer lifecycle analysis (new, active, inactive)"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    Order = current_app.order_model_class
    
    try:
        today = datetime.utcnow()
        
        # New customers (last 30 days)
        new_customers = db.session.query(User).filter(
            User.create_at >= today - timedelta(days=30),
            User.role == 'customer'
        ).count()
        
        # Active customers (ordered in last 30 days)
        active_customers = db.session.query(func.count(func.distinct(Order.user_id))).filter(
            Order.order_date >= today - timedelta(days=30)
        ).scalar() or 0
        
        # Inactive customers (no orders in last 60 days)
        inactive = db.session.query(User).filter(
            User.role == 'customer',
            User.last_login < today - timedelta(days=60)
        ).count()
        
        # At-risk customers (no activity but previously active)
        at_risk = db.session.query(User).filter(
            User.role == 'customer',
            User.last_login >= today - timedelta(days=60),
            User.last_login < today - timedelta(days=30)
        ).count()
        
        return {
            'new': new_customers,
            'active': active_customers,
            'at_risk': at_risk,
            'inactive': inactive
        }
    except Exception as e:
        print(f"Error getting customer lifecycle: {e}")
        return {'new': 0, 'active': 0, 'at_risk': 0, 'inactive': 0}

# ============ CUSTOMER SPENDING DISTRIBUTION ============
def get_customer_spending_distribution():
    """Get distribution of customer spending levels"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        # Get customer spending totals
        customer_spend = db.session.query(
            func.sum(Order.grand_total).label('total_spend')
        ).group_by(Order.user_id).all()
        
        # Categorize by spending level
        spending_levels = {
            'high': 0,      # > $1000
            'medium': 0,    # $500-$1000
            'low': 0,       # $100-$500
            'minimal': 0    # < $100
        }
        
        for spend in customer_spend:
            amount = spend.total_spend or 0
            if amount >= 1000:
                spending_levels['high'] += 1
            elif amount >= 500:
                spending_levels['medium'] += 1
            elif amount >= 100:
                spending_levels['low'] += 1
            else:
                spending_levels['minimal'] += 1
        
        return spending_levels
    except Exception as e:
        print(f"Error getting spending distribution: {e}")
        return {'high': 0, 'medium': 0, 'low': 0, 'minimal': 0}

# ============ EXPORT ORDERS ============
def export_orders_csv(date_from=None, date_to=None):
    """Export orders to CSV"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        query = db.session.query(Order)
        
        if date_from:
            query = query.filter(Order.order_date >= date_from)
        if date_to:
            query = query.filter(Order.order_date <= date_to)
        
        orders = query.order_by(Order.order_date.desc()).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Order ID', 'Order Number', 'Customer', 'Email', 'Date', 'Status', 'Total', 'Payment Status'])
        
        for order in orders:
            user = db.session.query(User).get(order.user_id)
            writer.writerow([
                order.id,
                order.order_number,
                user.username if user else 'Unknown',
                user.email if user else '',
                order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else '',
                order.status,
                f'${order.grand_total:.2f}',
                order.payment_status
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting orders: {e}")
        return ""

# ============ EXPORT CUSTOMERS ============
def export_customers_csv():
    """Export customer list to CSV"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    User = current_app.user_model_class
    
    try:
        customers = db.session.query(User).filter(
            User.role == 'customer'
        ).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Email', 'Name', 'Phone', 'City', 'Created', 'Last Login'])
        
        for customer in customers:
            writer.writerow([
                customer.id,
                customer.username,
                customer.email or '',
                f'{customer.first_name or ""} {customer.last_name or ""}',
                customer.phone or '',
                customer.city or '',
                customer.create_at.strftime('%Y-%m-%d') if customer.create_at else '',
                customer.last_login.strftime('%Y-%m-%d') if customer.last_login else ''
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting customers: {e}")
        return ""

# ============ EXPORT PRODUCTS ============
def export_products_csv():
    """Export product inventory to CSV"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    
    try:
        products = db.session.query(Product).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'SKU', 'Price', 'Stock', 'Category', 'Rating', 'Reviews', 'Status'])
        
        for product in products:
            writer.writerow([
                product.id,
                product.product_name,
                product.sku or '',
                f'${product.price:.2f}',
                product.stock,
                product.category_id,
                product.rating_avg,
                product.review_count,
                product.status
            ])
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting products: {e}")
        return ""

# ============ API ENDPOINTS ============
@analytics_export_bp.route('/customer-demographics')
def customer_demographics_api():
    """Get customer demographic analysis"""
    data = get_customer_demographics()
    
    return jsonify({
        'success': True,
        'data': data
    })

@analytics_export_bp.route('/customer-lifecycle')
def customer_lifecycle_api():
    """Get customer lifecycle data"""
    data = get_customer_lifecycle()
    
    return jsonify({
        'success': True,
        'data': data
    })

@analytics_export_bp.route('/spending-distribution')
def spending_distribution_api():
    """Get customer spending distribution"""
    data = get_customer_spending_distribution()
    
    return jsonify({
        'success': True,
        'data': data
    })

@analytics_export_bp.route('/export/orders')
def export_orders_api():
    """Export orders as CSV"""
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')
    
    date_from = datetime.fromisoformat(date_from_str) if date_from_str else None
    date_to = datetime.fromisoformat(date_to_str) if date_to_str else None
    
    csv_content = export_orders_csv(date_from, date_to)
    
    csv_bytes = BytesIO(csv_content.encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'orders_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@analytics_export_bp.route('/export/customers')
def export_customers_api():
    """Export customers as CSV"""
    csv_content = export_customers_csv()
    
    csv_bytes = BytesIO(csv_content.encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'customers_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@analytics_export_bp.route('/export/products')
def export_products_api():
    """Export products as CSV"""
    csv_content = export_products_csv()
    
    csv_bytes = BytesIO(csv_content.encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'products_{datetime.now().strftime("%Y%m%d")}.csv'
    )
