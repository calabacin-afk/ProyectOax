from flask import Blueprint


health_bp = Blueprint("health", __name__)


@health_bp.get("/health/live")
def live():
    """Liveness only; this endpoint does not claim the database is ready."""
    return {"status": "ok"}, 200
