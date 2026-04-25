from flask import Blueprint, current_app, redirect, render_template, request, url_for
from sqlalchemy import text
import os


product_bp = Blueprint('product_module', __name__, url_prefix='')

UPLOAD_FOLDER = 'static/upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@product_bp.route('/products')
def products_route():
    from routes.admin.auth import login_required

    @login_required
    def _products():
        db = current_app.extensions['sqlalchemy']
        Product = current_app.product_model_class

        page = request.args.get('page', 1, type=int)
        per_page = 10
        search_query = request.args.get('search', '', type=str)

        rows = get_all_products_list(db)
        if search_query:
            query = search_query.lower()
            rows = [row for row in rows if query in str(row.get('product_name', '')).lower()]

        total = len(rows)
        start = (page - 1) * per_page
        end = start + per_page
        products = rows[start:end]
        total_pages = max(1, (total + per_page - 1) // per_page)

        return render_template(
            'dashboard/products.html',
            module_name='Products',
            module_icon='fa-boxes',
            module='products',
            products=products,
            page=page,
            total_pages=total_pages,
            total=total,
            search_query=search_query,
        )

    return _products()


@product_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    Category = current_app.category_model_class

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        category_id = request.form.get('category_id')
        price = request.form.get('price')
        stock = request.form.get('stock')
        status = request.form.get('status', 'instock')
        description = request.form.get('description')
        image_file = request.files.get('image')

        if not all([product_name, category_id, price, stock]):
            return redirect(url_for('product_module.add_product'))

        image_filename = handle_image_upload(image_file)
        new_product = Product(
            product_name=product_name,
            category_id=int(category_id),
            price=float(price),
            stock=int(stock),
            status=status,
            description=description,
            image=image_filename,
        )

        try:
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('product_module.products_route', message='Product created successfully!', type='success'))
        except Exception:
            db.session.rollback()
            return redirect(url_for('product_module.add_product', message='Error adding product', type='error'))

    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template('dashboard/products_action/add_product.html', module_name='Add Product', module_icon='fa-plus-circle', categories=categories)


@product_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class
    Category = current_app.category_model_class

    product = db.session.get(Product, product_id)
    if not product:
        return redirect(url_for('product_module.products_route'))

    if request.method == 'POST':
        product.product_name = request.form.get('product_name')
        product.category_id = int(request.form.get('category_id'))
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.status = request.form.get('status', 'instock')
        product.description = request.form.get('description')

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            delete_image_files(product.image)
            image_filename = handle_image_upload(image_file)
            if image_filename:
                product.image = image_filename

        try:
            db.session.commit()
            return redirect(url_for('product_module.products_route', message='Product updated successfully!', type='success'))
        except Exception:
            db.session.rollback()
            return redirect(url_for('product_module.edit_product', product_id=product_id, message='Error updating product', type='error'))

    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template('dashboard/products_action/edit_product.html', product=product, categories=categories, module_name='Edit Product', module_icon='fa-edit')


@product_bp.route('/products/delete/<int:product_id>', methods=['POST', 'GET'])
def delete_product(product_id):
    db = current_app.extensions['sqlalchemy']
    Product = current_app.product_model_class

    product = db.session.get(Product, product_id)
    if not product:
        return redirect(url_for('product_module.products_route'))

    delete_image_files(product.image)

    try:
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('product_module.products_route', message='Product deleted successfully!', type='success'))
    except Exception:
        db.session.rollback()
        return redirect(url_for('product_module.products_route', message='Error deleting product', type='error'))


def get_all_products_list(db):
    sql = text("SELECT p.*, c.category_name FROM product p INNER JOIN category c ON c.id = p.category_id")
    result = db.session.execute(sql).fetchall()
    return [dict(row._mapping) for row in result]


def handle_image_upload(image_file):
    from upload_service import save_image
    from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

    if not image_file or not image_file.filename or not allowed_file(image_file.filename):
        return None

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    try:
        images = save_image(image_file, UPLOAD_FOLDER, ALLOWED_EXTENSIONS)
        return images['original'] if isinstance(images, dict) else None
    except Exception as e:
        print(f'Image upload error: {e}')
        return None


def delete_image_files(image_filename):
    if not image_filename:
        return

    from config import UPLOAD_FOLDER

    name, ext = os.path.splitext(image_filename)
    for filename in [image_filename, f'resized_{name}{ext}', f'thumb_{name}{ext}']:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f'Could not delete {filename}: {e}')
