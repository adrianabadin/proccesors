# External Integrations

**Analysis Date:** 2026-05-02

## APIs & External Services

**AI Extraction / Summarization:**
- DeepSeek API (`https://api.deepseek.com`) - Ordinance structured extraction (articles, entities, categories, references)
  - SDK/Client: `openai` package configured with custom `baseURL`
  - Model: `deepseek-chat` (configurable via `MODEL` env var)
  - Auth: `DEEPSEEK_API_KEY`
  - Used in: `src/processor/concurrent-deepseek.ts`

- Groq API (`https://api.groq.com/openai/v1`) - LLM summaries on demand
  - SDK/Client: `openai` package configured with custom `baseURL`
  - Model: `llama-3.3-70b-versatile`
  - Auth: `GROQ_API_KEY`
  - Used in: `src/mcp-server/llm.ts`

**AI Embeddings:**
- OpenAI API - Semantic similarity embeddings
  - SDK/Client: `openai` package with default `baseURL`
  - Model: `text-embedding-3-small` (1536 dimensions)
  - Auth: `OPENAI_API_KEY`
  - Note: `.env.example` shows `OPENAI_API_KEY` may be set to a Groq key — appears interchangeable if Groq supports OpenAI embeddings API
  - Used in: `src/mcp-server/embeddings.ts`

**Web Scraping Target:**
- HCD Saladillo (`https://hcd.saladillo.gob.ar`) - Municipal ordinances source website
  - Pagination pattern: `/?f1={year}&wpcfs=preset-1`, `/page/{n}/?f1={year}&wpcfs=preset-1`
  - No auth required; scraper uses spoofed Chrome User-Agent
  - Used in: `app.ts` (legacy), `src/scraper/scraper-playwright.ts` (current)

## Data Storage

**Databases:**
- PostgreSQL (primary) at `thecodersteam.com:5432/ordenanzas`
  - Connection: `DATABASE_URL` env var
  - Two separate clients:
    - `src/mcp-server/db.ts` — raw `pg.Pool` (max 20 connections), used by all MCP tools
    - `src/db/index.ts` — Drizzle ORM wrapping `pg.Pool`, used by processor pipeline
  - Schema defined in `src/db/schema.ts` (Drizzle) and `database/schema.sql` (SQL)

**File Storage:**
- Local filesystem — scraped `.txt` files saved to year-named directories
  - Pattern: `./{year}/Ordenanza N° {number}.txt`
  - 1986–2025 directories at project root

**Caching (in PostgreSQL):**
- `embeddings_cache` table — stores OpenAI embedding vectors as JSON text strings
  - Schema: `src/db/schema-cache.ts`
  - Unique constraint on `(ordenanza_id, modelo)`
- `resumenes_cache` table — stores Groq-generated summaries
  - Schema: `src/db/schema-cache.ts`
  - Unique constraint on `(ordenanza_id, texto_original, estilo, longitud_palabras)`

## Authentication & Identity

**Auth Provider:**
- None (no user-facing auth)
- MCP server and processor use API keys only
- Scraper uses no authentication (public website)

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- Pino structured JSON to stderr (MCP server: `src/mcp-server/logger.ts`)
- Console.log/console.error directly (processor: `src/processor/concurrent-deepseek.ts`)
- Log levels: `debug`, `info`, `warn`, `error` (configurable via `LOG_LEVEL` env var)
- Dev mode: pino-pretty colored output (when `NODE_ENV=development` or `VERBOSE=true`)

## CI/CD & Deployment

**Hosting:**
- VPS (thecodersteam.com) — processor runs as one-off batch jobs
- MCP server launches as a subprocess from Claude Code via `.mcp.json`

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - PostgreSQL connection string
- `DEEPSEEK_API_KEY` - For processor pipeline
- `OPENAI_API_KEY` - For embeddings (MCP server)
- `GROQ_API_KEY` - For summarization (MCP server)

**Optional env vars:**
- `VERBOSE=true` - Enable debug logging
- `LOG_LEVEL=debug|info|warn|error` - Log verbosity (default: `info`)
- `NODE_ENV=development` - Enables pino-pretty colored output
- `DEEPSEEK_WORKERS=6` - Concurrent workers (processor)
- `DB_BATCH_SIZE=5` - DB batch size (processor)
- `MAX_QUEUE_SIZE=50` - Backpressure queue size (processor)
- `MODEL=deepseek-chat` - DeepSeek model to use
- `BATCH_SIZE=50` - Ordinances per processor run
- `PROCESS_ALL` - Pass `--all` CLI flag to process everything

**Secrets location:**
- `.env` file at project root (gitignored)
- `.mcp.json` at project root (gitignored) — contains hardcoded DB credentials and API keys

## Webhooks & Callbacks

**Incoming:** None

**Outgoing:** None

---

*Integration audit: 2026-05-02*
