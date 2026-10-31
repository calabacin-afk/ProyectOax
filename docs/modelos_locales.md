# Modelos locales y hardware

## Equipo informado

- Ryzen 9 8940HX
- 24 GB RAM DDR5
- RTX 5060 Laptop con 8 GB de VRAM GDDR7
- SSD de 1 TB

Cada integrante debe medir su propia computadora; la misma etiqueta Ollama no garantiza la misma velocidad o reparto GPU/CPU.

## Gemma 4

El catálogo de Ollama publica actualmente `gemma4:e2b` y `gemma4:e4b`. Las variantes 26B A4B y 31B exceden la VRAM disponible para una ejecución completamente en GPU: las cifras Q4 de referencia de Google son aproximadamente 14.4 GB y 17.5 GB solo para cargar el modelo. En una laptop de 8 GB no son recomendación para el MVP.

Google estima memoria Q4 de alrededor de 2.9 GB para E2B y 4.5 GB para E4B, antes de sumar contexto y el runtime. Ollama publica varios artefactos/cuants por etiqueta con tamaños distintos. Para iniciar pruebas locales se recomienda E2B por margen de memoria; E4B se puede comparar con consultas cortas y contextos pequeños. La elección final depende de una medición real de VRAM, RAM y tiempo de respuesta.

Instalación y prueba para la futura fase de interpretación:

```powershell
ollama pull gemma4:e2b
ollama run gemma4:e2b
```

El proyecto ya tiene `GEMMA_MODEL`, pero todavía no realiza peticiones al modelo. Gemma no forma parte de las rutas ejecutadas hasta implementar su servicio, esquema validado, manejo de fallos y pruebas. La app actual sigue sirviendo búsquedas tradicionales aunque Ollama esté apagado.

## Embeddings actualmente conectados

La administración genera un vector por ficha con `qwen3-embedding:0.6b` mediante `POST /api/embed` de Ollama. La familia Qwen3 Embedding es multilingüe y declara soporte para más de 100 idiomas. La configuración de este proyecto usa 1024 dimensiones; el backend rechaza respuesta con dimensión o valores no válidos.

```powershell
ollama pull qwen3-embedding:0.6b
ollama run qwen3-embedding:0.6b
```

Cada colección de lugares tiene modelo y dimensión versionados en los metadatos. No se comparan ni mezclan vectores de modelos distintos. La búsqueda semántica de consultas aún no está conectada, por lo que falta evaluar calidad de recuperación en español antes de presentarla como funcionalidad.

## Variables locales

```dotenv
OLLAMA_URL=http://localhost:11434
GEMMA_MODEL=gemma4:e2b
EMBEDDING_MODEL=qwen3-embedding:0.6b
EMBEDDING_DIMENSION=1024
OLLAMA_TIMEOUT_SECONDS=45
```

En Docker Desktop, la app usa `host.docker.internal:11434` para Ollama instalado en Windows. No expongas el puerto de Ollama a redes públicas.

## Licencias y verificación

Gemma es open-weight con condiciones de uso de Google; hay que revisar y cumplir los [términos de Gemma](https://ai.google.dev/gemma/terms) antes de redistribuir pesos o preparar entrega pública. Qwen3 Embedding se publica con licencia Apache-2.0 en su repositorio/model card; vuelve a verificar los términos del artefacto exacto usado.

Fuentes principales:

- [Etiquetas disponibles en Ollama Gemma 4](https://ollama.com/library/gemma4)
- [Requisitos estimados de memoria de Google](https://ai.google.dev/gemma/docs/core?hl=es-419)
- [Términos de uso de Gemma](https://ai.google.dev/gemma/terms)
- [Qwen3 Embedding en Ollama](https://ollama.com/library/qwen3-embedding)
- [Modelo Qwen3 Embedding](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
