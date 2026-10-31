from app.services.account_service import create_user
from app.extensions import get_catalog_collection
from app.services.errors import EmbeddingUnavailableError
from app.services.place_service import create_place, get_place, generate_missing_embeddings
from app.services.place_service import list_admin_places


def test_home_displays_empty_state_without_fake_places(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Estamos preparando el catálogo" in response.get_data(as_text=True)


def test_categories_endpoint_returns_known_categories(client):
    response = client.get("/categorias/")

    assert response.status_code == 200
    assert response.json["data"]
    assert {item["slug"] for item in response.json["data"]} >= {"gastronomia", "cultura"}


def test_register_creates_a_user_session(client, csrf):
    response = client.post(
        "/auth/registro",
        data={
            "_csrf_token": csrf,
            "name": "María López",
            "email": "Maria@example.com",
            "password": "UnaClaveLarga-123",
            "password_confirmation": "UnaClaveLarga-123",
        },
    )

    assert response.status_code == 302
    with client.session_transaction() as current_session:
        assert current_session["name"] == "María López"
        assert current_session["role"] == "user"


def test_register_rejects_missing_csrf(client):
    response = client.post(
        "/auth/registro",
        data={
            "name": "María López",
            "email": "maria@example.com",
            "password": "UnaClaveLarga-123",
            "password_confirmation": "UnaClaveLarga-123",
        },
    )

    assert response.status_code == 400


def test_login_uses_a_password_hash_and_generic_failure(client, app, csrf):
    with app.app_context():
        create_user("María López", "maria@example.com", "UnaClaveLarga-123")

    response = client.post(
        "/auth/login",
        data={"_csrf_token": csrf, "email": "maria@example.com", "password": "incorrecta"},
    )
    assert response.status_code == 401
    assert "Correo o contraseña incorrectos" in response.get_data(as_text=True)

    response = client.post(
        "/auth/login",
        data={"_csrf_token": csrf, "email": "maria@example.com", "password": "UnaClaveLarga-123"},
    )
    assert response.status_code == 302
    with client.session_transaction() as current_session:
        assert current_session["role"] == "user"


def test_admin_page_requires_an_admin(client):
    response = client.get("/admin/lugares")

    assert response.status_code == 302


def test_verified_places_are_searchable_and_budget_is_a_hard_filter(client, app):
    with app.app_context():
        get_catalog_collection().add(
            ids=["place-test-1"],
            embeddings=[[0.0]],
            documents=["Café de prueba en Oaxaca"],
            metadatas=[
                {
                    "name": "Café de prueba",
                    "description": "Café local con una descripción verificada para prueba.",
                    "category": "cafeterias",
                    "status": "verificado",
                    "price_min_mxn": 40,
                    "price_max_mxn": 80,
                    "latitude": 17.06,
                    "longitude": -96.72,
                    "tags": ["café", "prueba"],
                }
            ],
        )

    found = client.get("/lugares/?q=café")
    too_expensive = client.get("/lugares/?presupuesto=50")
    within_budget = client.get("/lugares/?presupuesto=100")

    assert found.status_code == 200
    assert "Café de prueba" in found.get_data(as_text=True)
    assert "Café de prueba" not in too_expensive.get_data(as_text=True)
    assert "Café de prueba" in within_budget.get_data(as_text=True)
    assert "OpenStreetMap" in within_budget.get_data(as_text=True)


def test_admin_can_add_pending_place_and_publish_after_verification(
    client, app, monkeypatch
):
    monkeypatch.setattr(
        "app.services.place_service.embed_text", lambda _text: [0.0] * 1024
    )
    with app.app_context():
        admin = create_user(
            "Admin Oaxaca", "admin@example.com", "ClaveSegura-987654", role="admin"
        )
    client.get("/auth/login")
    with client.session_transaction() as current_session:
        current_session["user_id"] = admin["id"]
        current_session["name"] = admin["name"]
        current_session["role"] = "admin"
        csrf = current_session["_csrf_token"]

    form_page = client.get("/admin/lugares/nuevo")
    assert form_page.status_code == 200
    assert "Duración aproximada" in form_page.get_data(as_text=True)
    assert "Ambiente confirmado" in form_page.get_data(as_text=True)

    response = client.post(
        "/admin/lugares/nuevo",
        data={
            "_csrf_token": csrf,
            "name": "Taller de prueba",
            "category": "artesanias",
            "description": "Taller de artesanías de prueba con información pendiente.",
            "zone": "Centro",
            "source_url": "",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        pending = list_admin_places("pendiente")
    assert [place["name"] for place in pending] == ["Taller de prueba"]
    place_id = pending[0]["id"]

    response = client.get("/")
    assert "Taller de prueba" not in response.get_data(as_text=True)

    response = client.post(
        f"/admin/lugares/{place_id}/verificar",
        data={"_csrf_token": csrf, "source_url": "https://example.org/fuente"},
    )
    assert response.status_code == 302
    detail = client.get(f"/lugares/{place_id}")
    assert detail.status_code == 200
    assert "Taller de prueba" in detail.get_data(as_text=True)


def test_user_can_save_a_verified_place(client, app, csrf):
    with app.app_context():
        user = create_user("Ana Oaxaca", "ana@example.com", "ClaveSegura-987654")
        get_catalog_collection().add(
            ids=["place-favorite-1"],
            embeddings=[[0.0]],
            documents=["Lugar verificado de prueba"],
            metadatas=[
                {
                    "name": "Lugar favorito de prueba",
                    "description": "Un lugar de prueba que tiene información verificada.",
                    "category": "cultura",
                    "status": "verificado",
                }
            ],
        )

    with client.session_transaction() as current_session:
        current_session["user_id"] = user["id"]
        current_session["name"] = user["name"]
        current_session["role"] = "user"
        csrf_token = current_session["_csrf_token"]

    response = client.post(
        "/favoritos/place-favorite-1", data={"_csrf_token": csrf_token}
    )
    assert response.status_code == 302
    favorites = client.get("/favoritos/")
    assert favorites.status_code == 200
    assert "Lugar favorito de prueba" in favorites.get_data(as_text=True)


def test_json_search_returns_only_public_catalogue_records(client, app):
    with app.app_context():
        get_catalog_collection().add(
            ids=["api-place-1"],
            embeddings=[[0.0]],
            documents=["Taller real de prueba"],
            metadatas=[
                {
                    "name": "Taller API de prueba",
                    "description": "Ficha de prueba publicada para validar búsqueda API.",
                    "category": "artesanias",
                    "status": "verificado",
                }
            ],
        )

    response = client.post(
        "/busqueda/",
        json={"q": "Taller API", "categoria": "artesanias"},
    )

    assert response.status_code == 200
    assert response.json["meta"]["modo"] == "tradicional"
    assert response.json["data"][0]["name"] == "Taller API de prueba"


def test_json_search_rejects_unrecognized_fields(client):
    response = client.post("/busqueda/", json={"sql": "DROP TABLE lugares"})

    assert response.status_code == 400
    assert response.json["error"]["codigo"] == "http_400"


def test_surprise_filters_are_strict_and_exclude_unknown_prices(client, app):
    with app.app_context():
        get_catalog_collection().add(
            ids=["surprise-known", "surprise-unknown"],
            embeddings=[[0.0], [0.0]],
            documents=["Taller conocido", "Lugar con precio desconocido"],
            metadatas=[
                {
                    "name": "Taller familiar",
                    "description": "Taller verificado, económico y para toda la familia.",
                    "category": "artesanias",
                    "status": "verificado",
                    "price_min_mxn": 50,
                    "price_max_mxn": 100,
                    "duration_minutes": 45,
                    "ambience": ["tranquilo"],
                    "companions": ["familia"],
                },
                {
                    "name": "Lugar sin precio",
                    "description": "Lugar verificado sin dato de precio disponible.",
                    "category": "cultura",
                    "status": "verificado",
                    "duration_minutes": 30,
                    "ambience": ["tranquilo"],
                    "companions": ["familia"],
                },
            ],
        )

    match = client.get(
        "/sorprendeme?presupuesto=100&minutos=60&con_quien=familia&ambiente=tranquilo"
    )
    too_strict = client.get(
        "/sorprendeme?presupuesto=20&minutos=60&con_quien=familia&ambiente=tranquilo"
    )

    assert match.status_code == 200
    assert "Taller familiar" in match.get_data(as_text=True)
    assert "Lugar sin precio" not in match.get_data(as_text=True)
    assert too_strict.status_code == 200
    assert "Taller familiar" not in too_strict.get_data(as_text=True)
    assert "Aún no encontramos una opción verificada" in too_strict.get_data(as_text=True)


def test_catalogue_saves_without_ollama_and_can_index_later(app, monkeypatch):
    def unavailable(_text):
        raise EmbeddingUnavailableError("Ollama no está activo")

    monkeypatch.setattr("app.services.place_service.embed_text", unavailable)
    with app.app_context():
        place = create_place(
            {
                "name": "Ficha offline",
                "description": "Ficha de prueba agregada mientras Ollama no está disponible.",
                "category": "cultura",
                "verified": False,
            },
            created_by="admin-test",
        )
        assert place["embedding_status"] == "pendiente"
        assert place["status"] == "pendiente"
        assert get_place(place["id"]) is None

        monkeypatch.setattr(
            "app.services.place_service.embed_text", lambda _text: [0.0] * 1024
        )
        indexed, total = generate_missing_embeddings()
        refreshed = get_place(place["id"], include_unverified=True)

    assert (indexed, total) == (1, 1)
    assert refreshed["embedding_status"] == "listo"
