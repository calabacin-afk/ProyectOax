# Descubre Oaxaca

Prototipo inicial para descubrir lugares y experiencias reales de Oaxaca mediante búsqueda tradicional, mapa y recomendaciones con Gemma 4 local.

## Estado del código

- `prototipo.html` es una maqueta visual estática.
- Flask sirve la maqueta desde `/` y ofrece `/health/live`.
- No están implementados todavía catálogo, autenticación, búsqueda, rutas, IA ni conexión SQLAlchemy a la base.
- La infraestructura PostgreSQL/PostGIS/pgvector está preparada en Docker Compose; falta construirla y verificarla cuando Docker Desktop esté disponible.

## Requisitos para iniciar en Windows

1. Git (ya disponible en la computadora inspeccionada).
2. Python 3.13 (disponible como `py -3.13` en la computadora inspeccionada).
3. Docker Desktop con Compose v2 para ejecutar PostgreSQL.
4. Ollama para la fase de Gemma; no es necesario para ver la maqueta.

Docker Desktop y Ollama no aparecen instalados en esta computadora. No se instalaron desde este proyecto.

## Ejecutar la pantalla Flask

En PowerShell, desde la raíz del repositorio:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y reemplaza `SECRET_KEY`. Puedes generarla con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Después inicia Flask:

```powershell
python run.py
```

Abre `http://127.0.0.1:5000/`. La pantalla no realiza búsquedas ni llamadas externas todavía.

## Ejecutar PostgreSQL con Docker Compose

Después de instalar Docker Desktop y arrancarlo:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs -f db
```

La base queda publicada en `localhost:5433`; dentro de Compose, Flask usa el nombre de servicio `db`. No borres el volumen `postgres_data` si quieres conservar la base local.

## Ollama para la laptop de demo

Perfil inicial a medir: `gemma4:e4b`; alternativa ligera: `gemma4:e2b`. Instala Ollama desde su página oficial y luego ejecuta:

```powershell
ollama pull gemma4:e4b
ollama run gemma4:e4b
ollama pull qwen3-embedding:0.6b
```

## Documentación

- [Arquitectura](docs/arquitectura.md)
- [Contratos de API](docs/api.md)
- [Modelo de datos](docs/modelo_datos.md)
- [Responsabilidades del equipo](docs/equipo.md)
- [Modelos locales y hardware](docs/modelos_locales.md)

## Ramas

El flujo acordado es `main` estable, `develop` integración y `feature/*` para trabajo individual. La carpeta todavía no tiene repositorio Git ni remoto GitHub; el primer commit debe hacerse en `develop`, no directamente en `main`.
