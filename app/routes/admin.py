from urllib.parse import urlparse

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from ..constants import AMBIENCES, CATEGORIES, COMPANIONS
from ..extensions import limiter
from ..security import admin_required, require_csrf
from ..services.place_service import create_place, list_admin_places, verify_place


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _optional_text(field, maximum):
    value = request.form.get(field, "").strip()
    if len(value) > maximum:
        raise ValueError(f"El campo {field} supera el máximo de {maximum} caracteres.")
    return value or None


def _optional_price(field):
    raw = request.form.get(field, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("Los precios deben ser cantidades enteras en MXN.") from exc
    if value < 0 or value > 1_000_000:
        raise ValueError("El precio debe estar entre 0 y 1,000,000 MXN.")
    return value


def _optional_coordinate(field, low, high):
    raw = request.form.get(field, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("Las coordenadas deben ser números válidos.") from exc
    if not low <= value <= high:
        raise ValueError("Una coordenada está fuera de rango.")
    return value


def _optional_duration():
    raw = request.form.get("duration_minutes", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("La duración debe ser un número entero de minutos.") from exc
    if not 1 <= value <= 1440:
        raise ValueError("La duración debe estar entre 1 y 1,440 minutos.")
    return value


def _valid_url(value, field, required=False):
    if not value:
        if required:
            raise ValueError(f"Agrega una fuente para verificar {field}.")
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} debe ser una dirección http o https válida.")
    return value


def _place_form_data():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    if not 2 <= len(name) <= 120:
        raise ValueError("El nombre debe tener entre 2 y 120 caracteres.")
    if not 20 <= len(description) <= 3000:
        raise ValueError("La descripción debe tener entre 20 y 3,000 caracteres.")
    if category not in CATEGORIES:
        raise ValueError("Selecciona una categoría válida.")

    price_min = _optional_price("price_min_mxn")
    price_max = _optional_price("price_max_mxn")
    if (price_min is None) != (price_max is None):
        raise ValueError("Escribe ambos precios o deja ambos vacíos.")
    if price_min is not None and price_min > price_max:
        raise ValueError("El precio mínimo no puede superar el máximo.")

    latitude = _optional_coordinate("latitude", -90, 90)
    longitude = _optional_coordinate("longitude", -180, 180)
    if (latitude is None) != (longitude is None):
        raise ValueError("Escribe latitud y longitud juntas, o deja ambas vacías.")

    verified = request.form.get("verified") == "yes"
    source_url = _valid_url(
        _optional_text("source_url", 500),
        "la ficha",
        required=verified,
    )
    photo_url = _valid_url(_optional_text("photo_url", 500), "la foto")
    photo_source_url = _valid_url(
        _optional_text("photo_source_url", 500), "la fuente de la foto"
    )
    if photo_url and not photo_source_url:
        raise ValueError("Incluye la fuente o licencia de la foto.")

    tags = [tag.strip()[:40] for tag in request.form.get("tags", "").split(",")]
    tags = list(dict.fromkeys(tag for tag in tags if tag))[:10]
    ambience = request.form.getlist("ambience")
    companions = request.form.getlist("companions")
    if any(value not in AMBIENCES for value in ambience):
        raise ValueError("Selecciona un ambiente válido.")
    if any(value not in COMPANIONS for value in companions):
        raise ValueError("Selecciona una opción válida de acompañantes.")
    return {
        "name": name,
        "description": description,
        "category": category,
        "address": _optional_text("address", 240),
        "zone": _optional_text("zone", 100),
        "phone": _optional_text("phone", 40),
        "website": _valid_url(_optional_text("website", 500), "el sitio web"),
        "opening_hours": _optional_text("opening_hours", 240),
        "duration_minutes": _optional_duration(),
        "ambience": ambience,
        "companions": companions,
        "price_min_mxn": price_min,
        "price_max_mxn": price_max,
        "photo_url": photo_url,
        "photo_source_url": photo_source_url,
        "latitude": latitude,
        "longitude": longitude,
        "source_url": source_url,
        "tags": tags,
        "verified": verified,
    }


@admin_bp.get("/lugares")
@admin_required
def places():
    status = request.args.get("estado", "pendiente")
    if status not in {"pendiente", "verificado"}:
        abort(400)
    return render_template(
        "admin/places.html",
        places=list_admin_places(status),
        status=status,
    )


@admin_bp.route("/lugares/nuevo", methods=["GET", "POST"])
@admin_required
@limiter.limit("20 per hour")
def new_place():
    if request.method == "GET":
        return render_template(
            "admin/place_form.html",
            categories=CATEGORIES,
            ambiences=AMBIENCES,
            companions=COMPANIONS,
        )

    require_csrf()
    try:
        data = _place_form_data()
        place = create_place(data, session["user_id"])
    except ValueError as exc:
        return render_template(
            "admin/place_form.html",
            categories=CATEGORIES,
            ambiences=AMBIENCES,
            companions=COMPANIONS,
            error=str(exc),
            form=request.form,
        ), 422 if isinstance(exc, ValueError) else 503

    if place["status"] == "verificado":
        flash("Lugar guardado y publicado con la fuente que proporcionaste.", "success")
    else:
        flash("Lugar guardado como pendiente; no aparecerá en el catálogo público.", "info")
    if place["embedding_status"] == "pendiente":
        flash(
            "La ficha ya funciona en búsqueda tradicional. Su vector semántico queda pendiente hasta que Ollama esté disponible.",
            "warning",
        )
    return redirect(url_for("admin.places"))


@admin_bp.post("/lugares/<place_id>/verificar")
@admin_required
@limiter.limit("30 per hour")
def verify(place_id):
    require_csrf()
    source_url = request.form.get("source_url", "").strip()
    try:
        source_url = _valid_url(source_url, "la fuente", required=True)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("admin.places", estado="pendiente"))
    place = verify_place(place_id, source_url, session["user_id"])
    if place is None:
        abort(404)
    flash("Lugar verificado y publicado.", "success")
    if place["embedding_status"] == "pendiente":
        flash(
            "La búsqueda tradicional está lista; el embedding semántico se puede generar cuando Ollama esté activo.",
            "warning",
        )
    return redirect(url_for("admin.places", estado="pendiente"))
