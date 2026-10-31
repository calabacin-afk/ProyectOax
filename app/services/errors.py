class StorageUnavailableError(RuntimeError):
    """The local Chroma store could not be opened or queried."""


class EmbeddingUnavailableError(RuntimeError):
    """Ollama could not produce a valid embedding for a place record."""
