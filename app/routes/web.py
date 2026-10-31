import random

from flask import Blueprint, abort, jsonify, render_template, request, session

from ..constants import AMBIENCES, CATEGORIES, COMPANIONS
from ..extensions import limiter
from ..services.favorite_service import favorite_place_ids
from ..services.place_service import get_place, list_public_places


web_bp = Blueprint("web", __name__)


def _catalogue():
    query = request.args.get("q", "").strip()
    category = request.args.get("categoria", "").strip()
    zone = request.args.get("zona", "").strip()
    raw_budget = request.args.get("presupuesto", "").strip()
    page_value = request.args.get("pagina", "1").strip()

    if len(query) > 120 or len(zone) > 100:
        abort(400, description="El texto de búsqueda es demasiado largo.")
    if category and category not in CATEGORIES:
        abort(400, description="La categoría seleccionada no existe.")
    try:
        budget = int(raw_budget) if raw_budget else None
        page = int(page_value)
    except ValueError:
        abort(400, description="El presupuesto o número de página no es válido.")
    if budget is not None and not 0 <= budget <= 1_000_000:
        abort(400, description="El presupuesto debe ser de 0 a 1,000,000 MXN.")
    if not 1 <= page <= 10000:
        abort(400, description="La página solicitada no es válida.")

    places = list_public_places(query, category, zone, budget)
    page_size = 12
    page_count = max(1, (len(places) + page_size - 1) // page_size)
    if page > page_count:
        page = page_count
    start = (page - 1) * page_size
    visible_places = places[start : start + page_size]

    favorites = set()
    if session.get("user_id"):
        favorites = favorite_place_ids(session["user_id"])
    map_points = [
        {
            "id": place["id"],
            "name": place["name"],
            "url": f"/lugares/{place['id']}",
            "lat": place["latitude"],
            "lon": place["longitude"],
        }
        for place in visible_places
        if place["latitude"] is not None and place["longitude"] is not None
    ]
    return render_template(
        "places/index.html",
        places=visible_places,
        categories=CATEGORIES,
        selected_category=category,
        query=query,
        zone=zone,
        budget=raw_budget,
        page=page,
        page_count=page_count,
        total=len(places),
        favorite_ids=favorites,
        map_points=map_points,
    )


@web_bp.get("/")
def index():
    return _catalogue()


@web_bp.get("/lugares/")
def places():
    return _catalogue()


@web_bp.get("/lugares/<place_id>")
def place_detail(place_id):
    place = get_place(place_id)
    if place is None:
        abort(404)
    favorite = False
    if session.get("user_id"):
        favorite = place_id in favorite_place_ids(session["user_id"])
    return render_template("places/detail.html", place=place, is_favorite=favorite)


@web_bp.get("/sorprendeme")
def surprise():
    category = request.args.get("categoria", "").strip()
    budget_text = request.args.get("presupuesto", "").strip()
    duration_text = request.args.get("minutos", "").strip()
    companion = request.args.get("con_quien", "").strip()
    ambience = request.args.get("ambiente", "").strip()
    exclude_id = request.args.get("excluir", "").strip()
    if category and category not in CATEGORIES:
        abort(400, description="La categoría seleccionada no existe.")
    if companion and companion not in COMPANIONS:
        abort(400, description="La opción de acompañantes no es válida.")
    if ambience and ambience not in AMBIENCES:
        abort(400, description="El ambiente seleccionado no es válido.")
    try:
        budget = int(budget_text) if budget_text else None
        duration = int(duration_text) if duration_text else None
    except ValueError:
        abort(400, description="Presupuesto o duración no válidos.")
    if budget is not None and not 0 <= budget <= 1_000_000:
        abort(400, description="El presupuesto debe ser de 0 a 1,000,000 MXN.")
    if duration is not None and not 1 <= duration <= 1440:
        abort(400, description="El tiempo disponible debe ser de 1 a 1,440 minutos.")

    candidates = list_public_places(
        category=category,
        budget=budget,
        duration_max=duration,
        companion=companion,
        ambience=ambience,
    )
    alternatives = [place for place in candidates if place["id"] != exclude_id]
    place = random.choice(alternatives) if alternatives else None
    if not exclude_id and candidates:
        place = random.choice(candidates)
    reasons = []
    if place:
        if category:
            reasons.append(f"Pertenece a la categoría {place['category_label']}.")
        if budget is not None:
            reasons.append(
                f"Su precio verificado (hasta ${place['price_max_mxn']} MXN) está dentro de tu límite."
            )
        if duration is not None:
            reasons.append(
                f"Su duración verificada es de {place['duration_minutes']} minutos, dentro del tiempo que tienes."
            )
        if companion:
            reasons.append(f"La ficha indica que es compatible con: {COMPANIONS[companion].lower()}.")
        if ambience:
            reasons.append(f"La ficha describe un ambiente {AMBIENCES[ambience].lower()}.")
        if not reasons:
            reasons.append("Es una ficha real del catálogo marcada como verificada.")
    return render_template(
        "places/surprise.html",
        place=place,
        has_another=len(candidates) > 1,
        reasons=reasons,
        categories=CATEGORIES,
        ambiences=AMBIENCES,
        companions=COMPANIONS,
        filters={
            "categoria": category,
            "presupuesto": budget_text,
            "minutos": duration_text,
            "con_quien": companion,
            "ambiente": ambience,
        },
    )


@web_bp.get("/categorias/")
def categories():
    return {"data": [{"slug": slug, "nombre": label} for slug, label in CATEGORIES.items()]}


def _api_place(place):
    """Return only public catalogue fields; never include account/admin metadata."""
    fields = (
        "id",
        "name",
        "description",
        "category",
        "category_label",
        "address",
        "zone",
        "phone",
        "website",
        "opening_hours",
        "duration_minutes",
        "ambience",
        "companions",
        "price_min_mxn",
        "price_max_mxn",
        "tags",
        "photo_url",
        "photo_source_url",
        "latitude",
        "longitude",
        "source_url",
        "status",
    )
    return {field: place.get(field) for field in fields}


def _validated_api_filters(payload):
    if not isinstance(payload, dict):
        abort(400, description="El cuerpo debe ser un objeto JSON.")
    allowed = {"q", "categoria", "zona", "presupuesto"}
    if set(payload) - allowed:
        abort(400, description="El cuerpo contiene campos no reconocidos.")
    query = payload.get("q", "")
    category = payload.get("categoria", "")
    zone = payload.get("zona", "")
    budget = payload.get("presupuesto")
    if not isinstance(query, str) or len(query) > 120:
        abort(422, description="q debe ser texto de hasta 120 caracteres.")
    if not isinstance(zone, str) or len(zone) > 100:
        abort(422, description="zona debe ser texto de hasta 100 caracteres.")
    if not isinstance(category, str) or (category and category not in CATEGORIES):
        abort(422, description="categoria no corresponde a una categoría existente.")
    if budget is not None and (
        isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= 1_000_000
    ):
        abort(422, description="presupuesto debe ser un entero entre 0 y 1,000,000 MXN.")
    return query, category, zone, budget


@web_bp.get("/api/lugares/")
@limiter.limit("60 per minute")
def api_places():
    query, category, zone, budget = _validated_api_filters(
        {
            "q": request.args.get("q", ""),
            "categoria": request.args.get("categoria", ""),
            "zona": request.args.get("zona", ""),
            "presupuesto": (
                int(request.args["presupuesto"])
                if request.args.get("presupuesto", "").isdigit()
                else request.args.get("presupuesto") or None
            ),
        }
    )
    places = list_public_places(query, category, zone, budget)
    return jsonify(data=[_api_place(place) for place in places], meta={"total": len(places)})


@web_bp.get("/api/lugares/<place_id>")
@limiter.limit("60 per minute")
def api_place_detail(place_id):
    place = get_place(place_id)
    if place is None:
        abort(404)
    return jsonify(data=_api_place(place))


@web_bp.post("/busqueda/")
@limiter.limit("30 per minute")
def api_search():
    payload = request.get_json(silent=True)
    if payload is None:
        abort(400, description="Envía un cuerpo JSON con Content-Type application/json.")
    query, category, zone, budget = _validated_api_filters(payload)
    places = list_public_places(query, category, zone, budget)
    return jsonify(
        data=[_api_place(place) for place in places],
        meta={"total": len(places), "modo": "tradicional"},
    )
