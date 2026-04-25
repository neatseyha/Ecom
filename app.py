from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import inspect, text, func
from config import Config, ProductionConfig
import dashboard_config
import os
import json
from telegram_bot import TelegramNotifier
import uuid
from datetime import datetime
from bakong_khqr import KHQR
import io
from base64 import b64encode

app = Flask(__name__)

# Use production config if DATABASE_URL is set (Render provides this)
if os.getenv('DATABASE_URL'):
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(Config)

# Ensure we have a secret key
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = os.urandom(24).hex()

# Database configuration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from model import init_models
Product, Category, User, Order, Wishlist, Rating, CartItem, OrderItem, Payment, Address, Shipping, Coupon, Brand = init_models(db)


def ensure_sqlite_product_schema():
    """Backfill missing product columns for older SQLite databases."""
    engine = db.engine
    if engine.url.get_backend_name() != 'sqlite':
        return

    inspector = inspect(engine)
    if 'product' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('product')}
    column_definitions = {
        'sku': 'VARCHAR(50)',
        'brand': 'VARCHAR(80)',
        'color': 'VARCHAR(100)',
        'size': 'VARCHAR(100)',
        'discount_percentage': 'FLOAT DEFAULT 0',
        'discount_price': 'FLOAT',
        'image_medium': 'VARCHAR(120)',
        'image_small': 'VARCHAR(120)',
        'weight': 'FLOAT',
        'dimensions': 'VARCHAR(100)',
        'rating_avg': 'FLOAT DEFAULT 0',
        'review_count': 'INTEGER DEFAULT 0',
        'is_featured': 'BOOLEAN DEFAULT 0',
        'is_new': 'BOOLEAN DEFAULT 0',
        'view_count': 'INTEGER DEFAULT 0',
        'meta_description': 'VARCHAR(160)',
        'meta_keywords': 'VARCHAR(200)',
    }

    missing_columns = [
        (name, definition)
        for name, definition in column_definitions.items()
        if name not in existing_columns
    ]

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f'ALTER TABLE product ADD COLUMN {name} {definition}'))

    print(f'Updated product table schema with {len(missing_columns)} missing columns.')


def ensure_sqlite_user_schema():
    """Backfill missing user columns for older SQLite databases."""
    engine = db.engine
    if engine.url.get_backend_name() != 'sqlite':
        return

    inspector = inspect(engine)
    if 'user' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('user')}
    column_definitions = {
        'first_name': 'VARCHAR(50)',
        'last_name': 'VARCHAR(50)',
        'phone': 'VARCHAR(20)',
        'profile_picture': 'VARCHAR(120)',
        'gender': 'VARCHAR(10)',
        'date_of_birth': 'DATE',
        'bio': 'VARCHAR(500)',
        'address': 'VARCHAR(255)',
        'city': 'VARCHAR(50)',
        'state': 'VARCHAR(50)',
        'zip_code': 'VARCHAR(20)',
        'country': 'VARCHAR(50)',
        'email_verified': 'BOOLEAN DEFAULT 0',
        'phone_verified': 'BOOLEAN DEFAULT 0',
        'newsletter_subscribed': 'BOOLEAN DEFAULT 0',
        'last_login': 'DATETIME',
        'updated_at': 'DATETIME',
        'deleted_at': 'DATETIME',
    }

    missing_columns = [
        (name, definition)
        for name, definition in column_definitions.items()
        if name not in existing_columns
    ]

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f'ALTER TABLE user ADD COLUMN {name} {definition}'))

    print(f'Updated user table schema with {len(missing_columns)} missing columns.')


def ensure_sqlite_category_schema():
    """Backfill missing category columns for older SQLite databases."""
    engine = db.engine
    if engine.url.get_backend_name() != 'sqlite':
        return

    inspector = inspect(engine)
    if 'category' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('category')}
    column_definitions = {
        'slug': 'VARCHAR(100)',
        'description': 'VARCHAR(500)',
        'parent_id': 'INTEGER',
        'icon': 'VARCHAR(100)',
        'image': 'VARCHAR(120)',
        'display_order': 'INTEGER DEFAULT 0',
        'status': "VARCHAR(20) DEFAULT 'active'",
        'meta_description': 'VARCHAR(160)',
        'meta_keywords': 'VARCHAR(200)',
        'created_at': 'DATETIME',
    }

    missing_columns = [
        (name, definition)
        for name, definition in column_definitions.items()
        if name not in existing_columns
    ]

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f'ALTER TABLE category ADD COLUMN {name} {definition}'))

    print(f'Updated category table schema with {len(missing_columns)} missing columns.')


