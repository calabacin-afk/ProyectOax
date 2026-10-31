import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
    CHROMA_CATALOG_COLLECTION = os.getenv(
        "CHROMA_CATALOG_COLLECTION", "lugares_catalogo_v1"
    )
    CHROMA_COLLECTION = os.getenv(
        "CHROMA_COLLECTION", "lugares_qwen3_embedding_0_6b_v1"
    )

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4:e2b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45"))
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
