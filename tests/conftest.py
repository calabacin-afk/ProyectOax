import pytest

from app import create_app
from app.config import Config


@pytest.fixture
def app(tmp_path):
    test_config = type(
        "TestConfig",
        (Config,),
        {
            "TESTING": True,
            "SECRET_KEY": "test-session-secret",
            "CHROMA_PATH": str(tmp_path / "chroma"),
            "RATELIMIT_ENABLED": False,
        },
    )
    application = create_app(test_config)
    yield application
    client = application.extensions.get("chroma_client")
    if client is not None:
        client.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf(client):
    client.get("/auth/login")
    with client.session_transaction() as current_session:
        return current_session["_csrf_token"]