def ensure_sqlite_order_schema():
    """Backfill missing order columns for older SQLite databases."""
    engine = db.engine
    if engine.url.get_backend_name() != 'sqlite':
        return

    inspector = inspect(engine)
    if 'order' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('order')}
    column_definitions = {
        'order_number': 'VARCHAR(20)',
        'subtotal': 'FLOAT DEFAULT 0',
        'discount_amount': 'FLOAT DEFAULT 0',
        'tax_amount': 'FLOAT DEFAULT 0',
        'shipping_cost': 'FLOAT DEFAULT 0',
        'grand_total': 'FLOAT DEFAULT 0',
        'customer_name': 'VARCHAR(120)',
        'customer_email': 'VARCHAR(120)',
        'customer_phone': 'VARCHAR(20)',
        'billing_address': 'VARCHAR(500)',
        'shipping_address': 'VARCHAR(500)',
        'shipping_method': 'VARCHAR(50)',
        'tracking_number': 'VARCHAR(100)',
        'payment_method': 'VARCHAR(50)',
        'payment_status': "VARCHAR(50) DEFAULT 'pending'",
        'estimated_delivery': 'DATETIME',
        'delivery_date': 'DATETIME',
        'cancel_reason': 'VARCHAR(500)',
        'refund_status': "VARCHAR(50) DEFAULT 'none'",
        'refund_amount': 'FLOAT',
        'currency': "VARCHAR(3) DEFAULT 'USD'",
        'notes': 'TEXT',
        'order_date': 'DATETIME',
        'updated_at': 'DATETIME',
    }

    missing_columns = [
        (name, definition)
        for name, definition in column_definitions.items()
        if name not in existing_columns
    ]

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f'ALTER TABLE \"order\" ADD COLUMN {name} {definition}'))

    print(f'Updated order table schema with {len(missing_columns)} missing columns.')


def ensure_sqlite_rating_schema():
    """Backfill missing rating columns for older SQLite databases."""
    engine = db.engine
    if engine.url.get_backend_name() != 'sqlite':
        return

    inspector = inspect(engine)
    if 'rating' not in inspector.get_table_names():
        return

    existing_columns = {column['name'] for column in inspector.get_columns('rating')}
    column_definitions = {
        'review_title': 'VARCHAR(200)',
        'helpful_yes_count': 'INTEGER DEFAULT 0',
        'helpful_no_count': 'INTEGER DEFAULT 0',
        'helpful_count': 'INTEGER DEFAULT 0',
        'images': 'VARCHAR(500)',
        'status': "VARCHAR(50) DEFAULT 'approved'",
        'verified_purchase': 'BOOLEAN DEFAULT 0',
        'is_seller_response': 'BOOLEAN DEFAULT 0',
        'seller_response': 'TEXT',
        'seller_response_date': 'DATETIME',
        'updated_at': 'DATETIME',
    }

    missing_columns = [
        (name, definition)
        for name, definition in column_definitions.items()
        if name not in existing_columns
    ]

    if not missing_columns:
        return

    with engine.begin() as connection:
        for name, definition in missing_columns:
            connection.execute(text(f'ALTER TABLE rating ADD COLUMN {name} {definition}'))

    print(f'Updated rating table schema with {len(missing_columns)} missing columns.')

# Store models in app for routes to access
app.user_model_class = User
app.product_model_class = Product
app.category_model_class = Category
app.order_model_class = Order
app.wishlist_model_class = Wishlist
app.rating_model_class = Rating
app.cart_item_model_class = CartItem
app.order_item_model_class = OrderItem
app.payment_model_class = Payment
app.address_model_class = Address
app.shipping_model_class = Shipping
app.coupon_model_class = Coupon
app.brand_model_class = Brand

with app.app_context():
    ensure_sqlite_product_schema()
    ensure_sqlite_user_schema()
    ensure_sqlite_category_schema()
    ensure_sqlite_order_schema()
    ensure_sqlite_rating_schema()
    try:
        if User.query.count() == 0:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Created default admin user: username=admin password=admin123')
    except Exception as e:
        pass

@app.context_processor
def inject_theme_defaults():
    return {
        'DEFAULT_THEME': app.config.get('DEFAULT_THEME', 'light'),
        'DEFAULT_PALETTE': app.config.get('DEFAULT_PALETTE', 'indigo')
    }

