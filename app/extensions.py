"""Lazy access to the persistent Chroma client.

We initialize Chroma only when a route/service needs it, so the static site can
still start if the local vector store has not been installed or initialized.
"""

from pathlib import Path

from flask import current_app


def get_chroma_client():
    """Return one persistent Chroma client for the current Flask process."""
    client = current_app.extensions.get("chroma_client")
    if client is None:
        import chromadb

        path = Path(current_app.config["CHROMA_PATH"]).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(path))
        current_app.extensions["chroma_client"] = client
    return client


def get_places_collection():
    """Return the versioned places collection without a built-in embedder."""
    collection = get_chroma_client().get_or_create_collection(
        name=current_app.config["CHROMA_COLLECTION"],
        metadata={
            "embedding_model": current_app.config["EMBEDDING_MODEL"],
            "embedding_schema_version": "v1",
        },
        embedding_function=None,
    )
    metadata = collection.metadata or {}
    if metadata.get("embedding_model") != current_app.config["EMBEDDING_MODEL"]:
        raise RuntimeError(
            "La colección de lugares fue creada con otro modelo de embeddings. "
            "Configura una colección nueva y reindexa los datos."
        )
    return collection
