#!/usr/bin/env python3
"""
Render Deployment Helper
Run this script after deploying to Render to initialize the database.
Usage: python render_init.py
"""

import os
import sys

# Add current directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db

    def init_database():
        """Initialize the database for production."""
        print("Starting database initialization...")

        with app.app_context():
            print("Creating database tables...")
            try:
                # Create all tables without redefining models
                db.create_all()
                print("✅ Database tables created successfully!")
            except Exception as e:
                print(f"❌ Error creating tables: {e}")
                return False

            # Test database connection
            try:
                db.session.execute(db.text('SELECT 1'))
                print("✅ Database connection test successful!")
            except Exception as e:
                print(f"❌ Database connection test failed: {e}")
                return False

        print("🎉 Database initialization completed successfully!")
        return True

    if __name__ == "__main__":
        success = init_database()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)