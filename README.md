# Descubre Oaxaca

“No visites solamente Oaxaca. Descúbrela de una manera diferente”.

Aplicación web Flask para explorar lugares con información comprobada, filtrar el catálogo, ver ubicaciones en un mapa, guardar favoritos y administrar fichas. No se incluyen establecimientos de ejemplo: el catálogo empieza vacío para evitar presentar datos inventados como reales.

## Qué funciona en esta versión

- Catálogo responsive con búsqueda por texto, categoría, zona y presupuesto máximo.
- Página de detalle para cada lugar verificado.
- Mapa Leaflet/OpenStreetMap cuando la ficha contiene coordenadas verificadas. La ubicación del visitante es opcional y solo centra el mapa.
- Registro, inicio de sesión y favoritos.
- Panel de administración para agregar fichas, revisar pendientes y publicarlas con una fuente.
- Experiencia “Sorpréndeme” que elige una ficha verificada respetando presupuesto, tiempo, compañía y ambiente cuando esos datos existen.
- API JSON de lectura y búsqueda tradicional en `/api/lugares/`, `/api/lugares/<id>` y `POST /busqueda/`.
- Chroma persistente para catálogo, usuarios y favoritos. Qwen3 Embedding vía Ollama genera vectores cuando está disponible; no es requisito para guardar ni buscar fichas por filtros tradicionales.

**Todavía pendiente:** interpretación de consultas con Gemma 4, recuperación semántica de consultas, reseñas, carga de imágenes, rutas con varias paradas y una API JSON completa para cuentas y administración. La variable `GEMMA_MODEL` está preparada, pero este código aún no llama a Gemma. El catálogo y la búsqueda tradicional siguen funcionando aunque Ollama esté apagado.

## Requisitos

- Windows 10/11, PowerShell y Python 3.13 (también puede usarse otra versión compatible con Chroma).
- Para generar el índice semántico opcional: [Ollama](https://ollama.com/download/windows) con `qwen3-embedding:0.6b` descargado. Guardar fichas no depende de Ollama.
- Docker Desktop solo si se desea ejecutar con Docker Compose.

## Preparar en Windows

En PowerShell, desde la carpeta del proyecto:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Abre `.env` y cambia `SECRET_KEY` si aún conserva el texto `REEMPLAZAR_...`. Puedes crear un valor así:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Pega el resultado después de `SECRET_KEY=`. Inicia la aplicación:

```powershell
python run.py
```

Visita [http://127.0.0.1:5000](http://127.0.0.1:5000). Detén el servidor con `Ctrl+C` en esa misma terminal.

## Crear una cuenta administradora

Con el entorno virtual activo, ejecuta:

```powershell
python -m flask --app run:app crear-admin
```

Escribe el correo, nombre y contraseña cuando el comando los solicite. Después inicia sesión en la página y abre **Administrar**. Las fichas nuevas quedan pendientes hasta que un administrador las revise y agregue una fuente verificable.

## Habilitar embeddings semánticos (opcional)

Instala Ollama y ejecuta estos comandos en una terminal:

```powershell
ollama pull qwen3-embedding:0.6b
ollama list
```

Deja Ollama abierto. La configuración local está en `.env`:

```dotenv
OLLAMA_URL=http://localhost:11434
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024
```

La aplicación valida que Ollama devuelva 1024 valores numéricos antes de guardar el vector. Sin Ollama puedes guardar lugares y usar búsqueda tradicional; el vector queda pendiente. Cuando Ollama esté listo, ejecuta:

```powershell
python -m flask --app run:app generar-embeddings
```

Un cambio futuro de modelo o dimensión requiere una colección Chroma versionada nueva y reindexar las fichas.

## Ejecutar pruebas

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
```

Las pruebas usan un directorio temporal y no cargan lugares a `chroma_data`.

## Docker Compose

Primero crea `.env` y configura `SECRET_KEY` como se indicó arriba. Luego:

```powershell
docker compose up --build -d
docker compose logs -f web
```

La aplicación queda en [http://127.0.0.1:5000](http://127.0.0.1:5000). La base Chroma persiste en el volumen `chroma_data`. Para detener:

```powershell
docker compose down
```

Para Ollama instalado en Windows, Compose usa `host.docker.internal:11434`. No publiques ese puerto de Ollama en Internet.

## Modelos locales y hardware

La laptop informada tiene Ryzen 9 8940HX, 24 GB de RAM, RTX 5060 Laptop de 8 GB y SSD de 1 TB. El catálogo actual de Ollama incluye `gemma4:e2b` y `gemma4:e4b`; Google estima 2.9 GB y 4.5 GB de memoria de modelo Q4, antes de sumar contexto y el resto del runtime. Para empezar la integración local se recomienda medir `gemma4:e2b`; E4B se puede probar como alternativa y verificar consumo real. Los modelos 26B A4B y 31B no son la opción inicial para esta GPU.

```powershell
ollama pull gemma4:e2b
ollama run gemma4:e2b
```

Los nombres y tamaños pueden cambiar. Consulta el [catálogo de Gemma 4 en Ollama](https://ollama.com/library/gemma4) y los [requisitos de memoria de Google](https://ai.google.dev/gemma/docs/core?hl=es-419) al preparar la demo. Aún falta conectar Gemma al flujo de búsqueda y validar sus respuestas en el backend.

## Compartir la aplicación por la misma Wi-Fi

En la laptop que corre Flask, permite conexiones solo en una red privada de confianza:

```powershell
$env:FLASK_HOST="0.0.0.0"
python run.py
```

Ejecuta `ipconfig`, encuentra la IPv4 de Wi-Fi y comparte `http://IP-DE-TU-LAPTOP:5000` con tu compañero. Esto solo comparte la aplicación en ejecución; para compartir código, ambos usan GitHub. Cada equipo debe tener su propio `.env`; no se comparte por Git.

## Datos y privacidad

- Los datos locales viven en `chroma_data/` y están ignorados por Git.
- `.env`, contraseñas, tokens, datos de modelos y registros locales no deben subirse.
- La geolocalización del navegador solo se solicita al pulsar el botón y no se almacena ni envía al servidor.
- Las fichas públicas son las que tienen estado verificado. El presupuesto estricto excluye lugares cuyo precio se desconoce.
- Los mapas usan teselas de OpenStreetMap con atribución. Para tráfico alto o producción, debe configurarse un proveedor que permita ese volumen según sus condiciones.
- La versión de Chroma del proyecto no debe exponerse como servidor HTTP público; el contenedor usa cliente persistente embebido y un solo worker.

## Documentación

- [Arquitectura](docs/arquitectura.md)
- [API disponible y pendiente](docs/api.md)
- [Modelo de datos Chroma](docs/modelo_datos.md)
- [Responsabilidades del equipo](docs/equipo.md)
- [Modelos locales y hardware](docs/modelos_locales.md)

## Git

Usamos `main` para la versión estable, `develop` para integración y ramas `feature/*` para cambios. Cada integrante abre Pull Request hacia `develop`. No subimos `.env`, el volumen `chroma_data`, credenciales, información personal innecesaria ni pesos de modelos.
