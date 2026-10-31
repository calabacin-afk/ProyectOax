import math

import httpx
from flask import current_app

from .errors import EmbeddingUnavailableError


def embed_text(text):
    """Request one validated vector from the configured local Ollama model."""
    url = f"{current_app.config['OLLAMA_URL'].rstrip('/')}/api/embed"
    try:
        response = httpx.post(
            url,
            json={"model": current_app.config["EMBEDDING_MODEL"], "input": text},
            timeout=current_app.config["OLLAMA_TIMEOUT_SECONDS"],
        )
        response.raise_for_status()
        payload = response.json()
        vectors = payload.get("embeddings")
        vector = vectors[0] if isinstance(vectors, list) and vectors else None
        if not isinstance(vector, list):
            raise ValueError("Ollama no devolvió un vector.")

        expected = current_app.config["EMBEDDING_DIMENSION"]
        if len(vector) != expected:
            raise ValueError(
                f"Dimensión recibida {len(vector)}; se esperaba {expected}."
            )
        values = [float(value) for value in vector]
        if not all(math.isfinite(value) for value in values):
            raise ValueError("El vector contiene valores no válidos.")
        return values
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        raise EmbeddingUnavailableError(
            "No se pudo generar el embedding. Revisa Ollama y el modelo configurado."
        ) from exc
