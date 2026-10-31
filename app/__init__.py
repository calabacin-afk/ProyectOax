from flask import Flask

from .config import Config


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    from .routes.health import health_bp
    from .routes.web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    return app
