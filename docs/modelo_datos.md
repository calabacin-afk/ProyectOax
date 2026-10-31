# Modelo de datos inicial con Chroma

Chroma organiza los registros en colecciones y guarda documentos, embeddings e información de metadatos. En este diseño es el almacén único del MVP; no se usa una base relacional aparte.

## Colecciones previstas

| Colección | ID del registro | Contenido principal | Estado |
|---|---|---|---|
| `lugares_qwen3_embedding_0_6b_v1` | `lugar_id` estable | Documento descriptivo verificado, embedding y metadatos de búsqueda | MVP |
| `categorias_v1` | `categoria_id` | Nombre, slug y estado | MVP |
| `usuarios_v1` | `usuario_id` | Nombre, email normalizado, hash de contraseña y rol | Posterior; nunca contraseña en texto claro |
| `favoritos_v1` | `usuario_id:lugar_id` | IDs de usuario y lugar, fecha de creación | Posterior |
| `preferencias_v1` | `usuario_id` | Preferencias consentidas del usuario | Posterior |
| `opiniones_v1` | `opinion_id` | Autor real, lugar, calificación, texto y estado de moderación | Posterior |
| `fotografias_v1` | `fotografia_id` | URL/ruta, texto alternativo, fuente, licencia y atribución | Posterior |
| `fuentes_lugar_v1` | `fuente_id` | Lugar, dato respaldado, fuente, revisión y responsable | MVP |

Las relaciones entre colecciones se guardan como IDs en metadatos y las valida el backend. Chroma no impone claves foráneas, unicidad de email entre usuarios ni transacciones que cubran varias colecciones. Esas reglas requieren validación de aplicación y pruebas de concurrencia antes de habilitar escritura multiusuario.

## Registro de lugar

- **ID:** UUID o slug estable generado por el backend. No se deriva del nombre visible.
- **Documento:** texto combinado para recuperación semántica, usando exclusivamente campos verificados: nombre, descripción, categorías y etiquetas.
- **Metadatos escalares:** `categoria_slug`, `estado_verificacion`, `precio_min_mxn`, `precio_max_mxn`, `precio_base`, `zona_slug`, `latitud`, `longitud`, `embedding_model` y `embedding_version`.
- **Opcionales:** dirección, contacto, horarios, precio, coordenadas y enlaces a fotos. Ausentes/desconocidos se omiten o marcan como pendientes; no se inventan.
- **Fotografías:** se guardan fuera de Chroma como archivos u objetos con licencia/fuente registrada; Chroma almacena la referencia y atribución. No incrustar imágenes remotas sin permiso.

En Chroma los metadatos deben ser valores escalares compatibles con su API; listas de etiquetas se normalizan como registros separados o se usan en el documento. Las coordenadas son solo para dibujar marcadores. El MVP no calculará ni filtrará por radio, distancia ni “cercanía”.

## Embeddings

- Candidato elegido para pruebas: `qwen3-embedding:0.6b` mediante Ollama.
- La documentación del modelo indica dimensión de 1024; el servicio debe comprobar que el vector recibido mida exactamente eso antes de escribirlo.
- Cada colección de embeddings tiene versión en su nombre y registra el modelo en los metadatos de colección y de cada registro.
- No se mezclan vectores de modelos distintos. Al cambiar modelo se crea colección nueva y se reindexan los lugares.
- No se configura un `embedding_function` ejecutable dentro de Chroma; el backend obtiene el vector de Ollama y manda `embeddings` explícitos.

## Búsqueda y validación

- Los campos exactos y rangos (por ejemplo, categoría o presupuesto máximo) se traducen a filtros `where` construidos por el backend. Nunca se pasa directamente al cliente Chroma una estructura arbitraria recibida del navegador o del modelo.
- Los lugares con presupuesto desconocido no califican cuando la persona fija un máximo estricto.
- La similitud semántica ordena candidatos reales. Las explicaciones usan campos devueltos por Chroma; Gemma no inventa fichas, precios, coordenadas ni reseñas.
- Para actualizaciones, el backend mantiene un identificador estable y usa operaciones de colección explícitas. Se conserva procedencia por campo en `fuentes_lugar_v1`.

## Datos de prueba y respaldo

No se sembrarán lugares ficticios presentados como reales. Si se crean registros sintéticos para pruebas, se marcarán claramente como tales y nunca se mezclarán con el catálogo público. Respaldar el volumen `chroma_data` con la aplicación detenida y documentar cómo restaurarlo antes de ingresar datos reales.
