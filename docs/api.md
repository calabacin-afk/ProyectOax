# API y rutas disponibles

Este documento describe el código que existe ahora. Las rutas HTML usan formularios Jinja y sesión de Flask. La API JSON disponible es pequeña e independiente. Las rutas de IA, opiniones y escritura JSON siguen pendientes; no se debe construir un cliente suponiendo que ya funcionan.

## Sitio web

| Método y ruta | Entrada | Resultado |
|---|---|---|
| `GET /` | Query opcional `q`, `categoria`, `zona`, `presupuesto`, `pagina` | Página principal y catálogo filtrado. |
| `GET /lugares/` | Los mismos filtros | Catálogo HTML; 400 si un filtro tiene formato inválido. |
| `GET /lugares/<id>` | ID Chroma | Detalle de una ficha verificada; 404 si no existe o sigue pendiente. |
| `GET /sorprendeme` | Query opcional `categoria`, `presupuesto`, `minutos`, `con_quien`, `ambiente`, `excluir` | Ficha aleatoria entre las que pasan todos los filtros. Si no hay coincidencias, mantiene los filtros y muestra el estado vacío. |
| `GET /categorias/` | — | JSON con categorías y slugs disponibles. |
| `GET /health/live` | — | `{"status":"ok"}`; solo confirma que Flask responde. |

Para filtros en el catálogo, `q` admite hasta 120 caracteres, `zona` hasta 100, `categoria` debe ser un slug conocido y `presupuesto` es un entero de 0 a 1,000,000 MXN. Un presupuesto estricto omite lugares sin precio máximo conocido o cuyo precio máximo lo supera.

“Sorpréndeme” admite presupuesto entero de 0 a 1,000,000 MXN, duración de 1 a 1,440 minutos, una opción de compañía (`solo`, `pareja`, `amigos`, `familia`) y un ambiente (`tranquilo`, `animado`, `aire-libre`, `familiar`). Si el registro no tiene el dato necesario para validar un filtro, queda fuera. Actualmente no usa ubicación, radio o distancia, ni llama a un modelo generativo.

## API JSON

Los resultados exitosos usan `{ "data": ..., "meta": ... }`. Los errores JSON usan `{ "error": { "codigo": ..., "mensaje": ... } }`.

### `GET /api/lugares/`

Query opcional: `q`, `categoria`, `zona`, `presupuesto`.

Respuesta `200`:

```json
{
  "data": [{"id":"...","name":"...","category":"...","status":"verificado"}],
  "meta": {"total": 1}
}
```

Solo devuelve fichas verificadas. `presupuesto` es entero entre 0 y 1,000,000 MXN; las fichas sin precio máximo no coinciden.

### `GET /api/lugares/<id>`

Devuelve `200` con un objeto público de ficha o `404` cuando el lugar no existe/no está publicado.

### `POST /busqueda/`

Requiere `Content-Type: application/json`. Cuerpo:

```json
{
  "q": "café",
  "categoria": "cafeterias",
  "zona": "Centro",
  "presupuesto": 150
}
```

Todos los campos son opcionales. Campos no reconocidos se rechazan. Devuelve `200` con las fichas y `meta.modo` igual a `tradicional`; no requiere Ollama.

### Códigos de error JSON

- `400`: cuerpo ausente/no JSON o propiedades no reconocidas.
- `404`: ficha inexistente o no publicada.
- `422`: tipo, rango o categoría inválidos.
- `429`: límite de solicitudes.
- `503`: almacenamiento local no disponible.
- `500`: error interno; el detalle técnico se conserva solo en el log del servidor.

## Formularios y sesión

| Método y ruta | Validaciones y resultado |
|---|---|
| `GET/POST /auth/registro` | Nombre de 2–80 caracteres, correo normalizado, contraseña de mínimo 12 caracteres y CSRF. Crea una cuenta y sesión. Conflicto de correo: 409. |
| `GET/POST /auth/login` | Correo y contraseña con respuesta genérica al fallar. CSRF requerido. |
| `POST /auth/logout` | Sesión y CSRF requeridos; limpia la sesión. |
| `GET /favoritos/` | Requiere sesión iniciada. |
| `POST /favoritos/<id>` | Requiere sesión, ficha verificada y CSRF; alterna el favorito y regresa a la página anterior del mismo sitio. |
| `GET /admin/lugares` | Requiere rol `admin`. |
| `GET/POST /admin/lugares/nuevo` | Requiere admin y CSRF; crea ficha pendiente o publicada tras confirmación y fuente. Si Ollama no está disponible, guarda la ficha para búsqueda tradicional y marca el embedding como pendiente. |
| `POST /admin/lugares/<id>/verificar` | Requiere admin, CSRF y URL de fuente `http/https`; publica la ficha. |

El primer admin se crea desde consola con `python -m flask --app run:app crear-admin`.

Para reintentar la generación de embeddings pendientes después de activar Ollama: `python -m flask --app run:app generar-embeddings`.

## Contratos pendientes

Estas rutas aún no existen y no deben considerarse parte de la integración actual:

- API JSON de registro, login, logout, escritura y actualización de lugares.
- `/ia/interpretar`, `/ia/buscar` y `/ia/sorprendeme` como API.
- Búsqueda semántica de consulta, ranking con embeddings y explicaciones generadas por Gemma.
- CRUD JSON de favoritos, perfiles, preferencias y opiniones.
- Planeación de rutas con múltiples paradas.

Al implementarlas se actualizarán este documento y las pruebas del endpoint correspondiente.
