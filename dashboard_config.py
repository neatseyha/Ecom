import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/upload')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

# Secret key for session signing — override in environment for production
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Session lifetime for "remember me" feature
from datetime import timedelta
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# Default UI theme and palette (use 'dark' or 'light' for DEFAULT_THEME)
DEFAULT_THEME = os.environ.get('DEFAULT_THEME', 'light')
DEFAULT_PALETTE = os.environ.get('DEFAULT_PALETTE', 'indigo')