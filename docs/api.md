# Contratos iniciales de API

Todas las respuestas de éxito usan `{"data": ..., "meta": ...}`. Los errores usan `{"error":{"codigo":"...","mensaje":"...","detalles":...}}`.

## Errores comunes

- `400`: JSON o parámetros mal formados.
- `401`: sesión requerida o credenciales inválidas.
- `403`: permisos insuficientes o token CSRF inválido.
- `404`: recurso inexistente.
- `409`: conflicto, por ejemplo un registro duplicado.
- `422`: cuerpo válido como JSON pero inválido según el esquema.
- `429`: límite de solicitudes excedido.
- `503` / `504`: dependencia requerida no disponible o agotó el tiempo.

## Endpoints

| Método y ruta | Entrada | Respuesta y reglas |
|---|---|---|
| `POST /auth/registro` | `{nombre,email,password}` | `201` perfil básico; correo único, contraseña validada y guardada con Argon2id. |
| `POST /auth/login` | `{email,password}` | `200` sesión y perfil; `401` mensaje genérico. |
| `POST /auth/logout` | Sesión y CSRF | `204`; invalida la sesión. |
| `GET /categorias/` | Sin cuerpo | `200` categorías activas. |
| `GET /lugares/` | Query: `q`, `categoria`, `etiqueta`, `precio_max_mxn`, `lat`, `lon`, `radio_km`, `pagina`, `limite` | `200` lista paginada. `lat`/`lon` deben venir juntos; un radio necesita origen. |
| `GET /lugares/<id>` | ID en ruta | `200` ficha pública; `404` si no existe o no es pública. |
| `POST /lugares/` | Campos de lugar, fuentes y fotos | `201` estado inicial `pendiente`; solo rol administrador. |
| `PUT /lugares/<id>` | Representación completa editable | `200`; solo administrador, con validaciones y procedencia. |
| `POST /busqueda/` | `{consulta?, filtros?, origen?}` | `200` búsqueda tradicional; no requiere IA. |
| `POST /ia/interpretar` | `{consulta}` | `200` `SearchIntent` validado; `503`/`504` si Gemma no responde. |
| `POST /ia/buscar` | `{consulta, filtros_confirmados?, origen?}` | `200` resultados existentes y `modo`; degradación a texto tradicional si Gemma falla. |
| `POST /ia/sorprendeme` | Presupuesto o sin límite, origen, distancia máxima; tiempo opcional | `200` candidatos elegibles. Presupuesto/distancia indicados son límites estrictos. |
| `GET /favoritos/` | Sesión autenticada | `200` lista del usuario. |
| `POST /favoritos/<lugar_id>` | Sesión autenticada | `201` favorito guardado; operación idempotente. |
| `DELETE /favoritos/<lugar_id>` | Sesión autenticada | `204` favorito eliminado. |
| `POST /rutas/planificar` | `{paradas:[id,...]}`; de 2 a 8 IDs en orden | `200` itinerario. Sin motor vial, geometría/distancia/tiempo serán `null`. |

## Esquema `SearchIntent`

Campos propuestos: `intencion` (enum), `categorias` (slugs conocidos), `tipo_comida`, `presupuesto_maximo_mxn`, `preferencia_presupuesto`, `ambiente`, `companeros`, `zona_texto`, `radio_km`, `duracion_max_min`, `requiere_ubicacion` y `pregunta_aclaratoria`.

Un monto máximo solo se fija si la persona lo expresa numéricamente. Una preferencia como “económico” es cualitativa y no se convierte en una cifra. El modelo no devuelve coordenadas, identificadores de lugares ni SQL. La ubicación del navegador se envía por separado, con consentimiento.

## Restricciones de recomendación

- Un límite de presupuesto excluye fichas sin precio conocido o con unidad de precio incompatible.
- Un límite de distancia excluye fichas sin coordenadas.
- Si no hay resultados, la aplicación explica qué dato o filtro lo impide; no amplía límites por cuenta propia.
- Las razones de recomendación se construyen con campos recuperados, no con datos generados por el modelo.