def product_to_dict(p):
    image_url = p.image
    if image_url and not image_url.startswith('http'):
        # Usually images uploaded via the backend are saved in 'upload' subfolder
        image_url = url_for('static', filename='upload/' + image_url)
    elif not image_url:
        image_url = 'https://via.placeholder.com/400x500?text=No+Image'
        
    return {
        'id': p.id,
        'name': p.product_name,
        'price': float(p.price),
        'image': image_url,
        'description': p.description or 'No description available.',
        'stock': p.stock
    }

def get_products(limit=None, search=None, category_id=None, min_price=None, max_price=None, 
                  brand=None, in_stock_only=False, has_discount=False, min_rating=None, sort_by='featured'):
    """
    Enhanced product filtering with multiple criteria.
    
    Args:
        limit: Max number of products to return
        search: Search term for product name/description
        category_id: Filter by category ID
        min_price: Minimum price filter
        max_price: Maximum price filter
        brand: Filter by brand name
        in_stock_only: Only show in-stock products
        has_discount: Only show discounted products
        min_rating: Minimum average rating (1-5)
        sort_by: Sort option (featured, price_asc, price_desc, newest, rating, popular)
    """
    query = Product.query
    
    # Apply filters
    if search:
        # Search in product name, description, and brand
        query = query.filter(
            (Product.product_name.ilike(f'%{search}%')) |
            (Product.description.ilike(f'%{search}%')) |
            (Product.brand.ilike(f'%{search}%'))
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if brand:
        query = query.filter(Product.brand.ilike(f'%{brand}%'))
    
    if in_stock_only:
        query = query.filter(Product.stock > 0)
    
    if has_discount:
        query = query.filter(Product.discount_percentage > 0)
    
    if min_rating is not None:
        query = query.filter(Product.rating_avg >= min_rating)
    
    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.id.desc())
    elif sort_by == 'rating':
        query = query.order_by(Product.rating_avg.desc())
    elif sort_by == 'popular':
        query = query.order_by(Product.view_count.desc())
    else:  # featured
        query = query.order_by(Product.is_featured.desc(), Product.id.asc())
    
    if limit:
        query = query.limit(limit)
    
    return [product_to_dict(p) for p in query.all()]

def get_product(product_id):
    p = Product.query.get(product_id)
    return product_to_dict(p) if p else None

@app.route('/')
def home():
    wishlist_product_ids = []
    if 'user_id' in session:
        wishlist_product_ids = [w.product_id for w in Wishlist.query.filter_by(user_id=session['user_id']).all()]
    return render_template('home.html', featured_products=get_products(limit=4), wishlist_product_ids=wishlist_product_ids)

@app.route('/shop')
def shop():
    # Get filter and pagination parameters
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    brand = (request.args.get('brand', '') or '').strip()
    sort_by = request.args.get('sort_by', 'featured')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    if brand.lower() == 'all':
        brand = ''

    def normalize_brand_label(value):
        normalized = ' '.join((value or '').split())
        if not normalized:
            return ''
        if normalized.casefold() == 'h&m':
            return 'H&M'
        return normalized.title()

    raw_brand_values = [
        row[0]
        for row in (
            db.session.query(Product.brand)
            .filter(Product.brand.isnot(None))
            .filter(func.trim(Product.brand) != '')
            .distinct()
            .all()
        )
    ]

    brand_canonical_map = {}
    for raw_brand in raw_brand_values:
        key = ' '.join(raw_brand.split()).casefold()
        if key and key not in brand_canonical_map:
            brand_canonical_map[key] = normalize_brand_label(raw_brand)

    if brand:
        brand_key = ' '.join(brand.split()).casefold()
        brand = brand_canonical_map.get(brand_key, normalize_brand_label(brand))
    
    # Build query
    query = Product.query
    
    if search:
        query = query.filter(Product.product_name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if brand:
        query = query.filter(func.lower(func.trim(Product.brand)) == brand.casefold())
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.id.desc())
    else:  # featured
        query = query.order_by(Product.id.asc())
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = [product_to_dict(p) for p in pagination.items]
    
    categories = Category.query.all()
    available_brands = sorted(set(brand_canonical_map.values()), key=str.casefold)
    
    wishlist_product_ids = []
    if 'user_id' in session:
        wishlist_product_ids = [w.product_id for w in Wishlist.query.filter_by(user_id=session['user_id']).all()]
    
    return render_template('shop.html', 
                           products=products, 
                           categories=categories, 
                           available_brands=available_brands,
                           current_category=category_id, 
                           search=search, 
                           min_price=min_price, 
                           max_price=max_price,
                           brand=brand,
                           sort_by=sort_by,
                           pagination=pagination,
                           total_count=pagination.total,
                           wishlist_product_ids=wishlist_product_ids)

