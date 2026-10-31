# Descubre Oaxaca

Plataforma para descubrir lugares y experiencias reales de Oaxaca mediante búsqueda tradicional, mapa y recomendaciones con Gemma 4 local.

> “No visites solamente Oaxaca. Descúbrela de una manera diferente”.

## Estado del proyecto

- `prototipo.html` es una maqueta visual estática; Flask la sirve en `/`.
- `/health/live` confirma que Flask responde.
- Catálogo, búsqueda, autenticación e integración de modelos todavía no están implementados.
- El MVP usará Chroma como único almacén. No usa PostgreSQL, PostGIS ni pgvector.
- El MVP no tiene filtro por radio o distancia. Las coordenadas opcionales se reservan para dibujar marcadores en Leaflet.
- La conexión al `PersistentClient` se crea cuando una función la solicita; la maqueta no necesita que Ollama esté activo.

## Requisitos

- Python 3.13.
- Para ejecutar la app en contenedor: Docker Desktop con Compose v2.
- Para la fase IA: Ollama y modelos locales; no se necesitan para ver la maqueta.

## Ejecutar Flask en Windows

Desde PowerShell, en la carpeta del proyecto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y cambia `SECRET_KEY`. Puedes generar una clave con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Arranca Flask:

```powershell
python run.py
```

Abre `http://127.0.0.1:5000/`. La pantalla no realiza búsquedas todavía. Si la carpeta `chroma_data` se crea al probar almacenamiento local, no se sube a Git.

## Ejecutar con Docker Compose

Después de instalar y abrir Docker Desktop:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs -f web
```

Abre `http://127.0.0.1:5000/`. Chroma persiste en el volumen Docker `chroma_data`; no hay un puerto de base de datos publicado. Para detener: `docker compose down`. No uses `docker compose down -v` si quieres conservar los datos.

Para conectar Ollama instalado en Windows dentro del contenedor, Compose usa `host.docker.internal:11434`. Al ejecutar Flask directamente, `.env` usa `localhost:11434`.

## Modelos locales (cuando llegue la fase IA)

En la laptop informada (Ryzen 9 8940HX, 24 GB RAM, RTX 5060 Laptop con 8 GB VRAM) se probará primero Gemma 4 E4B y se conservará E2B como alternativa. Instala Ollama desde su página oficial y después:

```powershell
ollama pull gemma4:e4b
ollama run gemma4:e4b
ollama pull qwen3-embedding:0.6b
```

El equipo debe medir latencia y memoria en cada computadora antes de fijar el perfil de demo.

## Aviso de seguridad de Chroma

La versión estable fijada de Chroma tiene avisos de seguridad publicados para ciertos usos del servidor HTTP y funciones de embeddings dinámicas. El prototipo usa persistencia embebida, no abre un servidor Chroma, y no acepta funciones de embeddings enviadas por usuarios. Mantén la app local; antes de exponerla a Internet revisa las [versiones y avisos de Chroma](https://github.com/chroma-core/chroma/releases) y actualiza a una versión corregida.

## Documentación

- [Arquitectura](docs/arquitectura.md)
- [Contratos de API](docs/api.md)
- [Modelo de datos Chroma](docs/modelo_datos.md)
- [Responsabilidades del equipo](docs/equipo.md)
- [Modelos locales y hardware](docs/modelos_locales.md)

## Git

Trabajamos con `main` (estable), `develop` (integración) y ramas `feature/*`. Cada integrante hace commits descriptivos y abre Pull Requests hacia `develop`. Nunca subas `.env`, el volumen `chroma_data`, credenciales o pesos de modelos.
