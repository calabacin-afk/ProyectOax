import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")
    CHROMA_COLLECTION = os.getenv(
        "CHROMA_COLLECTION", "lugares_qwen3_embedding_0_6b_v1"
    )

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4:e4b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