@app.route('/api/product/<int:product_id>')
def api_product_detail(product_id):
    """API endpoint for product details in JSON format"""
    product = get_product(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    return jsonify({
        'success': True,
        'product': product
    })

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return redirect(url_for('shop'))
    
    # Get any 3 other products for the related section
    all_products = get_products()
    related = [p for p in all_products if p['id'] != product_id][:4]
    
    wishlist_product_ids = []
    if 'user_id' in session:
        wishlist_product_ids = [w.product_id for w in Wishlist.query.filter_by(user_id=session['user_id']).all()]
        
    return render_template('product_detail.html', product=product, related_products=related, wishlist_product_ids=wishlist_product_ids)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    """Add product to cart - handles both form submission and AJAX"""
    from flask import flash
    
    # Check if user is logged in
    if not session.get('user_id'):
        flash('Please login first to add items to cart', 'warning')
        return redirect(url_for('login'))
    
    # Handle both form data and JSON
    if request.form:
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', 1, type=int)
        color = request.form.get('color', 'Default')
        size = request.form.get('size', 'Regular')
    else:
        data = request.get_json() or {}
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        color = data.get('color', 'Default')
        size = data.get('size', 'Regular')
    
    # Get product
    product = get_product(product_id)
    if not product:
        flash('Product not found', 'error')
        return redirect(request.referrer or url_for('shop'))
    
    # Initialize cart in session if not exists
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Check if identical product (same variation) already in cart
    existing_item = next((item for item in cart if item['id'] == product_id and item.get('color') == color and item.get('size') == size), None)
    if existing_item:
        existing_item['quantity'] += quantity
        flash(f'✅ Updated {product["name"]} quantity in cart!', 'success')
    else:
        cart.append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'image': product['image'],
            'quantity': quantity,
            'color': color,
            'size': size
        })
        flash(f'✅ Added {product["name"]} ({color}, {size}) to cart!', 'success')
    
    session['cart'] = cart
    session.modified = True
    
    # If JSON request, return JSON
    if request.is_json:
        return jsonify({'success': True, 'cart_count': len(cart)})
    
    # If form submission, redirect back
    return redirect(request.referrer or url_for('shop'))

@app.route('/get-cart-count', methods=['GET'])
def get_cart_count():
    """Get the current cart item count"""
    cart = session.get('cart', [])
    return jsonify({'cart_count': len(cart)})

@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    session['cart'] = cart
    session.modified = True
    return jsonify({'success': True})

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    session.modified = True
    return jsonify({'success': True})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    
    # Get user information if logged in
    user = None
    if session.get('user_id'):
        user = User.query.get(session.get('user_id'))
    
    if request.method == 'POST':
        # Just render the checkout form - no processing on POST yet
        return redirect(url_for('checkout'))
    
    return render_template('checkout.html', cart_items=cart_items, user=user)


@app.route('/checkout-confirm', methods=['POST'])
def checkout_confirm():
    """Validate form data and show confirmation page"""
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    
    # Validate required fields
    if not name:
        return render_template('checkout.html', cart_items=cart_items, error='Please enter your full name')
    if not email:
        return render_template('checkout.html', cart_items=cart_items, error='Please enter your email')
    if not phone:
        return render_template('checkout.html', cart_items=cart_items, error='Please enter your phone number')
    if not address:
        return render_template('checkout.html', cart_items=cart_items, error='Please enter your shipping address')
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Check for discount in session storage (passed from cart page)
    discount_amount = 0
    coupon_code = None
    
    # Store form data in session for the next step
    session['checkout_data'] = {
        'name': name,
        'email': email,
        'phone': phone,
        'address': address
    }
    session.modified = True
    
    return render_template('checkout_confirm.html', 
                         cart_items=cart_items,
                         name=name,
                         email=email,
                         phone=phone,
                         address=address,
                         subtotal=subtotal,
                         discount_amount=discount_amount,
                         coupon_code=coupon_code)


@app.route('/api/order-preview', methods=['POST'])
def api_order_preview():
    """API endpoint to get order preview data as JSON"""
    cart_items = session.get('cart', [])
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    
    # Validate required fields
    errors = []
    if not name:
        errors.append('Please enter your full name')
    if not email:
        errors.append('Please enter your email')
    if not phone:
        errors.append('Please enter your phone number')
    if not address:
        errors.append('Please enter your shipping address')
    
    if errors:
        return jsonify({'error': errors[0]}), 400
    
    if address and len(address) < 10:
        return jsonify({'error': 'Address must be at least 10 characters long'}), 400
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Store form data in session for the next step
    session['checkout_data'] = {
        'name': name,
        'email': email,
        'phone': phone,
        'address': address
    }
    session.modified = True
    
    return jsonify({
        'success': True,
        'items': cart_items,
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'subtotal': round(subtotal, 2),
        'shipping': 0,
        'total': round(subtotal, 2)
    })


