"""Flask app initialization."""
from flask import Flask, send_from_directory
from flask_cors import CORS
import os


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load config
    app.config['DEV_MODE'] = os.getenv('DEV_MODE', 'true').lower() == 'true'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

    # Enable CORS for development
    CORS(app)

    # Register blueprints
    from app.routes import upload, posts, admin, users
    app.register_blueprint(upload.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(users.bp)

    # Serve uploaded files from nested structure
    from app.config import POSTS_DIR

    @app.route('/uploads/posts/<path:filepath>')
    def serve_posts(filepath):
        """
        Serve post files from nested structure.
        Supports paths like: YYYY/MM/post_N/files.zip or YYYY/MM/post_N/screenshot_0.png
        """
        return send_from_directory(POSTS_DIR, filepath)

    # Initialize database
    from app.services import database
    database.init_db()

    # Seed dev user if in dev mode
    if app.config['DEV_MODE']:
        database.seed_dev_user()

    # Cleanup old temp files on startup
    from app.services import storage
    storage.cleanup_old_temp_files()

    return app
