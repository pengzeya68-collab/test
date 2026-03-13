from app import create_app, db
from models import User

app = create_app()

# Test database connection and user creation
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created successfully!")
    
    # Test user creation
    try:
        from werkzeug.security import generate_password_hash
        
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        if test_user:
            print(f"Test user already exists: {test_user.username} ({test_user.email})")
        else:
            hashed_password = generate_password_hash('password123')
            new_user = User(
                username='testuser',
                email='test@example.com',
                password_hash=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            print(f"Test user created successfully: {new_user.username} ({new_user.email})")
            
        # List all users
        print("\nAll users in database:")
        users = User.query.all()
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Created: {user.created_at}")
            
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.session.rollback()

print("\nDatabase test completed!")
