#!/usr/bin/env python3
"""
Render Deployment Helper
Run this script after deploying to Render to initialize the database.
"""

import os
import sys
from app import app, db
from model import init_models

def init_database():
    """Initialize the database for production."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database initialized successfully!")

        # Initialize models if needed
        Product, Category, User, Order, Wishlist, Rating, CartItem, OrderItem, Payment, Address, Shipping, Coupon, Brand = init_models(db)

        print("All models initialized!")

if __name__ == "__main__":
    init_database()