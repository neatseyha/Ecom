from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from routes.admin.auth import login_required


rating_bp = Blueprint('rating_module', __name__, url_prefix='')


@rating_bp.route('/ratings')
def ratings_route():
    @login_required
    def _ratings():
        db = current_app.extensions['sqlalchemy']
        Rating = current_app.rating_model_class

        page = request.args.get('page', 1, type=int)
        per_page = 10

        try:
            ratings_query = db.session.query(Rating).paginate(page=page, per_page=per_page)
            ratings_list = []

            for rating in ratings_query.items:
                ratings_list.append({
                    'id': rating.id,
                    'product_id': rating.product_id,
                    'product_name': rating.product_name if hasattr(rating, 'product_name') else 'Product',
                    'user_id': rating.user_id,
                    'rating': rating.rating,
                    'review': rating.review[:100] if rating.review else 'No review text',
                    'verified': rating.verified_purchase if hasattr(rating, 'verified_purchase') else False,
                    'created_at': rating.created_at.strftime('%b %d, %Y') if hasattr(rating, 'created_at') and rating.created_at else 'N/A',
                })

            return render_template('dashboard/ratings.html', ratings=ratings_list, page=page, total_pages=ratings_query.pages, total=ratings_query.total, module_name='Product Ratings', module_icon='fa-star')
        except Exception as e:
            print(f'Error loading ratings: {e}')
            return render_template('dashboard/ratings.html', ratings=[], page=1, total_pages=1, total=0, module_name='Product Ratings', module_icon='fa-star')

    return _ratings()


@rating_bp.route('/ratings/delete/<int:rating_id>', methods=['POST'])
def delete_rating(rating_id):
    @login_required
    def _delete():
        db = current_app.extensions['sqlalchemy']
        Rating = current_app.rating_model_class

        try:
            rating = db.session.query(Rating).filter(Rating.id == rating_id).first()
            if rating:
                db.session.delete(rating)
                db.session.commit()
                return redirect(url_for('rating_module.ratings_route', message='Rating deleted successfully', type='success'))
            return redirect(url_for('rating_module.ratings_route', message='Rating not found', type='error'))
        except Exception:
            db.session.rollback()
            return redirect(url_for('rating_module.ratings_route', message='Error deleting rating', type='error'))

    return _delete()


@rating_bp.route('/ratings/stats')
def rating_stats():
    @login_required
    def _stats():
        db = current_app.extensions['sqlalchemy']
        Rating = current_app.rating_model_class

        try:
            total_ratings = db.session.query(Rating).count()
            avg_rating = 0
            if total_ratings > 0:
                ratings = db.session.query(Rating).all()
                avg_rating = sum(r.rating for r in ratings) / len(ratings)

            rating_dist = {
                '5_stars': db.session.query(Rating).filter(Rating.rating == 5).count(),
                '4_stars': db.session.query(Rating).filter(Rating.rating == 4).count(),
                '3_stars': db.session.query(Rating).filter(Rating.rating == 3).count(),
                '2_stars': db.session.query(Rating).filter(Rating.rating == 2).count(),
                '1_star': db.session.query(Rating).filter(Rating.rating == 1).count(),
            }

            return jsonify({'total_ratings': total_ratings, 'average_rating': round(avg_rating, 1), 'distribution': rating_dist})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return _stats()
