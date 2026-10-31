# Modelos locales — perfil de demo

## Hardware informado

- AMD Ryzen 9 8940HX, 16 núcleos / 32 hilos.
- 24 GB DDR5.
- NVIDIA RTX 5060 Laptop, 8 GB GDDR7.
- SSD de 1 TB.

La ficha de NVIDIA indica 8 GB GDDR7 para la RTX 5060 Laptop; AMD publica 16 núcleos y 32 hilos para el 8940HX.

## Recomendación inicial

- Gemma principal a medir: `gemma4:e4b`.
- Alternativa de menor consumo: `gemma4:e2b`.
- No usar 26B/31B como configuración estable del hackathon. Sus estimaciones oficiales Q4 rondan 14.4 GB y 17.5 GB, respectivamente; la descarga parcial a RAM/CPU puede ser posible, pero no se asume que tenga latencia adecuada.
- Embeddings candidato: `qwen3-embedding:0.6b`, con 1024 dimensiones en la configuración inicial. Medir calidad sobre consultas en español antes de fijarlo.

Las estimaciones de memoria cambian según cuantización, runtime, contexto y procesos concurrentes. Verificar VRAM y velocidad en la laptop real antes de cerrar la demo.

## Variables

```dotenv
OLLAMA_URL=http://localhost:11434
GEMMA_MODEL=gemma4:e4b
EMBEDDING_MODEL=qwen3-embedding:0.6b
```

Comandos Windows publicados por Ollama para instalar y obtener el modelo:

```powershell
irm https://ollama.com/install.ps1 | iex
ollama pull gemma4:e4b
ollama run gemma4:e4b
ollama pull qwen3-embedding:0.6b
```

En Docker Desktop, la app usa `host.docker.internal` para comunicarse con Ollama instalado en Windows. No exponer el puerto local de Ollama a redes públicas.

## Fuentes

- [Ollama para Windows](https://ollama.com/download/windows)
- [Catálogo Gemma 4 de Ollama](https://ollama.com/library/gemma4)
- [Memoria estimada por Google para Gemma 4](https://ai.google.dev/gemma/docs/core)
- [NVIDIA RTX 50 para laptops](https://www.nvidia.com/en-us/geforce/laptops/50-series/)
- [AMD Ryzen 9 8940HX](https://www.amd.com/en/products/processors/laptop/ryzen/8000-series/amd-ryzen-9-8940hx.html)
- [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
