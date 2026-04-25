# Quick API Reference Guide

## Authentication Required Routes
All routes below require user to be logged in (session['user_id'] must be set)

---

## Wishlist API

### View Wishlist
```
GET /wishlist/
Response: HTML page with wishlist items
```

### Add to Wishlist
```
POST /wishlist/add
Body: {
    "product_id": 123,
    "priority": "high|medium|low",  // optional
    "notes": "string",               // optional
    "category_type": "favorites|watch-later|gift-ideas"  // optional
}
Response: {"success": true, "item_id": 1, "message": "Added to wishlist"}
```

### Remove from Wishlist
```
DELETE /wishlist/remove/<id>
Response: {"success": true, "message": "Removed from wishlist"}
```

### Update Wishlist Item
```
PUT /wishlist/update/<id>
Body: {
    "priority": "high",
    "notes": "updated notes",
    "is_price_watch_enabled": true,
    "target_price": 49.99
}
Response: {"success": true, "message": "Wishlist item updated"}
```

### Move to Cart
```
POST /wishlist/to-cart/<id>
Response: Redirects to cart or {"success": true}
```

### Get Wishlist Count
```
GET /wishlist/count
Response: {"count": 5}
```

### Clear Wishlist
```
DELETE /wishlist/clear
Response: {"success": true, "message": "Wishlist cleared"}
```

---

## Reviews API

### Submit Review
```
POST /review/submit
Body: {
    "product_id": 123,
    "rating": 4.5,                  // 1-5
    "review_title": "Great product!",
    "review": "Full review text here"
}
Response: {"success": true, "message": "Review submitted successfully"}
```

### Get Product Reviews
```
GET /review/product/<product_id>?sort_by=recent&page=1&per_page=10
Query params:
    sort_by: recent|helpful|rating_high|rating_low
    page: page number
    per_page: items per page
Response: {
    "success": true,
    "product_name": "...",
    "average_rating": 4.2,
    "total_reviews": 15,
    "reviews": [
        {
            "id": 1,
            "username": "john",
            "rating": 5,
            "review_title": "...",
            "review": "...",
            "created_at": "2024-01-15 10:30:00"
        }
    ]
}
```

### Delete Review
```
DELETE /review/delete/<review_id>
Response: {"success": true, "message": "Review deleted successfully"}
```

### Mark Helpful
```
POST /review/<review_id>/helpful
Body: {"is_helpful": true|false}
Response: {"success": true, "helpful_yes_count": 10, "helpful_no_count": 2}
```

### Get Rating Distribution
```
GET /review/distribution/<product_id>
Response: {
    "success": true,
    "average_rating": 4.2,
    "total_reviews": 15,
    "distribution": {"1": 1, "2": 0, "3": 2, "4": 5, "5": 7},
    "percentages": {"1": 6.7, "2": 0, "3": 13.3, "4": 33.3, "5": 46.7}
}
```

### Get User Reviews
```
GET /review/user
Response: {
    "success": true,
    "total_reviews": 3,
    "reviews": [...]
}
```

---

## Coupon API

### Validate Coupon
```
POST /coupon/validate
Body: {
    "code": "SAVE20",
    "cart_total": 100.00
}
Response: {
    "success": true,
    "code": "SAVE20",
    "discount_type": "percentage|fixed",
    "discount_value": 20,
    "discount_amount": 20.00,
    "final_total": 80.00
}
```

### Apply Coupon
```
POST /coupon/apply
Body: {
    "code": "SAVE20",
    "cart_total": 100.00
}
Response: Same as validate + coupon applied
```

### Get Active Coupons
```
GET /coupon/active
Response: {
    "success": true,
    "total_coupons": 5,
    "coupons": [
        {
            "code": "SAVE20",
            "discount_type": "percentage",
            "discount_value": 20,
            "min_purchase": 50.00,
            "expires_at": "2024-12-31 23:59:59"
        }
    ]
}
```

### Create Coupon (Admin)
```
POST /coupon/create
Body: {
    "code": "SUMMER50",
    "discount_percentage": 50,  // OR discount_amount
    "max_uses": 100,
    "min_purchase": 25.00,
    "start_date": "2024-06-01T00:00:00",
    "end_date": "2024-08-31T23:59:59",
    "is_active": true
}
```