@app.route('/place-order', methods=['POST'])
def place_order():
    """Create DB order first, then continue to Bakong static payment page."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    checkout_data = session.get('checkout_data', {})
    
    if not cart_items or not checkout_data:
        return redirect(url_for('checkout'))
    
    name = checkout_data.get('name')
    email = checkout_data.get('email')
    phone = checkout_data.get('phone')
    address = checkout_data.get('address')
    
    # Generate unique order number
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Calculate order total
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

    # Backward compatibility for legacy order schema that requires single-item columns.
    first_item = cart_items[0]
    legacy_product_id = first_item.get('id')
    legacy_quantity = int(first_item.get('quantity', 1))
    legacy_price = float(first_item.get('price', 0))
    legacy_total = subtotal
    legacy_product_name = first_item.get('name')

    try:
        # Persist order immediately with pending payment for static Bakong flow.
        order = Order(
            order_number=order_number,
            user_id=user_id,
            product_id=legacy_product_id,
            product_name=legacy_product_name,
            quantity=legacy_quantity,
            price=legacy_price,
            total_price=legacy_total,
            subtotal=subtotal,
            discount_amount=0,
            tax_amount=0,
            shipping_cost=0,
            grand_total=subtotal,
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            billing_address=address,
            shipping_address=address,
            shipping_method='standard',
            payment_method='bakong_static',
            payment_status='pending',
            status='pending_payment',
            order_date=datetime.utcnow()
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            product_id = item.get('id')
            product = Product.query.get(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")

            quantity = int(item.get('quantity', 1))
            unit_price = float(item.get('price', 0))
            line_total = unit_price * quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=line_total
            )
            db.session.add(order_item)

            if product.stock is not None:
                product.stock = max(0, product.stock - quantity)

        payment = Payment(
            order_id=order.id,
            amount=subtotal,
            payment_method='bakong_static',
            payment_status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Order creation error: {e}")
        return render_template('checkout.html', cart_items=cart_items, error='Unable to create order. Please try again.')

    # Store order number in session for success page
    session['order_number'] = order_number
    session['pending_order_db_id'] = order.id
    session.modified = True
    
    # Store order data in session for Bakong payment processing
    session['pending_order'] = {
        'order_id': order.id,
        'order_number': order_number,
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'items': cart_items,
        'total': subtotal
    }
    session.modified = True

    # Clear cart once order is safely persisted.
    session['cart'] = []
    session.modified = True
    
    # Redirect to Bakong payment page (to be implemented)
    return redirect(url_for('bakong_payment'))

@app.route('/bakong-payment')
def bakong_payment():
    """Bakong payment page - display QR code for scanning"""
    pending_order = session.get('pending_order')
    
    if not pending_order:
        return redirect(url_for('checkout'))
    
    order_number = pending_order.get('order_number', 'ORD-UNKNOWN')
    total = pending_order.get('total', 0)
    
    print(f"\n{'='*60}")
    print(f"BAKONG PAYMENT PAGE - Order: {order_number}, Total: {total}")
    print(f"{'='*60}\n")
    
    # Just pass order details - QR will be generated dynamically via /bakong-qr endpoint
    return render_template('bakong_payment.html', 
                         order=pending_order,
                         order_number=order_number,
                         total=total)

@app.route('/bakong-qr')
def bakong_qr():
    """Generate Bakong KHQR QR code image dynamically"""
    pending_order = session.get('pending_order')
    
    if not pending_order:
        return "No pending order", 400
    
    order_number = pending_order.get('order_number', 'ORD-UNKNOWN')
    total = pending_order.get('total', 0)
    
    # Your Bakong KHQR credentials
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiYTQ2ZGFkMWQzZDJkNGNhYSJ9LCJpYXQiOjE3NzY5MzM5MTAsImV4cCI6MTc4NDcwOTkxMH0.56gab7xcBP4AHoS9myh2CulN3sEq7tTilF7mMkHIn-Y'
    
    try:
        print(f"\n[QR GENERATION]")
        print(f"  Order: {order_number}")
        print(f"  Amount: ៛{total:,.0f}")
        
        # Initialize KHQR with Seyha Neat's credentials
        khqr = KHQR(token)
        print(f"  ✓ KHQR initialized")
        
        # Create QR data for this transaction
        qr_data = khqr.create_qr(
            bank_account='seyha_neat@aclb',
            merchant_name='Seyha Neat',
            merchant_city='Phnom Penh',
            amount=float(total),
            currency='KHR',
            phone_number='0719171737',
            bill_number=order_number,
            static=False,
            expiration=2
        )
        
        print(f"  ✓ QR data created: {qr_data[:30]}...")
        
        # Generate styled KHQR image (returns PNG bytes)
        image_data = khqr.qr_image(qr_data, format='png')
        
        print(f"  ✓ QR image generated ({len(image_data)} bytes)")
        
        # Store in session for payment verification
        session['qr_data'] = qr_data
        session['qr_timestamp'] = datetime.now().isoformat()
        session.modified = True
        
        # Return PNG image directly
        return send_file(
            io.BytesIO(image_data),
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        print(f"  ✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: Generate simple QR code
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f"{order_number}:{total}")
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to PNG bytes
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            
            print(f"  ✓ Fallback QR generated")
            
            return send_file(
                img_io,
                mimetype='image/png',
                as_attachment=False
            )
        except Exception as fallback_error:
            print(f"  ✗ Fallback failed: {fallback_error}")
            return "Could not generate QR code", 500

@app.route('/check-bakong-payment')
def check_bakong_payment():
    """Check Bakong payment status using YOUR account"""
    
    # Get QR data from session (generated when QR endpoint was accessed)
    qr_data = session.get('qr_data')
    
    print(f"\n[PAYMENT CHECK]")
    print(f"  QR Data from session: {'Found' if qr_data else 'NOT FOUND'}")
    
    if not qr_data:
        print(f"  ✗ No QR data in session")
        return 'UNPAID'
    
    try:
        # Use YOUR Bakong token (Seyha Neat)
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiYTQ2ZGFkMWQzZDJkNGNhYSJ9LCJpYXQiOjE3NzY5MzM5MTAsImV4cCI6MTc4NDcwOTkxMH0.56gab7xcBP4AHoS9myh2CulN3sEq7tTilF7mMkHIn-Y'
        khqr = KHQR(token)
        
        print(f"  ✓ KHQR initialized")
        
        # Generate MD5 hash
        md5 = khqr.generate_md5(qr_data)
        print(f"  ✓ MD5 hash: {md5}")
        
        # Check payment status
        print(f"  Checking payment status...")
        payment_status = khqr.check_payment(md5)
        
        print(f"  ✓ Status response: {payment_status}")
        return payment_status
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 'UNPAID'


@app.route('/api/bakong/confirm-payment', methods=['POST'])
def confirm_bakong_payment():
    """Customer confirms transfer for static Bakong; move order to verification queue."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    pending_order = session.get('pending_order', {})
    order_id = pending_order.get('order_id') or session.get('pending_order_db_id')
    if not order_id:
        return jsonify({'success': False, 'message': 'No pending order found'}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    if order.user_id != session.get('user_id'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    payment = Payment.query.filter_by(order_id=order.id).first()

    order.payment_status = 'pending_verification'
    order.status = 'pending_verification'
    if payment:
        payment.payment_status = 'pending_verification'

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Payment marked as pending verification',
        'order_number': order.order_number
    })


