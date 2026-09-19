# Architecture

**Analysis Date:** 2026-05-02

## Pattern Overview

**Overall:** Multi-tier data pipeline with a MCP server query layer

The codebase is a data engineering pipeline with three independent subsystems that share a single PostgreSQL database:
1. **Scraper** — fetches raw ordinance HTML → saves `.txt` files to filesystem
2. **Processor** — reads `.txt` files/DB rows → calls DeepSeek API → enriches DB with structured metadata
3. **MCP Server** — serves the enriched DB to AI assistants via 12 tools over stdio JSON-RPC

**Key Characteristics:**
- No web framework or HTTP server — the server is a stdio-based MCP process
- Two parallel database abstraction layers exist: raw `pg.Pool` (MCP server) and Drizzle ORM (processor)
- AI enrichment is a one-time batch pipeline (`procesado_ia=false` → `procesado_ia=true`)
- Embeddings for semantic search are generated on-demand and cached in `embeddings_cache`

## Layers

**Scraper Layer:**
- Purpose: Download ordinance texts from the HCD Saladillo website
- Location: `src/scraper/`, `app.ts`
- Contains: Playwright browser automation, HTML link extraction, file I/O
- Depends on: Filesystem, external website `hcd.saladillo.gob.ar`
- Used by: Developer runs manually; output goes to year directories

**Database Layer:**
- Purpose: Define schema and provide query interface
- Location: `src/db/schema.ts`, `src/db/index.ts`, `src/mcp-server/db.ts`
- Contains: Drizzle schema, Drizzle db client (processor), raw pg.Pool (MCP server)
- Note: Two separate pool instances with no shared state
- Depends on: PostgreSQL at `DATABASE_URL`

**Processor Layer:**
- Purpose: Enrich raw ordinance text with structured metadata via DeepSeek API
- Location: `src/processor/`
- Contains: Concurrent worker pool, circuit breaker, DB batcher, prompt engineering, JSON parser
- Depends on: `src/db/index.ts` (Drizzle), DeepSeek API, prompts from `src/processor/prompts.ts`
- Used by: Developer runs as one-shot batch: `npx tsx src/processor/concurrent-deepseek.ts`

**MCP Server Layer:**
- Purpose: Expose ordinance data as MCP tools to Claude Code and other MCP clients
- Location: `src/mcp-server/index.ts`
- Contains: McpServer instantiation, tool registration loop, graceful shutdown
- Depends on: `src/mcp-server/db.ts`, `src/mcp-server/tools/`, `src/mcp-server/logger.ts`
- Used by: Claude Code via `.mcp.json` configuration (stdio subprocess)

**Tools Layer:**
- Purpose: Implement each MCP tool's query logic and response formatting
- Location: `src/mcp-server/tools/`
- Contains: Tool definitions (name, description, inputSchema) and handlers (query → JSON response)
- Depends on: `src/mcp-server/db.ts` (query), `src/mcp-server/types.ts` (Zod schemas), optional AI clients
- Pattern: Each tool file exports `{name}Tool` object + `{name}Handler` async function

## Data Flow

**Scraping pipeline:**
1. `app.ts` or `src/scraper/scraper-playwright.ts` fetches paginated HTML from `hcd.saladillo.gob.ar`
2. HTML is parsed with JSDOM or Playwright to extract ordinance links
3. Each ordinance page is fetched individually
4. Text is saved to `./{year}/Ordenanza N° {number}.txt`

**Ingestion to DB:**
1. `src/processor/ingest.ts` (or similar) reads `.txt` files and inserts rows into `ordenanzas` table with `procesado_ia=false`

**AI Processing pipeline:**
1. `src/processor/concurrent-deepseek.ts` queries `WHERE procesado_ia = false`
2. 6 concurrent `DeepSeekWorker` instances pull tasks from a `TaskQueue`
3. Each worker calls DeepSeek API with full ordinance text
4. `parseExtractionResponse()` parses the JSON response into `ExtractionResult`
5. `DatabaseBatcher` accumulates results and flushes in batches of 5 to PostgreSQL
6. Transactional insert: ordinanza metadata + articles + entities + categories + references + amounts + annexes
7. On completion, `procesado_ia=true` and `version_prompt` is set

