# Configuration settings for TestMasterProject
import os
from datetime import timedelta

class Config:
    # Basic settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-2024'
    DEBUG = os.environ.get('DEBUG') or True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///testmaster.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # API settings
    API_PREFIX = '/api/v1'
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # Learning path settings
    DEFAULT_LEARNING_PATH = 'beginner-python'
    SUPPORTED_LANGUAGES = ['python', 'javascript', 'java', 'csharp']

# Development configuration
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

# Production configuration  
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

# Testing configuration
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}