from flask import render_template, jsonify, request, Blueprint, current_app
from sqlalchemy import func
from datetime import datetime, timedelta

# Create Blueprint
dashboard_bp = Blueprint('admin', __name__, url_prefix='')

# Import enhanced analytics functions
from routes.admin.dashboard_alerts import (
    get_all_alerts, get_low_stock_alerts, get_out_of_stock_alerts,
    get_pending_orders_alerts, get_pending_reviews_alerts
)
from routes.admin.dashboard_kpi import (
    get_revenue_metrics, get_order_metrics, get_customer_metrics,
    get_product_metrics, get_conversion_metrics
)
from routes.admin.dashboard_inventory_sales import (
    get_top_selling_products, get_slow_moving_products,
    get_revenue_by_category, get_daily_sales_trend
)
from routes.admin.dashboard_customer_analytics import (
    get_customer_lifecycle, get_customer_demographics,
    get_customer_spending_distribution
)
from routes.admin.dashboard_activity_logger import (
    get_admin_activity_logs, get_activity_statistics
)

# ============ DATABASE STATISTICS ============
def get_real_stats():
    """Get real statistics from database"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        # Total orders
        total_orders = db.session.query(Order).count()
        
        # Total revenue
        total_revenue = db.session.query(func.sum(Order.grand_total)).scalar() or 0
        
        # Active customers (users with role='customer')
        active_customers = db.session.query(User).filter(User.role == 'customer').count()
        
        # Products in stock
        products_in_stock = db.session.query(Product).filter(Product.stock > 0).count()
        
        return {
            'total_orders': f'{total_orders:,}',
            'total_revenue': f'${total_revenue:,.2f}',
            'active_customers': f'{active_customers:,}',
            'products_in_stock': f'{products_in_stock:,}'
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {
            'total_orders': '0',
            'total_revenue': '$0.00',
            'active_customers': '0',
            'products_in_stock': '0'
        }

def get_recent_orders(limit=5):
    """Get real recent orders from database"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        orders = db.session.query(Order).order_by(Order.order_date.desc()).limit(limit).all()
        recent = []
        
        for order in orders:
            # Get customer name
            customer = db.session.query(User).filter(User.id == order.user_id).first()
            customer_name = customer.username if customer else 'Unknown'
            
            recent.append({
                'id': f'#{order.id}',
                'customer': customer_name,
                'amount': f'${order.grand_total:,.2f}',
                'status': order.status or 'pending',
                'date': order.order_date.strftime('%b %d, %Y') if order.order_date else 'N/A'
            })
        
        return recent
    except Exception as e:
        print(f"Error fetching recent orders: {e}")
        return []

def generate_chart_data(period='week'):
    """Generate chart data based on real database data"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    try:
        if period == 'week':
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            revenue = []
            orders = []
            
            for i in range(7):
                date = datetime.now() - timedelta(days=6-i)
                daily_revenue = db.session.query(func.sum(Order.grand_total)).filter(
                    func.date(Order.order_date) == date.date()
                ).scalar() or 0
                daily_orders = db.session.query(Order).filter(
                    func.date(Order.order_date) == date.date()
                ).count()
                
                revenue.append(int(daily_revenue))
                orders.append(daily_orders)
        else:
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            revenue = [0, 0, 0, 0, 0, 0, 0]
            orders = [0, 0, 0, 0, 0, 0, 0]
        
        return {
            'labels': labels,
            'revenue': revenue,
            'orders': orders
        }
    except Exception as e:
        print(f"Error generating chart data: {e}")
        return {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'revenue': [0, 0, 0, 0, 0, 0, 0],
            'orders': [0, 0, 0, 0, 0, 0, 0]
        }

def get_analytics_stats(period='week'):
    """Get real analytics statistics from database"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    
    try:
        total_orders = db.session.query(Order).count()
        total_revenue = db.session.query(func.sum(Order.grand_total)).scalar() or 0
        
        if total_orders > 0:
            avg_order = total_revenue / total_orders
        else:
            avg_order = 0
        
        return {
            'revenue': f'${total_revenue:,.2f}',
            'revenue_change': '0',
            'orders': f'{total_orders:,}',
            'orders_change': '0',
            'avg_order': f'${avg_order:.2f}',
            'avg_order_change': '0',
            'conversion': '0%',
            'conversion_change': '0'
        }
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {
            'revenue': '$0.00',
            'revenue_change': '0',
            'orders': '0',
            'orders_change': '0',
            'avg_order': '$0.00',
            'avg_order_change': '0',
            'conversion': '0%',
            'conversion_change': '0'
        }