@app.route('/admin/api/orders/<int:order_id>/verify-bakong', methods=['POST'])
def admin_verify_bakong_payment(order_id):
    """Admin confirms or rejects static Bakong payment."""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403

    payload = request.get_json(silent=True) or {}
    approved = bool(payload.get('approved', True))

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    payment = Payment.query.filter_by(order_id=order.id).first()

    if approved:
        order.payment_status = 'completed'
        order.status = 'confirmed'
        if payment:
            payment.payment_status = 'completed'
    else:
        order.payment_status = 'failed'
        order.status = 'payment_failed'
        if payment:
            payment.payment_status = 'failed'

    db.session.commit()
    return jsonify({'success': True, 'approved': approved, 'order_number': order.order_number})

@app.route('/order-success')
def order_success():
    order_number = session.get('order_number', 'ORD-UNKNOWN')
    pending_order = session.get('pending_order', {}) or {}
    payment_pending = bool(pending_order)
    customer_name = pending_order.get('name')
    customer_phone = pending_order.get('phone')
    customer_address = pending_order.get('address')
    order_items = pending_order.get('items', [])
    order_total = pending_order.get('total', 0)

    session['cart'] = []
    session.pop('checkout_data', None)
    session.pop('pending_order', None)
    session.pop('pending_order_db_id', None)
    session.pop('qr_data', None)
    session.pop('qr_timestamp', None)
    session.modified = True
    return render_template(
        'order_success.html',
        order_number=order_number,
        payment_pending=payment_pending,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        order_items=order_items,
        order_total=order_total
    )

