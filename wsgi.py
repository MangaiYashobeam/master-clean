"""
🚀 WSGI Entry Point for Gunicorn - BioTrack Production
========================================================
This file serves as the entry point for Gunicorn in production.
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set environment variables for VPS mode
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('CAMERA_MODE', 'vps')  # VPS mode by default in production
os.environ.setdefault('SECRET_KEY', 'biotrack-production-secret-key-change-me-2025')

# Import and create the Flask application
from app.app import create_app

# Create the application instance
app = create_app(os.getenv("FLASK_CONFIG", "production"))

if __name__ == '__main__':
    # For local testing only
    app.run(host='0.0.0.0', port=5000, debug=False)
