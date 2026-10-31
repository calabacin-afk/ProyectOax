from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    # The static prototype can run before a local database is configured.
    # Once DATABASE_URL is set, the same factory initializes SQLAlchemy/Migrate.
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        db.init_app(app)
        migrate.init_app(app, db)

    from .routes.health import health_bp
    from .routes.web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    return app
