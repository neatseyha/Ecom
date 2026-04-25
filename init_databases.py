#!/usr/bin/env python
"""Properly initialize databases using Flask app context."""

import sys
import os

# Change to root directory
root_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_dir)

print("=" * 60)
print("INITIALIZING DATABASES WITH PROPER FLASK CONTEXT")
print("=" * 60)

# Initialize main app
print("\n[1/2] Main app database...")
from app import app, db

with app.app_context():
    # Create all tables
    db.create_all()
    print(f"✓ Created tables in: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Check what was created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"  Tables created: {len(tables)}")
    for table in sorted(tables):
        cols = len(inspector.get_columns(table))
        print(f"    - {table} ({cols} columns)")

# Initialize dashboard app
print("\n[2/2] Dashboard app database...")
os.chdir('dashboard-main')
sys.path.insert(0, os.getcwd())

# Import and initialize dashboard app
import importlib.util
spec = importlib.util.spec_from_file_location("dashboard_app", "app.py")
dashboard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard_module)

dashboard_app = dashboard_module.app
dashboard_db = dashboard_module.db

with dashboard_app.app_context():
    dashboard_db.create_all()
    print(f"✓ Created tables in: {dashboard_app.config['SQLALCHEMY_DATABASE_URI']}")
    
    from sqlalchemy import inspect
    inspector = inspect(dashboard_db.engine)
    tables = inspector.get_table_names()
    print(f"  Tables created: {len(tables)}")
    for table in sorted(tables):
        cols = len(inspector.get_columns(table))
        print(f"    - {table} ({cols} columns)")

print("\n" + "=" * 60)
print("✓ DATABASES INITIALIZED SUCCESSFULLY")
print("=" * 60)