**MCP query flow:**
1. Claude Code launches MCP server via `npx tsx src/mcp-server/index.ts` (stdio)
2. Client sends JSON-RPC tool call over stdin
3. `McpServer` dispatches to registered handler
4. Handler validates input with Zod, executes PostgreSQL query via `query()` helper
5. Result is JSON-serialized into `content[0].text` and returned over stdout

**Semantic similarity flow:**
1. `similar_ordenanzas` tool called with `ordenanza_id`
2. `getOrCreateEmbedding()` checks `embeddings_cache`; if miss, calls OpenAI `text-embedding-3-small`
3. `getAllEmbeddingsForSimilarity()` loads ALL cached embeddings into Node.js memory
4. Cosine similarity computed in-memory over all embeddings
5. Results filtered by threshold, sorted, sliced

**State Management:**
- No in-process state — all state lives in PostgreSQL
- Exception: cosine similarity search loads all embeddings into memory per request

## Key Abstractions

**Tool (MCP):**
- Purpose: A named capability exposed to AI clients
- Examples: `src/mcp-server/tools/search.ts`, `src/mcp-server/tools/by-id.ts`
- Pattern: `{ tool: { name, title, description, inputSchema }, handler: async (args, ctx) => MCP response }`

**Ordenanza:**
- Purpose: Core domain entity — a municipal ordinance
- Examples: `src/db/schema.ts` (DB), `src/mcp-server/types.ts` (API types)
- Fields: `id` (UUID), `numero` (int), `anio` (int), `titulo`, `texto_completo`, `resumen`, `estado`, articles, entities, categories, references, amounts, annexes

**ExtractionResult:**
- Purpose: Structured output from DeepSeek API processing
- Location: `src/processor/parser.ts`
- Contains: All enrichment fields (resumen, palabras_clave, articulos, entidades, categorias, referencias, montos, anexos)

**CircuitBreaker / TaskQueue / DatabaseBatcher:**
- Purpose: Resilience and throughput control for batch processor
- Location: `src/processor/concurrent-deepseek.ts`

## Entry Points

**Legacy Scraper:**
- Location: `app.ts`
- Triggers: `npx tsx app.ts`
- Responsibilities: Fetch + parse + save ordinances from 2025 (hardcoded year loop)

**Current Scraper:**
- Location: `src/scraper/scraper-playwright.ts`
- Triggers: `npm run scrape:playwright`
- Responsibilities: Playwright-based scrape of pages 1–4, structured downloads

**Processor:**
- Location: `src/processor/concurrent-deepseek.ts`
- Triggers: `npx tsx src/processor/concurrent-deepseek.ts [--all]`
- Responsibilities: Batch AI extraction of all unprocessed ordinances

**MCP Server:**
- Location: `src/mcp-server/index.ts`
- Triggers: Claude Code via `.mcp.json`; or manually `npx tsx src/mcp-server/index.ts`
- Responsibilities: Serve 12 tools, manage DB pool lifecycle

## Error Handling

**Strategy:** Catch-and-return in MCP tools; crash-fast in processor

**Patterns:**
- MCP tools: all handlers wrap logic in `try/catch`; errors return `{ isError: true, content: [{ type: "text", text: JSON.stringify({ error: "..." }) }] }`
- Processor: per-item errors are caught and marked as `ERROR_v1` in the DB via `DatabaseBatcher.markAsError()`; fatal errors exit with `process.exit(1)`
- DB query failures in `src/mcp-server/db.ts`: re-thrown after logging
- Circuit breaker in processor opens after 5 consecutive failures, cooldown 60s

## Cross-Cutting Concerns

**Logging:**
- MCP server: Pino logger to stderr (`src/mcp-server/logger.ts`). Use `logger.info(data, message)` (Pino API — data object first, message string second).
- Processor: `console.log` / `console.error` directly (no structured logging)
- Tool-level logging via `toolLogger(toolName)` wrapper in `src/mcp-server/utils.ts`

**Validation:**
- All MCP tool inputs validated via Zod v4 schemas in `src/mcp-server/types.ts`
- Schemas imported as `import * as z from "zod/v4"`
- DB constraints enforce business rules (positive numero, valid anio range, etc.)

**Authentication:**
- None — MCP server is trusted local process; no auth between Claude Code and MCP server

---

*Architecture analysis: 2026-05-02*
