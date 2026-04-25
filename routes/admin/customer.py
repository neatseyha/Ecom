from flask import Blueprint, current_app, render_template, request


admin_bp = Blueprint('customer_module', __name__, url_prefix='')


@admin_bp.route('/customers')
def customers_route():
    from routes.admin.auth import login_required
    from datetime import datetime, timedelta
    from sqlalchemy import func

    @login_required
    def _customers():
        db = current_app.extensions['sqlalchemy']
        User = current_app.user_model_class
        Order = current_app.order_model_class

        try:
            # Pagination settings
            per_page = 10
            page = request.args.get('page', 1, type=int)
            
            # Get total count of customers
            total_customers_count = db.session.query(User).filter(User.role == 'customer').count()
            total_pages = max(1, (total_customers_count + per_page - 1) // per_page)
            
            # Ensure page is valid
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages
            
            # Get paginated customers with role='customer'
            start = (page - 1) * per_page
            customers = db.session.query(User).filter(User.role == 'customer').offset(start).limit(per_page).all()
            customers_list = []

            for customer in customers:
                total_orders = db.session.query(Order).filter(Order.user_id == customer.id).count()
                join_date = customer.create_at.strftime('%b %Y') if getattr(customer, 'create_at', None) else 'N/A'
                customers_list.append({
                    'id': customer.id,
                    'name': customer.username,
                    'email': customer.email,
                    'phone': getattr(customer, 'phone', 'N/A'),
                    'total_orders': total_orders,
                    'join_date': join_date,
                })

            # Calculate statistics (for ALL customers, not just current page)
            total_customers = total_customers_count
            
            # New customers this month
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1)
            new_this_month = db.session.query(User).filter(
                User.role == 'customer',
                User.create_at >= month_start
            ).count()
            
            # Total spent by all customers
            total_spent = db.session.query(func.sum(Order.grand_total)).scalar() or 0
            
            # Retention rate (customers with more than 1 order)
            customers_with_orders = db.session.query(User).filter(
                User.role == 'customer'
            ).all()
            
            repeat_customers = 0
            for cust in customers_with_orders:
                order_count = db.session.query(Order).filter(Order.user_id == cust.id).count()
                if order_count > 1:
                    repeat_customers += 1
            
            retention_rate = int((repeat_customers / total_customers * 100) if total_customers > 0 else 0)
            
            # Format total spent
            total_spent_formatted = f'${total_spent:,.2f}'

            return render_template(
                'dashboard/customers.html',
                customers=customers_list,
                module_name='Customer Management',
                module_icon='fa-users',
                total_customers=total_customers,
                new_this_month=new_this_month,
                total_spent=total_spent_formatted,
                retention_rate=retention_rate,
                page=page,
                total_pages=total_pages,
                per_page=per_page
            )
        except Exception as e:
            print(f'Error loading customers: {e}')
            return render_template(
                'dashboard/customers.html',
                customers=[],
                module_name='Customer Management',
                module_icon='fa-users',
                total_customers=0,
                new_this_month=0,
                total_spent='$0.00',
                retention_rate=0
            )

    return _customers()
