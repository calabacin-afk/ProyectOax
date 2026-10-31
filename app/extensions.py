"""Lazy access to the persistent Chroma client.

We initialize Chroma only when a route/service needs it, so the static site can
still start if the local vector store has not been installed or initialized.
"""

from pathlib import Path

from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .services.errors import StorageUnavailableError


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)


def get_chroma_client():
    """Return one persistent Chroma client for the current Flask process."""
    client = current_app.extensions.get("chroma_client")
    if client is None:
        try:
            import chromadb

            path = Path(current_app.config["CHROMA_PATH"]).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(path))
        except Exception as exc:
            raise StorageUnavailableError(
                "No se pudo abrir el almacenamiento local."
            ) from exc
        current_app.extensions["chroma_client"] = client
    return client


def get_metadata_collection(name, collection_kind):
    """Create a metadata collection that never invokes Chroma's default embedder."""
    try:
        return get_chroma_client().get_or_create_collection(
            name=name,
            metadata={"kind": collection_kind, "schema_version": "v1"},
            embedding_function=None,
        )
    except StorageUnavailableError:
        raise
    except Exception as exc:
        raise StorageUnavailableError(
            "No se pudo abrir una colección de almacenamiento."
        ) from exc


def get_places_collection():
    """Return the vector-only collection for records with real Qwen embeddings."""
    try:
        collection = get_chroma_client().get_or_create_collection(
            name=current_app.config["CHROMA_COLLECTION"],
            metadata={
                "embedding_model": current_app.config["EMBEDDING_MODEL"],
                "embedding_dimension": current_app.config["EMBEDDING_DIMENSION"],
                "embedding_schema_version": "v1",
            },
            embedding_function=None,
        )
    except StorageUnavailableError:
        raise
    except Exception as exc:
        raise StorageUnavailableError(
            "No se pudo abrir la colección de lugares."
        ) from exc
    metadata = collection.metadata or {}
    if metadata.get("embedding_model") != current_app.config["EMBEDDING_MODEL"]:
        raise RuntimeError(
            "La colección de lugares fue creada con otro modelo de embeddings. "
            "Configura una colección nueva y reindexa los datos."
        )
    expected_dimension = current_app.config["EMBEDDING_DIMENSION"]
    stored_dimension = metadata.get("embedding_dimension", expected_dimension)
    if stored_dimension != expected_dimension:
        raise RuntimeError(
            "La colección de lugares fue creada con otra dimensión de embeddings. "
            "Configura una colección nueva y reindexa los datos."
        )
    return collection


def get_catalog_collection():
    """Return the catalogue records, which remain usable without Ollama."""
    return get_metadata_collection(
        current_app.config["CHROMA_CATALOG_COLLECTION"],
        "place_catalog_records",
    )
