from flask import Blueprint, render_template


web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def inicio():
    """Serve the static visual prototype while the product UI is built."""
    return render_template("index.html")
