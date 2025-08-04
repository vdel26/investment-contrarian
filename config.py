"""
Configuration module for environment-specific settings.
"""

import os
from pathlib import Path

# Environment variables
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
IS_PRODUCTION = FLASK_ENV == 'production'

# Base directory - handle production vs development
# Check for Render mounted disk (could be ./data or /data)
render_data_paths = [Path('./data'), Path('/data')]
mounted_data_path = None

for data_path in render_data_paths:
    if data_path.exists() and os.access(data_path, os.W_OK):
        mounted_data_path = data_path
        break

if mounted_data_path is not None:
    # Production: use mounted disk
    BASE_DIR = mounted_data_path
    DATA_DIR = BASE_DIR
    CACHE_DIR = BASE_DIR / "cache"
    LOGS_DIR = BASE_DIR / "logs"
    EMAIL_TEMPLATES_DIR = Path.cwd() / "email_templates"  # Templates stay in app directory
    print(f"Using mounted disk at: {mounted_data_path}")
else:
    # Development: use current working directory
    BASE_DIR = Path.cwd()
    CACHE_DIR = BASE_DIR / "cache"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    EMAIL_TEMPLATES_DIR = BASE_DIR / "email_templates"
    print(f"Using development paths in: {BASE_DIR}")

# Ensure directories exist
CACHE_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File paths
SUBSCRIBERS_FILE = DATA_DIR / "subscribers.json"
FNG_CACHE_FILE = CACHE_DIR / "fng_cache.json"
AAII_CACHE_FILE = CACHE_DIR / "aaii_cache.json"
SSI_CACHE_FILE = CACHE_DIR / "ssi_cache.json"
OVERALL_CACHE_FILE = CACHE_DIR / "overall_cache.json"

# API Keys (required in production)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL')
FROM_NAME = os.environ.get('FROM_NAME', 'Market Sentiment Terminal')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')

# URLs (will be updated for production)
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:5001')
UNSUBSCRIBE_URL = f"{DASHBOARD_URL}/unsubscribe"

def validate_production_config():
    """Validate that all required environment variables are set for production."""
    if not IS_PRODUCTION:
        return True
    
    required_vars = [
        ('OPENAI_API_KEY', OPENAI_API_KEY),
        ('SERPAPI_KEY', SERPAPI_KEY),
        ('RESEND_API_KEY', RESEND_API_KEY),
        ('FROM_EMAIL', FROM_EMAIL),
    ]
    
    missing_vars = [name for name, value in required_vars if not value]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables for production: {', '.join(missing_vars)}")
    
    return True