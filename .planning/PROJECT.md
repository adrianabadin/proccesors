# Ordenanzas Saladillo MCP — Semantic Search

## What This Is

Extensión del servidor MCP de ordenanzas municipales de Saladillo para agregar búsqueda semántica basada en embeddings vectoriales. El proyecto agrega un script de generación batch de embeddings con OpenAI `text-embedding-3-large` y una nueva herramienta MCP `semantic_search` que permite buscar ordenanzas por similitud conceptual en lugar de coincidencia de texto.

## Core Value

Un asistente de IA puede encontrar ordenanzas relevantes describiendo un concepto o situación en lenguaje natural, sin necesidad de conocer palabras clave exactas.

## Requirements

### Validated

- ✓ 12 herramientas MCP operativas (search, by-id, by-entity, similar, summarize, etc.) — existente
- ✓ `embeddings_cache` table con soporte multi-modelo (`modelo` column, unique en `ordenanza_id + modelo`) — existente
- ✓ Infraestructura de embeddings `text-embedding-3-small` con cosine similarity en memoria — existente
- ✓ Ordenanzas con `resumen` y `palabras_clave` pre-generados en DB — existente
- ✓ Cliente OpenAI configurado y funcional — existente

### Active

- [ ] Script batch para generar embeddings `text-embedding-3-large` para todas las ordenanzas
- [ ] Selección inteligente de texto: texto completo para ordenanzas cortas, resumen para muy largas
- [ ] Rate limiting y progreso visible en el script batch
- [ ] Nueva herramienta MCP `semantic_search` que busca por texto libre
- [ ] Búsqueda semántica retorna ordenanzas con score de similitud

### Out of Scope

- Reemplazar `text-embedding-3-small` existente — coexisten como modelos separados en `embeddings_cache`
- pgvector / búsqueda vectorial nativa en PostgreSQL — se mantiene cosine similarity en memoria
- Re-generación automática de resúmenes — los resúmenes ya existen en DB
- Frontend o interfaz visual — el consumidor es el MCP server

## Context

- **Infraestructura existente:** `embeddings_cache` ya soporta múltiples modelos. El batch script puede insertar con `modelo = 'text-embedding-3-large'` sin conflicto.
- **Dimensiones:** `text-embedding-3-large` produce 3072 dimensiones (vs 1536 del modelo small). El campo `dimensions` en la tabla ya acepta este valor.
- **Herramienta similar existente:** `similar_ordenanzas` usa embeddings on-demand para encontrar similares a una ordenanza dada. `semantic_search` es diferente: busca por texto libre.
- **Threshold de longitud:** Se define durante la implementación (aprox. 8000 chars = ~2000 tokens como límite para usar texto completo vs resumen).
- **Cosine similarity en Node.js:** Funciona bien para el dataset actual. Si el dataset crece significativamente, revisar pgvector.

## Constraints

- **Tech Stack**: TypeScript + Node.js + tsx, sin cambiar stack actual
- **API**: OpenAI `text-embedding-3-large` — requiere `OPENAI_API_KEY` en `.env`
- **DB**: PostgreSQL en `thecodersteam.com:5432/ordenanzas` — sin migraciones destructivas
- **MCP**: Nueva herramienta coexiste con las 12 existentes, no reemplaza ninguna
- **Memoria**: Cosine similarity carga todos los embeddings en memoria — aceptable para dataset actual

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| `text-embedding-3-large` en lugar de `small` | Mayor calidad semántica para búsqueda por concepto | — Pending |
| Texto completo para cortas, resumen para largas | Los resúmenes ya existen; para textos muy largos el embedding del resumen es más representativo | — Pending |
| Nueva herramienta `semantic_search` (no reemplazar `similar_ordenanzas`) | Casos de uso distintos: `similar` busca por ordenanza, `semantic_search` busca por texto libre | — Pending |
| Cosine similarity en memoria (sin pgvector) | Evita dependencia de extensión PostgreSQL que puede no estar disponible en el VPS | — Pending |

---
*Last updated: 2026-05-02 after initialization*
