"""
Product Review and Rating Routes
Submit, manage, and display product reviews
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from datetime import datetime
from sqlalchemy import func

review_bp = Blueprint('review', __name__, url_prefix='/review')

# ============ SUBMIT REVIEW ============
@review_bp.route('/submit', methods=['POST'])
def submit_review():
    """Submit a new review for a product"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json() if request.is_json else request.form
    product_id = data.get('product_id', type=int)
    rating = data.get('rating', type=float)
    review_title = data.get('review_title', '')
    review_text = data.get('review', '')
    
    if not product_id or not rating:
        return jsonify({'success': False, 'message': 'Product ID and rating are required'}), 400
    
    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
    
    Product = current_app.product_model_class
    Rating = current_app.rating_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    # Check if user already reviewed this product
    existing_review = db.session.query(Rating).filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.review_title = review_title
        existing_review.review = review_text
        existing_review.updated_at = datetime.utcnow()
        message = 'Review updated successfully'
    else:
        # Create new review
        new_review = Rating(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            review_title=review_title,
            review=review_text,
            status='approved',
            verified_purchase=True  # Can be updated based on order verification
        )
        db.session.add(new_review)
        message = 'Review submitted successfully'
    
    # Update product rating stats
    all_reviews = db.session.query(Rating).filter_by(product_id=product_id).all()
    if all_reviews:
        avg_rating = sum([r.rating for r in all_reviews]) / len(all_reviews)
        product.rating_avg = round(avg_rating, 2)
        product.review_count = len(all_reviews)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': message})

# ============ GET PRODUCT REVIEWS ============
@review_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    """Get all reviews for a product"""
    from app import db
    
    Product = current_app.product_model_class
    Rating = current_app.rating_model_class
    User = current_app.user_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    sort_by = request.args.get('sort_by', 'recent')  # recent, helpful, rating_high, rating_low
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = db.session.query(Rating).filter_by(
        product_id=product_id,
        status='approved'
    )
    
    # Apply sorting
    if sort_by == 'helpful':
        query = query.order_by((Rating.helpful_yes_count - Rating.helpful_no_count).desc())
    elif sort_by == 'rating_high':
        query = query.order_by(Rating.rating.desc())
    elif sort_by == 'rating_low':
        query = query.order_by(Rating.rating.asc())
    else:  # recent
        query = query.order_by(Rating.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    reviews_data = []
    for review in pagination.items:
        user = db.session.query(User).get(review.user_id)
        reviews_data.append({
            'id': review.id,
            'user_id': review.user_id,
            'username': user.username if user else 'Anonymous',
            'rating': review.rating,
            'review_title': review.review_title,
            'review': review.review,
            'helpful_yes_count': review.helpful_yes_count,
            'helpful_no_count': review.helpful_no_count,
            'verified_purchase': review.verified_purchase,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'images': review.images
        })
    
    return jsonify({
        'success': True,
        'product_id': product_id,
        'product_name': product.product_name,
        'average_rating': product.rating_avg,
        'total_reviews': product.review_count,
        'reviews': reviews_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })

# ============ DELETE REVIEW ============
@review_bp.route('/delete/<int:review_id>', methods=['POST', 'DELETE'])
def delete_review(review_id):
    """Delete a review (by reviewer or admin)"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Rating = current_app.rating_model_class
    User = current_app.user_model_class
    
    review = db.session.query(Rating).get(review_id)
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404
    
    user = db.session.query(User).get(user_id)
    is_admin = user.role == 'admin' if user else False
    
    # Only review owner or admin can delete
    if review.user_id != user_id and not is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    product_id = review.product_id
    db.session.delete(review)
    
    # Update product stats
    Product = current_app.product_model_class
    product = db.session.query(Product).get(product_id)
    remaining_reviews = db.session.query(Rating).filter_by(product_id=product_id).all()
    
    if remaining_reviews:
        avg_rating = sum([r.rating for r in remaining_reviews]) / len(remaining_reviews)
        product.rating_avg = round(avg_rating, 2)
        product.review_count = len(remaining_reviews)
    else:
        product.rating_avg = 0
        product.review_count = 0
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review deleted successfully'})

# ============ MARK HELPFUL ============
@review_bp.route('/<int:review_id>/helpful', methods=['POST'])
def mark_helpful(review_id):
    """Mark a review as helpful or not helpful"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    data = request.get_json()
    is_helpful = data.get('is_helpful', True)
    
    Rating = current_app.rating_model_class
    
    review = db.session.query(Rating).get(review_id)
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404
    
    if is_helpful:
        review.helpful_yes_count += 1
    else:
        review.helpful_no_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'helpful_yes_count': review.helpful_yes_count,
        'helpful_no_count': review.helpful_no_count
    })

# ============ GET RATING DISTRIBUTION ============
@review_bp.route('/distribution/<int:product_id>', methods=['GET'])
def get_rating_distribution(product_id):
    """Get distribution of ratings for a product"""
    from app import db
    
    Rating = current_app.rating_model_class
    Product = current_app.product_model_class
    
    product = db.session.query(Product).get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
    
    distribution = {}
    for i in range(1, 6):
        count = db.session.query(Rating).filter_by(
            product_id=product_id,
            rating=i,
            status='approved'
        ).count()
        distribution[i] = count
    
    total_reviews = sum(distribution.values())
    
    return jsonify({
        'success': True,
        'product_id': product_id,
        'average_rating': product.rating_avg,
        'total_reviews': total_reviews,
        'distribution': distribution,
        'percentages': {
            str(i): round((distribution[i] / total_reviews * 100), 1) if total_reviews > 0 else 0
            for i in range(1, 6)
        }
    })

# ============ GET USER REVIEWS ============
@review_bp.route('/user', methods=['GET'])
def get_user_reviews():
    """Get all reviews submitted by the current user"""
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    Rating = current_app.rating_model_class
    Product = current_app.product_model_class
    
    reviews = db.session.query(Rating).filter_by(user_id=user_id).all()
    
    reviews_data = []
    for review in reviews:
        product = db.session.query(Product).get(review.product_id)
        reviews_data.append({
            'id': review.id,
            'product_id': review.product_id,
            'product_name': product.product_name if product else 'Unknown',
            'rating': review.rating,
            'review_title': review.review_title,
            'review': review.review,
            'status': review.status,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': review.updated_at.strftime('%Y-%m-%d %H:%M:%S') if review.updated_at else None
        })
    
    return jsonify({
        'success': True,
        'total_reviews': len(reviews_data),
        'reviews': reviews_data
    })
