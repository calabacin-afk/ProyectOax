# Coordinación del equipo

## Propiedad por integrante

1. **Frontend y UX:** `app/templates/`, `app/static/`, `prototipo.html` y el consumo de los contratos en `docs/api.md`. Responsable de Bootstrap, Leaflet, geolocalización opcional y accesibilidad. Las coordenadas solo centran el mapa/ubican marcadores; no se implementa búsqueda por radio.
2. **Backend y datos:** `app/__init__.py`, `app/config.py`, `app/extensions.py`, `app/models/`, `app/schemas/`, `app/routes/`, `app/services/search_service.py`, Docker y contratos. Responsable de validaciones y lecturas/escrituras en colecciones Chroma; no usa SQL, PostgreSQL, PostGIS ni pgvector.
3. **IA:** `app/services/ai/gemma_service.py`, `app/services/embedding_service.py`, `app/services/recommendation_service.py` y evaluación de modelos. Gemma devuelve filtros estructurados; Ollama genera embeddings; el backend valida todo antes de consultar Chroma. El modelo no crea lugares ni modifica colecciones directamente.

## Interfaces de integración

- Frontend llama únicamente a endpoints descritos en `docs/api.md`.
- IA expone funciones Python que reciben texto y devuelven `SearchIntent`/vectores validados; no reciben conexiones directas al almacén.
- Backend publica una colección versionada para lugares y controla qué metadatos se pueden filtrar.
- Cambios de rutas, esquemas o campos de metadatos se coordinan en PR y actualizan la documentación antes de integrar.
- Chroma no ofrece relaciones foráneas ni transacciones multi-colección; las comprobaciones de referencias e identidad son responsabilidad del backend.

## Git y trabajo mixto

- `main`: versión estable; `develop`: integración; `feature/*`: trabajo individual.
- Abrir Pull Requests a `develop`; nadie trabaja directamente en `main`.
- Antes de editar, cada persona avisa qué archivos tomará. Un archivo compartido tiene un responsable para evitar conflictos cuando se trabaja en computadoras diferentes o en el mismo equipo.
- No subir `.env`, credenciales, tokens, información personal innecesaria, el volumen `chroma_data` ni pesos de modelos.
