#!/usr/bin/env python
"""
Seed script to insert 5 records into each database table
Run with: python seed_data.py
"""

from app import app, db, User, Brand, Category, Product, Address, CartItem, Coupon, Order, OrderItem, Payment, Rating, Shipping, Wishlist
from datetime import datetime, timedelta


def seed_database():
    """Seed the database with sample data"""
    
    with app.app_context():
        # Clear existing data (optional - comment out to append)
        print("🗑️  Clearing existing data...")
        db.session.query(Wishlist).delete()
        db.session.query(CartItem).delete()
        db.session.query(Rating).delete()
        db.session.query(Shipping).delete()
        db.session.query(Payment).delete()
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(Coupon).delete()
        db.session.query(Address).delete()
        db.session.query(Product).delete()
        db.session.query(Category).delete()
        db.session.query(Brand).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        # 1. Create Users
        print("\n👥 Creating 5 Users...")
        users = []
        user_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'password': 'pass123', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'password': 'pass123', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'mike_johnson', 'email': 'mike@example.com', 'password': 'pass123', 'first_name': 'Mike', 'last_name': 'Johnson'},
            {'username': 'sarah_williams', 'email': 'sarah@example.com', 'password': 'pass123', 'first_name': 'Sarah', 'last_name': 'Williams'},
            {'username': 'david_brown', 'email': 'david@example.com', 'password': 'pass123', 'first_name': 'David', 'last_name': 'Brown'},
        ]
        
        for data in user_data:
            user = User(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone='555-000' + str(len(users)+1),
                gender='M' if len(users) % 2 == 0 else 'F',
                role='customer',
                is_active=True,
                city='New York',
                country='USA'
            )
            user.set_password(data['password'])
            users.append(user)
            db.session.add(user)
        db.session.commit()
        print(f"✅ Created {len(users)} users")
        
        # 2. Create Brands
        print("\n🏢 Creating 5 Brands...")
        brands = []
        brand_data = [
            {'name': 'Nike', 'slug': 'nike', 'description': 'Premium athletic brand'},
            {'name': 'Adidas', 'slug': 'adidas', 'description': 'Sports and lifestyle brand'},
            {'name': 'Gucci', 'slug': 'gucci', 'description': 'Luxury fashion brand'},
            {'name': 'Zara', 'slug': 'zara', 'description': 'Contemporary fashion brand'},
            {'name': 'H&M', 'slug': 'hm', 'description': 'Fast fashion brand'},
        ]
        
        for data in brand_data:
            brand = Brand(
                name=data['name'],
                slug=data['slug'],
                description=data['description'],
                is_active=True
            )
            brands.append(brand)
            db.session.add(brand)
        db.session.commit()
        print(f"✅ Created {len(brands)} brands")
        
        # 3. Create Categories
        print("\n📁 Creating 5 Categories...")
        categories = []
        category_data = [
            {'category_name': 'Men Tops', 'slug': 'men-tops', 'description': 'T-shirts and tops for men'},
            {'category_name': 'Women Dresses', 'slug': 'women-dresses', 'description': 'Dresses for women'},
            {'category_name': 'Shoes', 'slug': 'shoes', 'description': 'Footwear collection'},
            {'category_name': 'Accessories', 'slug': 'accessories', 'description': 'Bags, belts, and more'},
            {'category_name': 'Outerwear', 'slug': 'outerwear', 'description': 'Jackets and coats'},
        ]
        
        for data in category_data:
            category = Category(
                category_name=data['category_name'],
                slug=data['slug'],
                description=data['description'],
                status='active'
            )
            categories.append(category)
            db.session.add(category)
        db.session.commit()
        print(f"✅ Created {len(categories)} categories")
        
        # 4. Create Products
        print("\n🛍️  Creating 5 Products...")
        products = []
        product_data = [
            {'product_name': 'Premium White T-Shirt', 'brand': 'Nike', 'price': 29.99, 'stock': 100, 'category_id': categories[0].id},
            {'product_name': 'Elegant Black Dress', 'brand': 'Gucci', 'price': 149.99, 'stock': 50, 'category_id': categories[1].id},
            {'product_name': 'Running Shoes', 'brand': 'Adidas', 'price': 89.99, 'stock': 75, 'category_id': categories[2].id},
            {'product_name': 'Leather Handbag', 'brand': 'Gucci', 'price': 199.99, 'stock': 30, 'category_id': categories[3].id},
            {'product_name': 'Winter Jacket', 'brand': 'Zara', 'price': 119.99, 'stock': 45, 'category_id': categories[4].id},
        ]
        
        for data in product_data:
            product = Product(
                product_name=data['product_name'],
                sku=f"SKU-{len(products)+1}",
                brand=data['brand'],
                price=data['price'],
                stock=data['stock'],
                category_id=data['category_id'],
                color='Black',
                size='M',
                description=f"High-quality {data['product_name'].lower()}",
                status='instock'
            )
            products.append(product)
            db.session.add(product)
        db.session.commit()
        print(f"✅ Created {len(products)} products")
        
        # 5. Create Addresses
        print("\n📍 Creating 5 Addresses...")
        addresses = []
        address_data = [
            {'user_id': users[0].id, 'full_name': 'John Doe', 'street': '123 Main St', 'city': 'New York', 'zip': '10001'},
            {'user_id': users[1].id, 'full_name': 'Jane Smith', 'street': '456 Oak Ave', 'city': 'Los Angeles', 'zip': '90001'},
            {'user_id': users[2].id, 'full_name': 'Mike Johnson', 'street': '789 Pine Rd', 'city': 'Chicago', 'zip': '60601'},
            {'user_id': users[3].id, 'full_name': 'Sarah Williams', 'street': '321 Elm St', 'city': 'Houston', 'zip': '77001'},
            {'user_id': users[4].id, 'full_name': 'David Brown', 'street': '654 Cedar Ln', 'city': 'Phoenix', 'zip': '85001'},
        ]
        
        for data in address_data:
            address = Address(
                user_id=data['user_id'],
                full_name=data['full_name'],
                phone='555-1234',
                street_address=data['street'],
                city=data['city'],
                state='NY' if data['city'] == 'New York' else 'CA',
                zip_code=data['zip'],
                country='USA',
                type='shipping',
                is_default=True
            )
            addresses.append(address)
            db.session.add(address)
        db.session.commit()
        print(f"✅ Created {len(addresses)} addresses")
        
        # 6. Create Cart Items
        print("\n🛒 Creating 5 Cart Items...")
        cart_items = []
        for i in range(5):
            cart_item = CartItem(
                user_id=users[i].id,
                product_id=products[i].id,
                quantity=2,
                price=products[i].price,
                size='M',
                color='Black'
            )
            cart_items.append(cart_item)
            db.session.add(cart_item)
        db.session.commit()
        print(f"✅ Created {len(cart_items)} cart items")
        
        # 7. Create Coupons
        print("\n🎟️  Creating 5 Coupons...")
        coupons = []
        coupon_data = [
            {'code': 'SAVE10', 'discount': 10},
            {'code': 'SALE20', 'discount': 20},
            {'code': 'WELCOME15', 'discount': 15},
            {'code': 'FASHION25', 'discount': 25},
            {'code': 'SUMMER30', 'discount': 30},
        ]
        
        now = datetime.now()
        for data in coupon_data:
            coupon = Coupon(
                code=data['code'],
                discount_percentage=data['discount'],
                max_uses=100,
                min_purchase=50.0,
                start_date=now,
                end_date=now + timedelta(days=30),
                is_active=True
            )
            coupons.append(coupon)
            db.session.add(coupon)
        db.session.commit()
        print(f"✅ Created {len(coupons)} coupons")
        
        # Skip Order-related tables due to schema mismatch and create Ratings/Wishlists instead
        
        # 8. Create Ratings
        print("\n⭐ Creating 5 Ratings...")
        ratings = []
        for i in range(5):
            rating = Rating(
                user_id=users[i].id,
                product_id=products[i].id,
                rating=4.5,
                review_title=f"Great {products[i].product_name.lower()}!",
                review=f"This is an excellent product. Highly recommended!",
                status='approved',
                verified_purchase=True,
                helpful_count=5
            )
            ratings.append(rating)
            db.session.add(rating)
        db.session.commit()
        print(f"✅ Created {len(ratings)} ratings")
        
        # Skip Wishlist due to schema mismatch
        wishlists = []
        
        print("\n" + "="*50)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("\n📊 Summary:")
        print(f"   ✓ Users: {len(users)}")
        print(f"   ✓ Brands: {len(brands)}")
        print(f"   ✓ Categories: {len(categories)}")
        print(f"   ✓ Products: {len(products)}")
        print(f"   ✓ Addresses: {len(addresses)}")
        print(f"   ✓ Cart Items: {len(cart_items)}")
        print(f"   ✓ Coupons: {len(coupons)}")
        print(f"   ✓ Ratings: {len(ratings)}")
        print("\n⚠️  Skipped (Schema Mismatch):")
        print("   - Orders, OrderItems, Payments, Shipping")
        print("   - Wishlists (database has product_name, model does not)")
        print("\n🎉 Total Records Created: 40 (8 tables × 5 records)")
        print("="*50)


if __name__ == '__main__':
    seed_database()
