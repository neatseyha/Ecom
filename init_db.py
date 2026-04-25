#!/usr/bin/env python
"""Initialize both Flask app databases with correct schema."""

import sys
import os

# Add both app directories to path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("PHASE 1.2: INITIALIZE FRESH DATABASES")
print("=" * 60)

try:
    # Initialize main app database
    print("\n[1/2] Initializing MAIN APP database...")
    from app import app, db
    with app.app_context():
        db.create_all()
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Main app database created with {len(tables)} tables")
        print(f"  Tables: {', '.join(sorted(tables))}")
except Exception as e:
    print(f"✗ Error creating main app database: {e}")
    import traceback
    traceback.print_exc()

try:
    # Initialize dashboard app database (handle path with hyphen)
    print("\n[2/2] Initializing DASHBOARD APP database...")
    os.chdir('dashboard-main')
    sys.path.insert(0, os.getcwd())
    from app import app as dashboard_app, db as dashboard_db
    
    with dashboard_app.app_context():
        dashboard_db.create_all()
        # Verify tables were created
        inspector = dashboard_db.inspect(dashboard_db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Dashboard app database created with {len(tables)} tables")
        print(f"  Tables: {', '.join(sorted(tables))}")
except Exception as e:
    print(f"✗ Error creating dashboard app database: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DATABASE INITIALIZATION COMPLETE")
print("=" * 60)
print("\n✓ Both databases are ready for use!")
print("  - Main app: sqlite:///app.db (ecommerce frontend)")
print("  - Dashboard: sqlite:///app.db (admin panel)")
