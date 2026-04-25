from flask import Blueprint, current_app, jsonify, render_template, request


admin_bp = Blueprint('order_module', __name__, url_prefix='')


def _format_order_datetime(value, fmt):
    return value.strftime(fmt) if value else 'N/A'


@admin_bp.route('/orders')
def orders_route():
    from routes.admin.auth import login_required

    @login_required
    def _orders():
        db = current_app.extensions['sqlalchemy']
        Order = current_app.order_model_class
        User = current_app.user_model_class

        try:
            # Pagination settings
            per_page = 10
            page = request.args.get('page', 1, type=int)
            
            # Get total count of orders
            total_orders_count = db.session.query(Order).count()
            total_pages = max(1, (total_orders_count + per_page - 1) // per_page)
            
            # Ensure page is valid
            if page < 1:
                page = 1
            if page > total_pages:
                page = total_pages
            
            # Get paginated orders
            start = (page - 1) * per_page
            orders = db.session.query(Order).order_by(Order.order_date.desc()).offset(start).limit(per_page).all()
            orders_list = []

            for order in orders:
                customer = db.session.query(User).filter(User.id == order.user_id).first()
                customer_name = order.customer_name or (customer.username if customer else 'Unknown')
                customer_email = order.customer_email or (customer.email if customer else 'N/A')

                try:
                    OrderItem = current_app.order_item_model_class
                    # Try to count actual order items
                    item_count = db.session.query(OrderItem).filter_by(order_id=order.id).count()
                    
                    # Fallback to legacy quantity if no order items exist
                    if item_count == 0 and order.quantity:
                        item_count = order.quantity
                except Exception:
                    item_count = order.quantity or 0

                orders_list.append({
                    'id': order.id,  # Raw numeric ID for database lookup
                    'order_id': f'#{order.id}',  # Formatted display ID
                    'customer': customer_name,
                    'email': customer_email,
                    'amount': f'${order.grand_total:,.2f}' if order.grand_total else '$0.00',
                    'status': order.status or 'pending',
                    'payment_status': order.payment_status or 'pending',
                    'payment_method': order.payment_method or 'N/A',
                    'date': order.order_date.strftime('%b %d, %Y') if order.order_date else 'N/A',
                    'item_count': item_count,
                })

            return render_template('dashboard/orders.html', orders=orders_list, module_name='Order Management', module_icon='fa-shopping-cart',
                                 page=page, total_pages=total_pages, per_page=per_page, total=total_orders_count)
        except Exception as e:
            print(f'Error loading orders: {e}')
            return render_template('dashboard/orders.html', orders=[], module_name='Order Management', module_icon='fa-shopping-cart',
                                 page=1, total_pages=1, per_page=10, total=0)

    return _orders()


@admin_bp.route('/api/admin/orders/<int:order_id>', methods=['GET'])
def order_details_api(order_id):
    from routes.admin.auth import login_required

    @login_required
    def _order_details():
        db = current_app.extensions['sqlalchemy']
        Order = current_app.order_model_class
        OrderItem = current_app.order_item_model_class
        User = current_app.user_model_class

        order = db.session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404

        customer = db.session.query(User).filter(User.id == order.user_id).first()
        items = db.session.query(OrderItem).filter_by(order_id=order.id).all()

        items_data = []
        for item in items:
            items_data.append({
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price or 0),
                'total': float(item.total or 0),
                'size': item.size,
                'color': item.color,
            })

        if not items_data and order.product_name:
            quantity = order.quantity or 1
            unit_price = float(order.price or 0)
            total = float(order.total_price or order.grand_total or unit_price * quantity)
            items_data.append({
                'product_name': order.product_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total': total,
                'size': None,
                'color': None,
            })

        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number or f'#{order.id}',
                'display_id': f'#{order.id}',
                'order_date': _format_order_datetime(order.order_date, '%b %d, %Y %I:%M %p'),
                'status': order.status or 'pending',
                'payment_method': order.payment_method or 'N/A',
                'payment_status': order.payment_status or 'pending',
                'customer_name': order.customer_name or (customer.username if customer else 'Unknown'),
                'customer_email': order.customer_email or (customer.email if customer else 'N/A'),
                'customer_phone': order.customer_phone or (customer.phone if customer and getattr(customer, 'phone', None) else 'N/A'),
                'shipping_address': order.shipping_address or order.billing_address or 'N/A',
                'subtotal': float(order.subtotal or 0),
                'shipping_cost': float(order.shipping_cost or 0),
                'grand_total': float(order.grand_total or 0),
                'notes': order.notes or '',
                'items': items_data,
            }
        })

    return _order_details()
