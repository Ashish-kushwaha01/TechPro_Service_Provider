import os
from datetime import timedelta
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL with proper parsing for Render"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres://'):
        # Render gives postgres://, but SQLAlchemy needs postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url or 'sqlite:///tech_booking.db'

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    
    # Database
    # SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tech_booking.db' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')