---

## Profile API

### Get Profile
```
GET /profile/
Response: HTML profile page

GET /profile/data
Response: {
    "success": true,
    "user": {
        "id": 1,
        "username": "john",
        "email": "john@example.com",
        "first_name": "John",
        "phone": "123-456-7890",
        "bio": "...",
        "created_at": "2024-01-01 12:00:00"
    }
}
```

### Update Profile
```
POST /profile/update
Body: {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "555-1234",
    "city": "New York",
    "bio": "Updated bio",
    "newsletter_subscribed": true
}
```

### Upload Profile Picture
```
POST /profile/picture/update
Body: form-data with 'profile_picture' file
Response: {
    "success": true,
    "picture_url": "/static/upload/profile_1_1234567890.jpg"
}
```

### Change Password
```
POST /profile/password/change
Body: {
    "current_password": "oldpass123",
    "new_password": "newpass123",
    "confirm_password": "newpass123"
}
```

### Delete Account
```
POST /profile/delete
Body: {
    "password": "mypassword",
    "confirm_delete": true
}
Response: {"success": true} + Session cleared
```

### Get Account Stats
```
GET /profile/stats
Response: {
    "success": true,
    "stats": {
        "total_orders": 10,
        "total_spent": 500.00,
        "wishlist_items": 5,
        "reviews_submitted": 3
    }
}
```

---

## Recommendations API

### Get Personalized Recommendations
```
GET /recommend/personalized?limit=10
Response: {
    "success": true,
    "type": "personalized",
    "total": 10,
    "products": [...]
}
```

### Get Trending Products
```
GET /recommend/trending?limit=10&period=30d
Query params:
    period: 7d|30d|90d|all
Response: {
    "success": true,
    "products": [
        {
            "id": 123,
            "name": "...",
            "sales_in_period": 50
        }
    ]
}
```

### Get Similar Products
```
GET /recommend/similar/<product_id>?limit=10
```

### Get Featured Products
```
GET /recommend/featured?limit=10
```

### Get New Arrivals
```
GET /recommend/new-arrivals?limit=10&days=30
```

### Get On-Sale Products
```
GET /recommend/on-sale?limit=10
```

### Get Top-Rated Products
```
GET /recommend/top-rated?limit=10&min_reviews=5
```

---

## Order API

### Get Order Summary
```
GET /order/summary
Response: {
    "success": true,
    "summary": {
        "total_orders": 10,
        "total_spent": 500.00,
        "average_order_value": 50.00,
        "total_items_purchased": 25,
        "status_breakdown": {
            "pending": 1,
            "processing": 0,
            "shipped": 3,
            "delivered": 6,
            "cancelled": 0
        },
        "recent_orders": [...]
    }
}
```

### Reorder
```
POST /order/<order_id>/reorder
Response: Redirects to cart or {"success": true}
```

### Export Orders as CSV
```
GET /order/export/csv
Response: Downloads CSV file with order history
```

### Get Order Details (API)
```
GET /order/api/<order_id>
Response: {
    "success": true,
    "order": {
        "id": 123,
        "order_number": "ORD-001",
        "items": [...],
        "shipping": {...},
        "payment": {...}
    }
}
```

---

## Enhanced Search & Filter

### Shop Page Filters
```
GET /shop?search=laptop&category_id=5&min_price=100&max_price=500&sort_by=price_asc&page=1
Query params:
    search: product name/description/brand
    category_id: category filter
    min_price: minimum price
    max_price: maximum price
    sort_by: featured|price_asc|price_desc|newest|rating|popular
    page: page number
    per_page: items per page (default 12)
```

### API Search
```
GET /api/search?q=laptop
Response: {
    "success": true,
    "results": [...]
}
```

---

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (not logged in)
- `403` - Forbidden (no permission)
- `404` - Not Found
- `409` - Conflict (already exists)
- `500` - Server Error

---

## Common Response Format

**Success:**
```json
{
    "success": true,
    "message": "Operation successful",
    "data": {...}
}
```

**Error:**
```json
{
    "success": false,
    "message": "Error description"
}
```
