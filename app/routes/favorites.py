from urllib.parse import urlsplit

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from ..security import login_required, require_csrf
from ..services.favorite_service import favorite_place_ids, toggle_favorite
from ..services.place_service import get_place, list_public_places


favorites_bp = Blueprint("favorites", __name__, url_prefix="/favoritos")


@favorites_bp.get("/")
@login_required
def index():
    ids = favorite_place_ids(session["user_id"])
    places = [place for place in list_public_places() if place["id"] in ids]
    return render_template("favorites/index.html", places=places)


@favorites_bp.post("/<place_id>")
@login_required
def toggle(place_id):
    require_csrf()
    place = get_place(place_id)
    if place is None:
        abort(404)
    is_favorite = toggle_favorite(session["user_id"], place_id)
    flash(
        "Guardado en tus favoritos." if is_favorite else "Se quitó de tus favoritos.",
        "success",
    )
    referrer = request.referrer
    if referrer:
        target = urlsplit(referrer)
        if (
            target.scheme in {"http", "https"}
            and target.netloc == request.host
            and target.path.startswith("/")
            and not target.path.startswith("//")
        ):
            return redirect(target.path + (f"?{target.query}" if target.query else ""))
    return redirect(url_for("web.place_detail", place_id=place_id))
