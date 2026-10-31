# Contratos iniciales de API

Estos contratos son el acuerdo de integración del MVP. Todas las respuestas exitosas usan `{"data": ..., "meta": ...}` y los errores `{"error":{"codigo":"...","mensaje":"...","detalles":...}}`.

## Errores comunes

- `400`: JSON o parámetros mal formados.
- `401`: sesión requerida o credenciales inválidas.
- `403`: permisos insuficientes o token CSRF inválido.
- `404`: recurso inexistente o no público.
- `409`: conflicto de ID/correo/favorito duplicado.
- `422`: cuerpo JSON inválido según el esquema.
- `429`: límite de solicitudes excedido.
- `503` / `504`: Ollama u otra dependencia necesaria no disponible o agotó el tiempo.

## Endpoints

| Método y ruta | Solicitud / parámetros | Respuesta y validaciones |
|---|---|---|
| `POST /auth/registro` | `{nombre,email,password}` | `201` perfil; email normalizado y único; guardar solo hash seguro de contraseña. `409` email existente, `422` datos inválidos. |
| `POST /auth/login` | `{email,password}` | `200` sesión y perfil; `401` mensaje genérico si falla. |
| `POST /auth/logout` | Sesión y CSRF | `204`; invalida sesión. |
| `GET /categorias/` | Sin cuerpo | `200` categorías activas. |
| `GET /lugares/` | Query: `q`, `categoria`, `etiqueta`, `precio_max_mxn`, `zona`, `pagina`, `limite` | `200` lista paginada de fichas públicas. Presupuesto máximo excluye fichas sin precio verificado. No tiene parámetros de ubicación, radio ni distancia. |
| `GET /lugares/<id>` | ID en ruta | `200` ficha pública; `404` si falta o no está publicada. |
| `POST /lugares/` | Ficha, fuentes y fotos | `201` ficha en estado `pendiente`; solo administrador. Requiere procedencia de datos. |
| `PUT /lugares/<id>` | Campos editables de la ficha y sus fuentes | `200`; solo administrador; valida rangos, metadatos y procedencia. |
| `POST /busqueda/` | `{consulta?, filtros?, zona?, pagina?, limite?}` | `200` resultados de búsqueda tradicional, sin Ollama. `zona` es un filtro textual, no geográfico. |
| `POST /ia/interpretar` | `{consulta}` | `200` `SearchIntent` validado; `503`/`504` si Gemma no responde. No incluye origen GPS ni radio. |
| `POST /ia/buscar` | `{consulta, filtros_confirmados?}` | `200` resultados reales y `modo` (`semantico` o `tradicional`). Si Gemma falla, ejecuta búsqueda textual/filtros disponibles. |
| `POST /ia/sorprendeme` | `{presupuesto_maximo_mxn?, duracion_max_min?, companeros?, ambiente?, categorias?}` | `200` candidatos reales. Los límites expresados de presupuesto y duración son estrictos. No acepta distancia máxima. |
| `GET /favoritos/` | Sesión autenticada | `200` lista del usuario. |
| `POST /favoritos/<lugar_id>` | Sesión autenticada | `201` favorito guardado; operación idempotente. `404` lugar inexistente. |
| `DELETE /favoritos/<lugar_id>` | Sesión autenticada | `204` favorito eliminado. |
| `POST /rutas/planificar` | `{paradas:[id,...]}`; de 2 a 8 IDs ordenados | Contrato posterior: `200` paradas con coordenadas disponibles para dibujar en mapa. No calcula kilometraje, tiempo de traslado ni ruta vial. |

## Esquema `SearchIntent`

```json
{
  "intencion": "comer",
  "categorias": ["gastronomia"],
  "tipo_comida": ["tradicional oaxaqueña"],
  "presupuesto_maximo_mxn": 200,
  "preferencia_presupuesto": null,
  "ambiente": [],
  "companeros": null,
  "zona_texto": null,
  "duracion_max_min": null,
  "pregunta_aclaratoria": null
}
```

`intencion` pertenece a un enum backend; listas y textos tienen límites de tamaño; `presupuesto_maximo_mxn` y `duracion_max_min` son enteros positivos acotados; las categorías deben ser slugs existentes. Gemma no produce coordenadas, IDs, SQL ni nombres de establecimientos. Solo se fijan importes máximos numéricos cuando la persona los expresa. “Económico” permanece como preferencia cualitativa.

La ubicación del navegador es opcional y la gestiona el frontend para centrar el mapa. No se envía a Gemma ni se usa para filtrar resultados por cercanía en el MVP.

## Reglas de resultados

- Un máximo de presupuesto excluye lugares sin precio verificado o con unidad incompatible.
- Ningún filtro obligatorio se amplía automáticamente cuando falten resultados.
- Las recomendaciones se generan a partir de registros devueltos por Chroma; las explicaciones solo usan datos verificados de esos registros.
- La caída de Ollama no desactiva la búsqueda tradicional. Si Chroma no está disponible, las rutas que lo requieren responden `503` sin simular resultados.
