# Coordinación del equipo

## Propiedad por integrante

1. **Frontend/UX:** `app/templates/`, `app/static/`. Consume únicamente los contratos publicados en `docs/api.md`; no accede a la base de datos.
2. **Backend/datos:** `app/__init__.py`, `config.py`, `extensions.py`, `models/`, `schemas/`, `routes/`, `search_service.py`, migraciones, Docker y API. Mantiene los contratos como fuente de verdad.
3. **IA:** `services/ai/gemma_service.py`, `embedding_service.py`, `recommendation_service.py` y evaluación de modelos. Expone una interfaz que devuelve filtros y vectores; no produce SQL ni modifica directamente tablas.

## Git

- `main`: versión estable; `develop`: integración; `feature/*`: trabajo individual.
- Abrir Pull Requests a `develop`; no trabajar directamente en `main`.
- Un archivo compartido tiene un responsable. Los cambios de contrato pasan por PR y actualizan `docs/api.md`.
- No subir `.env`, credenciales, tokens, datos personales innecesarios ni pesos de modelos.
- Inicializar el repositorio y crear ramas después del primer commit de base en `develop`; no hay remoto GitHub configurado todavía.