@app.route('/api/orders/<order_id>/update-status', methods=['POST'])
def update_order_status(order_id):
    """API endpoint to update order status (admin only)"""
    # Check if user is admin
    if session.get('user_role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        new_status = data.get('status', '').lower()
        new_payment_status = data.get('payment_status', '').lower()
        notes = data.get('notes', '')
        
        # Valid statuses
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', '']
        valid_payment_statuses = ['pending', 'paid', 'refunded', 'failed', '']
        
        if new_status and new_status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid order status'}), 400
        
        if new_payment_status and new_payment_status not in valid_payment_statuses:
            return jsonify({'success': False, 'message': 'Invalid payment status'}), 400
        
        # Find order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Update statuses
        if new_status:
            order.status = new_status
        if new_payment_status:
            order.payment_status = new_payment_status
        
        # Add notes if provided
        if notes and hasattr(order, 'notes'):
            order.notes = notes
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order status updated successfully',
            'order_id': order_id,
            'status': new_status
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order status: {e}")
        return jsonify({'success': False, 'message': 'Failed to update order status'}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
            
        return redirect(url_for('login', error=1))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if email and password and name:
            # Check if user already exists
            existing = User.query.filter_by(email=email).first()
            if not existing:
                new_user = User(username=name, email=email, role='customer')
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                
                session['user_id'] = new_user.id
                return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            return redirect(url_for('login', reset_success=1))
        else:
            return render_template('reset_password.html', error="Email not found in our system.")
    return render_template('reset_password.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_phone = request.form.get('phone')
        
        # Update name
        if new_name:
            user.username = new_name
        
        # Update phone number
        if new_phone is not None:
            user.phone = new_phone
        
        db.session.commit()
        return redirect(url_for('profile', success=1))
    
    # Fetch user's orders
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.order_date.desc()).all()
    
    # Fetch user's wishlist
    wishlist = Wishlist.query.filter_by(user_id=user.id).order_by(Wishlist.added_date.desc()).all()
            
    return render_template('profile.html', user=user, orders=orders, wishlist=wishlist)

@app.route('/add-to-wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first to add items to wishlist', 'redirect': url_for('login')}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    product = get_product(product_id)
    
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    if existing:
        # Toggle: Remove from wishlist
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'success': True, 'action': 'removed', 'message': 'Removed from wishlist', 'wishlist_count': Wishlist.query.filter_by(user_id=session['user_id']).count()})
    
    # Add to wishlist
    wishlist_item = Wishlist(
        user_id=session['user_id'],
        product_id=product_id,
        product_name=product['name'],
        product_price=product['price'],
        product_image=product.get('image')
    )
    db.session.add(wishlist_item)
    db.session.commit()
    
    return jsonify({'success': True, 'action': 'added', 'message': 'Added to wishlist', 'wishlist_count': Wishlist.query.filter_by(user_id=session['user_id']).count()})

