# Responsabilidades e integración

## Integrante 1 — Frontend y UX

Propiedad principal:

- `app/templates/`
- `app/static/`
- integración visual con Leaflet y la API descrita en `docs/api.md`

Trabaja accesibilidad, navegación móvil, catálogo, ficha de lugar, formularios, mapa y “Sorpréndeme”. No inventa coordenadas ni envía ubicación del navegador al backend.

## Integrante 2 — Backend y datos

Propiedad principal:

- `app/__init__.py`, `app/config.py`, `app/extensions.py`, `app/security.py`
- `app/routes/`, `app/services/account_service.py`, `favorite_service.py`, `place_service.py`
- `Dockerfile`, `docker-compose.yml`, dependencias y contratos

El MVP usa Chroma como única persistencia, no PostgreSQL/PostGIS/pgvector. Mantiene validaciones, autorización, sesión, CSRF, colecciones y publicación de fichas.

## Integrante 3 — IA local

Propiedad principal:

- `app/services/embedding_service.py`
- Siguiente trabajo: `app/services/ai/gemma_service.py`, `app/services/search_service.py`, ranking y evaluación

Actualmente Qwen3 Embedding crea el vector de cada ficha desde Ollama. Gemma 4 está definida en configuración, pero aún no se usa. Al integrar Gemma, su módulo entregará únicamente un objeto validado con filtros; no abrirá colecciones ni ejecutará SQL.

## Interfaces acordadas

- Frontend puede consumir `/api/lugares/`, `/api/lugares/<id>`, `POST /busqueda/` y `/categorias/`; los formularios HTML existentes pueden mantenerse con Jinja.
- `list_public_places(...)` filtra exclusivamente los registros `verificado`; presupuesto y duración estrictos excluyen fichas con esos datos desconocidos.
- `create_place(data, created_by)` guarda primero el catálogo y trata de generar embedding con `embed_text`; si Ollama falla, el vector queda pendiente y la búsqueda tradicional sigue funcionando. El formulario nunca envía vectores.
- `CHROMA_CATALOG_COLLECTION` almacena fichas; `CHROMA_COLLECTION` contiene únicamente embeddings Qwen versión `qwen3-embedding:0.6b` y 1024 dimensiones. Cambiar modelo o dimensión implica una colección nueva y reindexación.
- Cambios a ruta, campo de metadatos, categoría o formato de API actualizan este acuerdo, documentación y pruebas en el mismo PR.

## Git y trabajo mixto

- `main`: versión estable; `develop`: integración; `feature/*`: cambios independientes.
- Pull Requests hacia `develop`, con commits que expliquen el cambio. Nadie trabaja directamente sobre `main`.
- Antes de editar un archivo compartido, revisen `git status` y avisen quién lo está modificando. Si trabajan en el mismo equipo, cada persona usa una rama y checkout separados o trabaja en turnos; no editen al mismo tiempo el mismo directorio.
- No subir `.env`, secretos, cuentas reales de prueba, información personal, `chroma_data` ni pesos de modelos.

## Integración

Cada PR debe incluir comprobación manual o automatizada de la ruta cambiada y actualizar documentación. Antes de una demo conjunta, hagan pull de `develop`, instalen `requirements.txt`, usen sus propios `.env` y validen que el modelo de embeddings local esté disponible para administración. El catálogo de cada laptop es local salvo que acuerden importar una copia verificada.
