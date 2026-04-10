#!/usr/bin/env python3
"""Update admin user is_admin field to True"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('FLASK_APP', 'backend.app:create_app')

try:
    from backend.models.models import User
    from backend.extensions import db
    from backend.app import create_app

    app = create_app()

    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("ERROR: User 'admin' not found in database!")
            print("Please check if the username is correct.")
            sys.exit(1)

        print(f"Before update: username={user.username}, is_admin={user.is_admin}")

        if user.is_admin:
            print("Already admin, no change needed.")
            sys.exit(0)

        user.is_admin = True
        db.session.commit()
        print(f"After update: username={user.username}, is_admin={user.is_admin}")
        print("\nSUCCESS: Admin permissions updated!")
        print("Now you can log in again and access the admin dashboard.")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