@app.route('/remove-from-wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    data = request.get_json()
    wishlist_id = data.get('wishlist_id')
    
    wishlist_item = Wishlist.query.filter_by(id=wishlist_id, user_id=session['user_id']).first()
    if not wishlist_item:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Removed from wishlist'})

@app.route('/add-rating', methods=['POST'])
def add_rating():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating')
    review = data.get('review', '')

    if not product_id or not rating:
        return jsonify({'success': False, 'message': 'Invalid input'}), 400

    if not (1 <= rating <= 5):
        return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400

    # Check if user already rated this product
    existing_rating = Rating.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()

    if existing_rating:
        existing_rating.rating = rating
        existing_rating.review = review
    else:
        new_rating = Rating(
            user_id=session['user_id'],
            product_id=product_id,
            rating=rating,
            review=review,
            verified_purchase=True
        )
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Rating saved successfully'})

@app.route('/get-ratings/<int:product_id>')
def get_ratings(product_id):
    ratings = Rating.query.filter_by(product_id=product_id).all()
    if not ratings:
        avg_rating = 0
        count = 0
    else:
        avg_rating = sum(r.rating for r in ratings) / len(ratings)
        count = len(ratings)

    return jsonify({
        'average_rating': round(avg_rating, 1),
        'total_reviews': count,
        'ratings': [r.to_dict() for r in ratings]
    })

@app.route('/logout_customer')
def logout_customer():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        notifier = TelegramNotifier()
        contact_data = {
            'name': name,
            'email': email,
            'phone': 'N/A',
            'address': f'Contact Message: {message}',
            'items': []
        }
        notifier.send_order(contact_data)
        return render_template('contact.html', success=True)
    return render_template('contact.html')

# ===== API ROUTES FOR FRONTEND =====

@app.route('/api/products', methods=['GET'])
def api_products():
    """Get all products with optional filtering"""
    try:
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sort_by = request.args.get('sort_by', 'featured')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        query = Product.query
        
        if search:
            query = query.filter(Product.product_name.ilike(f'%{search}%'))
        if category_id:
            query = query.filter_by(category_id=category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if sort_by == 'price_low':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Product.price.desc())
        elif sort_by == 'newest':
            query = query.order_by(Product.id.desc())
        else:
            query = query.order_by(Product.id.asc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        products = [product_to_dict(p) for p in pagination.items]
        
        return jsonify({
            'success': True,
            'products': products,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def api_categories():
    """Get all product categories"""
    try:
        categories = Category.query.all()
        return jsonify({
            'success': True,
            'categories': [{
                'id': c.id,
                'name': c.category_name,
                'description': c.description or '',
                'image': c.image or ''
            } for c in categories]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    """Get current cart from session"""
    try:
        cart = session.get('cart', [])
        total = sum(item['price'] * item['quantity'] for item in cart)
        return jsonify({
            'success': True,
            'cart': cart,
            'total': round(total, 2),
            'count': len(cart)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cart/add', methods=['POST'])
def api_add_to_cart():
    """API endpoint to add product to cart"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        product = get_product(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        if 'cart' not in session:
            session['cart'] = []
        
        cart = session['cart']
        existing = next((item for item in cart if item['id'] == product_id), None)
        
        if existing:
            existing['quantity'] += quantity
        else:
            cart.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity
            })
        
        session['cart'] = cart
        session.modified = True
        
        total = sum(item['price'] * item['quantity'] for item in cart)
        return jsonify({
            'success': True,
            'message': 'Product added to cart',
            'cart_count': len(cart),
            'total': round(total, 2)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def api_search():
    """Search products by name or description"""
    try:
        query_string = request.args.get('q', '')
        if not query_string or len(query_string) < 2:
            return jsonify({'success': True, 'results': []})
        
        products = Product.query.filter(
            Product.product_name.ilike(f'%{query_string}%') |
            Product.description.ilike(f'%{query_string}%')
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'results': [product_to_dict(p) for p in products]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

try:
    from routes.admin.auth import auth_bp
    from routes.admin.dashboard import dashboard_bp
    from routes.admin.product import product_bp
    from routes.admin.order import admin_bp as order_bp
    from routes.admin.customer import admin_bp as customer_bp
    from routes.admin.analytics import admin_bp as analytics_bp
    from routes.admin.category import admin_bp as category_bp
    from routes.admin.rating import rating_bp
    from routes.admin.setting import admin_bp as settings_bp
    from routes.admin.user import user_bp
    
    # Enhanced dashboard modules
    from routes.admin.dashboard_alerts import alerts_bp
    from routes.admin.dashboard_kpi import kpi_bp
    from routes.admin.dashboard_inventory_sales import inventory_sales_bp
    from routes.admin.dashboard_customer_analytics import analytics_export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(rating_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(user_bp)
    
    # Register enhanced dashboard blueprints
    app.register_blueprint(alerts_bp)
    app.register_blueprint(kpi_bp)
    app.register_blueprint(inventory_sales_bp)
    app.register_blueprint(analytics_export_bp)
    
    print("[OK] Admin & Dashboard routes loaded with enhancements")
except Exception as e:
    print(f'Failed to load admin auth/dashboard routes: {e}')

# ============ REGISTER MAIN ROUTES ============
try:
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.order import order_bp
    from routes.address import address_bp
    from routes.wishlist import wishlist_bp
    from routes.reviews import review_bp
    from routes.coupons import coupon_bp
    from routes.user_profile import profile_bp
    from routes.recommendations import recommend_bp
    
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(address_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(coupon_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(recommend_bp)
    
    print("[OK] Main shopping routes loaded successfully (cart, checkout, order, address, wishlist, review, coupon, profile, recommend)")
except Exception as e:
    print(f"[ERROR] Failed to load main routes: {e}")

@app.route('/admin')
@app.route('/admin/')
def admin_index():
    return redirect('/admin/login')

if __name__ == '__main__':
    import os
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
