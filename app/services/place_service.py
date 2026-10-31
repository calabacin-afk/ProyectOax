from datetime import UTC, datetime
from uuid import uuid4

from flask import current_app

from ..constants import CATEGORIES
from ..extensions import get_catalog_collection, get_places_collection
from .embedding_service import embed_text
from .errors import EmbeddingUnavailableError


def _records(where=None, limit=2000):
    result = get_catalog_collection().get(
        where=where,
        limit=limit,
        include=["documents", "metadatas"],
    )
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []
    places = []
    for index, place_id in enumerate(result["ids"]):
        metadata = metadatas[index] or {}
        places.append(_to_place(place_id, documents[index], metadata))
    return places


def _to_place(place_id, document, metadata):
    return {
        "id": place_id,
        "name": metadata.get("name", "Nombre pendiente"),
        "description": metadata.get("description", document or ""),
        "category": metadata.get("category", ""),
        "category_label": CATEGORIES.get(metadata.get("category"), "Otro lugar"),
        "address": metadata.get("address"),
        "zone": metadata.get("zone"),
        "phone": metadata.get("phone"),
        "website": metadata.get("website"),
        "opening_hours": metadata.get("opening_hours"),
        "duration_minutes": metadata.get("duration_minutes"),
        "ambience": metadata.get("ambience", []),
        "companions": metadata.get("companions", []),
        "price_min_mxn": metadata.get("price_min_mxn"),
        "price_max_mxn": metadata.get("price_max_mxn"),
        "tags": metadata.get("tags", []),
        "photo_url": metadata.get("photo_url"),
        "photo_source_url": metadata.get("photo_source_url"),
        "latitude": metadata.get("latitude"),
        "longitude": metadata.get("longitude"),
        "source_url": metadata.get("source_url"),
        "status": metadata.get("status", "pendiente"),
        "embedding_status": metadata.get("embedding_status", "pendiente"),
        "created_at": metadata.get("created_at"),
    }


def get_place(place_id, include_unverified=False):
    result = get_catalog_collection().get(
        ids=[place_id],
        include=["documents", "metadatas"],
    )
    if not result["ids"]:
        return None
    place = _to_place(
        result["ids"][0],
        (result.get("documents") or [""])[0],
        (result.get("metadatas") or [{}])[0] or {},
    )
    if not include_unverified and place["status"] != "verificado":
        return None
    return place


def list_public_places(
    query="",
    category="",
    zone="",
    budget=None,
    duration_max=None,
    companion="",
    ambience="",
):
    filters = [{"status": "verificado"}]
    if category:
        filters.append({"category": category})
    if budget is not None:
        # A strict budget filter intentionally excludes unknown prices.
        filters.append({"price_max_mxn": {"$lte": budget}})
    where = filters[0] if len(filters) == 1 else {"$and": filters}
    query_text = query.strip().casefold()
    zone_text = zone.strip().casefold()

    places = _records(where=where)
    if query_text:
        places = [
            place
            for place in places
            if query_text
            in " ".join(
                [
                    place["name"],
                    place["description"],
                    place["category_label"],
                    place["zone"] or "",
                    place["address"] or "",
                    " ".join(place["tags"]),
                ]
            ).casefold()
        ]
    if zone_text:
        places = [
            place
            for place in places
            if zone_text in (place["zone"] or "").casefold()
        ]
    if duration_max is not None:
        places = [
            place
            for place in places
            if place["duration_minutes"] is not None
            and place["duration_minutes"] <= duration_max
        ]
    if companion:
        places = [place for place in places if companion in place["companions"]]
    if ambience:
        places = [place for place in places if ambience in place["ambience"]]
    return sorted(places, key=lambda place: place["name"].casefold())


def list_admin_places(status="pendiente"):
    return _records(where={"status": status})


def _place_document(data):
    document_parts = [data["name"], data["description"], CATEGORIES[data["category"]]]
    if data.get("zone"):
        document_parts.append(data["zone"])
    if data.get("tags"):
        document_parts.extend(data["tags"])
    return "\n".join(document_parts)