# ============ ENHANCED DASHBOARD ROUTE ============
@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def dashboard_route():
    from routes.admin.auth import login_required
    
    @login_required
    def _dashboard():
        try:
            # ===== REAL-TIME ALERTS =====
            alerts = get_all_alerts()
            low_stock = get_low_stock_alerts()
            out_of_stock = get_out_of_stock_alerts()
            pending_orders = get_pending_orders_alerts()
            
            # ===== ADVANCED KPI METRICS =====
            revenue_kpi = get_revenue_metrics('month')
            order_kpi = get_order_metrics('month')
            customer_kpi = get_customer_metrics('month')
            product_kpi = get_product_metrics()
            conversion_kpi = get_conversion_metrics()
            
            # ===== INVENTORY ANALYTICS =====
            top_products = get_top_selling_products(limit=5)
            slow_movers = get_slow_moving_products(limit=5)
            
            # ===== SALES PERFORMANCE =====
            revenue_by_category = get_revenue_by_category()
            daily_trend = get_daily_sales_trend(days=7)
            
            # ===== CUSTOMER ANALYTICS =====
            customer_lifecycle = get_customer_lifecycle()
            customer_demographics = get_customer_demographics()
            spending_distribution = get_customer_spending_distribution()
            
            # ===== ACTIVITY LOG =====
            activity_logs = get_admin_activity_logs(limit=10)
            activity_stats = get_activity_statistics(days=30)
            
            # ===== DASHBOARD DATA =====
            dashboard_data = {
                'stats': {
                    'total_revenue': revenue_kpi['formatted'],
                    'total_orders': order_kpi['total_orders'],
                    'active_customers': customer_kpi['total_customers'],
                    'products_in_stock': product_kpi['in_stock']
                },
                'kpis': {
                    'revenue': revenue_kpi,
                    'orders': order_kpi,
                    'customers': customer_kpi,
                    'products': product_kpi,
                    'conversion': conversion_kpi
                },
                'alerts': {
                    'total_alerts': sum(len(alerts[severity]) for severity in alerts),
                    'critical': len(alerts['critical']),
                    'warning': len(alerts['warning']),
                    'low_stock': len(low_stock),
                    'out_of_stock': len(out_of_stock),
                    'pending_orders': len(pending_orders)
                },
                'inventory': {
                    'top_products': top_products,
                    'slow_movers': slow_movers,
                    'revenue_by_category': revenue_by_category
                },
                'sales': {
                    'daily_trend': daily_trend
                },
                'customers': {
                    'lifecycle': customer_lifecycle,
                    'spending_distribution': spending_distribution
                },
                'activity': {
                    'recent_logs': activity_logs,
                    'statistics': activity_stats
                }
            }
            
            return render_template(
                'dashboard/dashboard_enhanced.html',
                **dashboard_data,
                module_name='Dashboard',
                module_icon='fa-home'
            )
        except Exception as e:
            print(f"Error rendering dashboard: {e}")
            # Fallback to basic dashboard
            return render_template('dashboard/dashboard.html', 
                                 stats=get_real_stats(),
                                 recent_orders=get_recent_orders(limit=10),
                                 module_name='Dashboard',
                                 module_icon='fa-home')
    
    return _dashboard()


# ============ API ROUTES FOR DYNAMIC DATA ============
@dashboard_bp.route('/api/analytics')
def get_analytics_api():
    """API endpoint for dynamic analytics data"""
    period = request.args.get('period', 'week')
    stats = get_analytics_stats(period)
    chart_data = generate_chart_data(period)
    
    return jsonify({
        'stats': stats,
        'chart_data': chart_data
    })


@dashboard_bp.route('/api/notifications')
def get_notifications_api():
    """API endpoint for customer order notifications"""
    from flask import current_app
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    User = current_app.user_model_class
    
    try:
        # Get recent orders (last 10) for notifications
        recent_orders = db.session.query(Order).order_by(Order.order_date.desc()).limit(10).all()
        
        notifications = []
        for order in recent_orders:
            customer = db.session.query(User).filter(User.id == order.user_id).first()
            customer_name = customer.username if customer else 'Unknown Customer'
            
            notifications.append({
                'id': order.id,
                'customer': customer_name,
                'order_id': f'#{order.id}',
                'amount': f'${order.grand_total:,.2f}',
                'status': order.status or 'pending',
                'date': order.order_date.strftime('%Y-%m-%d %H:%M') if order.order_date else 'N/A',
                'message': f'{customer_name} placed order #{order.id} for {order.grand_total:,.2f}'
            })
        
        return jsonify({
            'success': True,
            'count': len(notifications),
            'notifications': notifications
        })
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({
            'success': False,
            'count': 0,
            'notifications': []
        })
