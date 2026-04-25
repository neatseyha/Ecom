from flask import Blueprint, current_app, redirect, render_template, request, url_for


admin_bp = Blueprint('category_module', __name__, url_prefix='')


@admin_bp.route('/categories', methods=['GET'])
def categories_route():
    from routes.admin.auth import login_required

    @login_required
    def _categories():
        db = current_app.extensions['sqlalchemy']
        Category = current_app.category_model_class

        categories = db.session.execute(db.select(Category).order_by(Category.category_name)).scalars().all()
        categories_list = []
        for c in categories:
            categories_list.append({
                'id': c.id,
                'category_name': c.category_name,
                'description': c.description,
                'product_count': len(c.products) if hasattr(c, 'products') else 0,
            })
        return render_template('dashboard/categories.html', categories=categories_list, module_name='Category Management', module_icon='fa-list')

    return _categories()


@admin_bp.route('/categories/add', methods=['POST'])
def add_category():
    db = current_app.extensions['sqlalchemy']
    Category = current_app.category_model_class
    name = request.form.get('category_name')
    description = request.form.get('description')

    if not name:
        return redirect(url_for('category_module.categories_route', message='Category name is required', type='error'))

    existing = db.session.execute(db.select(Category).filter_by(category_name=name)).scalar_one_or_none()
    if existing:
        return redirect(url_for('category_module.categories_route', message='Category with this name already exists', type='info'))

    category = Category(category_name=name, description=description)
    db.session.add(category)
    db.session.commit()
    return redirect(url_for('category_module.categories_route', message='Category added successfully', type='success'))


@admin_bp.route('/categories/edit/<int:category_id>', methods=['POST'])
def edit_category(category_id):
    db = current_app.extensions['sqlalchemy']
    Category = current_app.category_model_class

    category = db.session.get(Category, category_id)
    if not category:
        return redirect(url_for('category_module.categories_route', message='Category not found', type='error'))

    name = request.form.get('category_name')
    description = request.form.get('description')
    if not name:
        return redirect(url_for('category_module.categories_route', message='Category name is required', type='error'))

    existing = db.session.execute(db.select(Category).filter(Category.category_name == name, Category.id != category_id)).scalar_one_or_none()
    if existing:
        return redirect(url_for('category_module.categories_route', message='Another category with this name already exists', type='info'))

    category.category_name = name
    category.description = description
    db.session.commit()
    return redirect(url_for('category_module.categories_route', message='Category updated', type='success'))


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    db = current_app.extensions['sqlalchemy']
    Category = current_app.category_model_class

    category = db.session.get(Category, category_id)
    if not category:
        return redirect(url_for('category_module.categories_route', message='Category not found', type='error'))

    if hasattr(category, 'products') and len(category.products) > 0:
        return redirect(url_for('category_module.categories_route', message='Cannot delete category with products. Remove products first.', type='error'))

    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('category_module.categories_route', message='Category deleted', type='success'))
