import os
from datetime import timedelta
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    
    # SMART DATABASE URL
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # On Render: Use PostgreSQL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Local: Use SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///tech_booking.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    BCRYPT_LOG_ROUNDS = 12
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')