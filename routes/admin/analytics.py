from datetime import datetime, timedelta

from flask import Blueprint, current_app, render_template
from sqlalchemy import func


admin_bp = Blueprint('analytics_module', __name__, url_prefix='')


def get_real_analytics_data():
    db = current_app.extensions['sqlalchemy']
    Order = current_app.order_model_class
    OrderItem = current_app.order_item_model_class
    Product = current_app.product_model_class
    Category = current_app.category_model_class
    User = current_app.user_model_class

    try:
        total_orders = db.session.query(Order).count()
        total_revenue = db.session.query(func.sum(Order.grand_total)).scalar() or 0
        avg_order = total_revenue / total_orders if total_orders > 0 else 0

        stats = {
            'revenue': f'${total_revenue:,.2f}',
            'revenue_change': '0',
            'orders': f'{total_orders:,}',
            'orders_change': '0',
            'avg_order': f'${avg_order:.2f}',
            'avg_order_change': '0',
            'conversion': '0%',
            'conversion_change': '0',
        }

        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        revenue = []
        orders = []
        for i in range(7):
            date = datetime.now() - timedelta(days=6 - i)
            daily_revenue = db.session.query(func.sum(Order.grand_total)).filter(func.date(Order.order_date) == date.date()).scalar() or 0
            daily_orders = db.session.query(Order).filter(func.date(Order.order_date) == date.date()).count()
            revenue.append(int(daily_revenue))
            orders.append(daily_orders)

        categories_data = db.session.query(Category.category_name, func.count(Product.id)).join(Product, Category.id == Product.category_id).group_by(Category.id).all()
        category_labels = [c[0] for c in categories_data] if categories_data else ['No Data']
        category_values = [c[1] for c in categories_data] if categories_data else [0]

        # Get top products by quantity ordered
        top_products_data = db.session.query(
            Product.product_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(
            OrderItem, Product.id == OrderItem.product_id
        ).group_by(
            Product.id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(5).all()
        
        if top_products_data:
            top_labels = [p[0] for p in top_products_data]
            top_values = [int(p[1]) for p in top_products_data]
        else:
            top_labels = ['No Sales']
            top_values = [0]

        return {
            'stats': stats,
            'chart_data': {'labels': labels, 'revenue': revenue, 'orders': orders},
            'categories': {'labels': category_labels, 'data': category_values, 'colors': ['#22a54a', '#1aa179', '#20c997', '#ff9800', '#fd7e14'][:len(category_labels)]},
            'top_products': {'labels': top_labels, 'data': top_values},
            'customers_growth': {'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'], 'data': [10, 15, 20, 25, 30]},
        }
    except Exception as e:
        print(f'Error fetching analytics: {e}')
        return {
            'stats': {'revenue': '$0.00', 'revenue_change': '0', 'orders': '0', 'orders_change': '0', 'avg_order': '$0.00', 'avg_order_change': '0', 'conversion': '0%', 'conversion_change': '0'},
            'chart_data': {'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'revenue': [0, 0, 0, 0, 0, 0, 0], 'orders': [0, 0, 0, 0, 0, 0, 0]},
            'categories': {'labels': [], 'data': [], 'colors': []},
            'top_products': {'labels': [], 'data': []},
            'customers_growth': {'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'], 'data': [0, 0, 0, 0, 0]},
        }


@admin_bp.route('/analytics')
def analytics_route():
    from routes.admin.auth import login_required

    @login_required
    def _analytics():
        analytics_data = get_real_analytics_data()
        analytics_data['period'] = 'week'
        analytics_data['module_name'] = 'Analytics & Reports'
        analytics_data['module_icon'] = 'fa-chart-line'
        return render_template('dashboard/analytics.html', analytics=analytics_data, **analytics_data)

    return _analytics()