def _store_embedding(place_id, document, metadata):
    """Index one record if Ollama is ready; leave the catalog usable otherwise."""
    try:
        embedding = embed_text(document)
        vector_metadata = dict(metadata)
        vector_metadata.update(
            {
                "embedding_status": "listo",
                "embedding_model": current_app.config["EMBEDDING_MODEL"],
                "embedding_schema_version": "v1",
            }
        )
        get_places_collection().upsert(
            ids=[place_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[vector_metadata],
        )
        catalog_metadata = dict(metadata)
        catalog_metadata.update(
            {
                "embedding_status": "listo",
                "embedding_model": current_app.config["EMBEDDING_MODEL"],
                "embedding_schema_version": "v1",
            }
        )
        get_catalog_collection().update(ids=[place_id], metadatas=[catalog_metadata])
        return True
    except EmbeddingUnavailableError:
        current_app.logger.info("Embedding pendiente para una ficha de lugar.")
    except Exception as exc:
        current_app.logger.warning(
            "No se pudo actualizar el índice vectorial (tipo=%s).",
            type(exc).__name__,
        )
    return False


def create_place(data, created_by):
    document = _place_document(data)
    now = datetime.now(UTC).isoformat()
    metadata = {
        "name": data["name"],
        "description": data["description"],
        "category": data["category"],
        "status": "verificado" if data.get("verified") else "pendiente",
        "embedding_status": "pendiente",
        "created_at": now,
        "created_by": created_by,
    }
    optional_text = (
        "address",
        "zone",
        "phone",
        "website",
        "opening_hours",
        "photo_url",
        "photo_source_url",
        "source_url",
    )
    for key in optional_text:
        if data.get(key):
            metadata[key] = data[key]
    if data.get("price_min_mxn") is not None:
        metadata["price_min_mxn"] = data["price_min_mxn"]
        metadata["price_max_mxn"] = data["price_max_mxn"]
    if data.get("duration_minutes") is not None:
        metadata["duration_minutes"] = data["duration_minutes"]
    if data.get("latitude") is not None:
        metadata["latitude"] = data["latitude"]
        metadata["longitude"] = data["longitude"]
    if data.get("verified"):
        metadata["verified_by"] = created_by
        metadata["verified_at"] = now
    if data.get("tags"):
        metadata["tags"] = data["tags"]
    if data.get("ambience"):
        metadata["ambience"] = data["ambience"]
    if data.get("companions"):
        metadata["companions"] = data["companions"]

    place_id = str(uuid4())
    # The catalogue is metadata-first and has its own nonsemantic sentinel vector.
    # It remains searchable by exact fields/text even when Ollama is unavailable.
    get_catalog_collection().add(
        ids=[place_id],
        embeddings=[[0.0]],
        documents=[document],
        metadatas=[metadata],
    )
    _store_embedding(place_id, document, metadata)
    return get_place(place_id, include_unverified=True)


def verify_place(place_id, source_url, verified_by):
    place = get_place(place_id, include_unverified=True)
    if place is None:
        return None
    result = get_catalog_collection().get(ids=[place_id], include=["documents", "metadatas"])
    metadata = result["metadatas"][0] or {}
    metadata.update(
        {
            "status": "verificado",
            "source_url": source_url,
            "verified_by": verified_by,
            "verified_at": datetime.now(UTC).isoformat(),
        }
    )
    get_catalog_collection().update(ids=[place_id], metadatas=[metadata])
    document = (result.get("documents") or [place["description"]])[0]
    _store_embedding(place_id, document, metadata)
    return get_place(place_id)


def generate_missing_embeddings():
    """Retry the vector index for records saved while Ollama was unavailable."""
    pending = _records(where={"embedding_status": "pendiente"})
    indexed = 0
    for place in pending:
        result = get_catalog_collection().get(
            ids=[place["id"]], include=["documents", "metadatas"]
        )
        if not result["ids"]:
            continue
        document = (result.get("documents") or [place["description"]])[0]
        metadata = result["metadatas"][0] or {}
        if _store_embedding(place["id"], document, metadata):
            indexed += 1
    return indexed, len(pending)
