from flask import Flask
from flask_cors import CORS
import os
from datetime import timedelta
from extensions import db, jwt, migrate, limiter

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///testmaster.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    # Debug mode
    app.debug = True
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    CORS(app)
    
    # Import and register blueprints
    print("🔄 Importing blueprints...")
    from auth import auth_bp
    from learning_paths import learning_bp
    from exercises import exercises_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(learning_bp, url_prefix='/api')
    app.register_blueprint(exercises_bp, url_prefix='/api')
    
    print("✅ All blueprints registered!")
    
    # Create tables
    with app.app_context():
        import models
        db.create_all()
    
    # Add root route
    @app.route('/')
    def home():
        return {
            'message': 'TestMaster API is running!',
            'endpoints': [
                'POST /api/register',
                'POST /api/login', 
                'GET /api/learning-paths',
                'GET /api/exercises'
            ]
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    print('🚀 TestMaster API starting on http://localhost:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)