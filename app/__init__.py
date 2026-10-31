import secrets

from flask import Flask, jsonify, render_template, request, session

from .config import Config
from .extensions import limiter
from .security import csrf_token
from .services.errors import StorageUnavailableError


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config.get("SECRET_KEY") or app.config["SECRET_KEY"].startswith(
        "REEMPLAZAR_"
    ):
        app.config["SECRET_KEY"] = secrets.token_urlsafe(32)
        app.logger.warning(
            "SECRET_KEY no configurada: se generó una clave temporal para esta ejecución."
        )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    limiter.init_app(app)

    from .routes.health import health_bp
    from .routes.web import web_bp
    from .routes.auth import auth_bp, register_admin_cli
    from .routes.admin import admin_bp
    from .routes.favorites import favorites_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(favorites_bp)

    @app.context_processor
    def inject_template_helpers():
        user_id = session.get("user_id")
        current_user = None
        if user_id:
            current_user = {
                "id": user_id,
                "name": session.get("name", ""),
                "role": session.get("role", "user"),
            }
        return {"csrf_token": csrf_token, "current_user": current_user}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(self)")
        return response

    @app.errorhandler(StorageUnavailableError)
    def storage_unavailable(_error):
        if request.path.startswith("/api/") or request.path == "/busqueda/":
            return jsonify(error={"codigo": "almacenamiento_no_disponible", "mensaje": "El catálogo no está disponible."}), 503
        return render_template("errors/unavailable.html"), 503

    def _error_response(error, status):
        if request.path.startswith("/api/") or request.path == "/busqueda/":
            description = getattr(error, "description", "La solicitud no pudo completarse.")
            return jsonify(error={"codigo": f"http_{status}", "mensaje": description}), status
        return render_template(
            f"errors/{status}.html",
            message=getattr(error, "description", None),
        ), status

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(400)
    def bad_request(error):
        return _error_response(error, 400)

    @app.errorhandler(422)
    def unprocessable(error):
        return _error_response(error, 422)

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return jsonify(error={"codigo": "no_encontrado", "mensaje": "No se encontró el recurso."}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(
            "Error interno no controlado (tipo=%s, endpoint=%s)",
            type(error).__name__,
            request.endpoint or "desconocido",
        )
        if request.path.startswith("/api/") or request.path == "/busqueda/":
            return jsonify(error={"codigo": "error_interno", "mensaje": "Ocurrió un error interno."}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(429)
    def rate_limited(_error):
        if request.path.startswith("/api/") or request.path == "/busqueda/":
            return jsonify(error={"codigo": "limite_excedido", "mensaje": "Inténtalo de nuevo en un momento."}), 429
        return render_template("errors/429.html"), 429

    register_admin_cli(app)
    return app
