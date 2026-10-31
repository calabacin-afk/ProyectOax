import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    GEMMA_MODEL = os.getenv("GEMMA_MODEL", "gemma4:e4b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
