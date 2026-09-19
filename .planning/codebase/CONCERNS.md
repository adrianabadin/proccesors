# Codebase Concerns

**Analysis Date:** 2026-05-02

## Tech Debt

**Two separate database connection pools:**
- Issue: `src/mcp-server/db.ts` uses raw `pg.Pool` (max 20); `src/db/index.ts` uses Drizzle wrapping another `pg.Pool` with no configured limits. These are independent pools that don't share connections.
- Files: `src/mcp-server/db.ts`, `src/db/index.ts`
- Impact: Double the connections consumed when both subsystems run simultaneously; no unified connection limit management; schema drift possible since both have access to the DB
- Fix approach: Either unify on a single pool/client exported from one module, or document the intended separation clearly

**Duplicate utility functions:**
- Issue: `cosineSimilarity`, `parseVector`/`parseEmbeddingVector`, `formatVector`/`formatEmbeddingVector` are duplicated between `src/mcp-server/utils.ts` and `src/mcp-server/embeddings.ts`
- Files: `src/mcp-server/utils.ts` lines 103–165, `src/mcp-server/embeddings.ts` lines 172–265
- Impact: Changes must be made in two places; risk of divergence
- Fix approach: Remove duplicates from `embeddings.ts`; import from `utils.ts`

**Processor uses `console.log` instead of structured logging:**
- Issue: `src/processor/concurrent-deepseek.ts` uses raw `console.log` with emoji output
- Files: `src/processor/concurrent-deepseek.ts`
- Impact: Inconsistent log format; cannot filter/query processor logs programmatically; emoji pollution in VPS logs
- Fix approach: Import pino logger from a shared module or at least a local pino instance

**`app.ts` is a prototype, not production code:**
- Issue: Root-level `app.ts` is an unstructured script with hardcoded year (2025), no config module, variable shadowing, and unsafe callbacks
- Files: `app.ts`
- Impact: Unmaintainable; produces `undefined/` directory bug; replaced by `src/scraper/`
- Fix approach: Remove or archive `app.ts`; direct all usage to `src/scraper/scraper-playwright.ts`

## Known Bugs

**`undefined/` directory creation:**
- Symptoms: A directory named `undefined` exists at project root containing ordinance files
- Files: `app.ts` line 80 — `const anio = title.split("/")[1]`
- Trigger: When ordinance title does not contain `/` (no year suffix), `anio` is `undefined`, path becomes `./undefined/`
- Workaround: Manual cleanup of `undefined/` directory; not present in new scraper (`src/scraper/`)

**Variable shadowing in `app.ts`:**
- Symptoms: Outer `mainPage` (line 5) and inner `mainPage` (line 14) both declared with `const` in same scope chain
- Files: `app.ts` lines 5 and 14
- Trigger: TypeScript `strict` mode should catch this; however `app.ts` is not in `tsconfig.json` include
- Impact: Outer variable is inaccessible after inner declaration; first page is fetched but ignored

**`getAllEmbeddingsForSimilarity` returns incomplete type:**
- Symptoms: Return type declared as `Array<{ id, ordenanza_id, vector }>` but the query also selects `numero`, `anio`, `titulo`, `resumen`; those fields used in caller (`similar.ts`) are not typed
- Files: `src/mcp-server/embeddings.ts` lines 127–148
- Impact: TypeScript does not catch misuse of the extra fields; `emb.numero`, `emb.anio`, etc. accessed but typed as `any`

**`getOrCreateEmbedding` passes empty string for `textoCompleto`:**
- Symptoms: `similar.ts` calls `getOrCreateEmbedding(args.ordenanza_id, "")` — passes empty text
- Files: `src/mcp-server/tools/similar.ts` line 44, `src/mcp-server/embeddings.ts` lines 83–120
- Trigger: When embedding not in cache, `generateEmbedding("")` is called, generating a useless embedding for empty text
- Fix approach: Query `texto_completo` from DB first; pass it to `getOrCreateEmbedding`

**Test suite non-runnable:**
- Symptoms: `src/mcp-server/tests/tools.test.ts` imports `vitest` which is not in `package.json`
- Files: `src/mcp-server/tests/tools.test.ts`, `package.json`
- Trigger: Running any test command
- Fix approach: `npm install --save-dev vitest`

**Test mocks never injected:**
- Symptoms: `mockDB.query` is defined in test file but `searchOrdenanzasTool.handler()` internally imports real `query` from `../db.js` — mock has no effect
- Files: `src/mcp-server/tests/tools.test.ts`
- Trigger: Running the tests against a real DB or a DB that's offline
- Fix approach: Add `vi.mock("../db.js", () => ({ query: vi.fn(), execute: vi.fn() }))` at top of test file

## Security Considerations

**Credentials committed in `.mcp.json`:**
- Risk: `.mcp.json` contains hardcoded `DATABASE_URL` with password and `GROQ_API_KEY` in plaintext
- Files: `.mcp.json`
- Current mitigation: `.mcp.json` is gitignored
- Recommendations: Confirm `.mcp.json` stays gitignored; consider using `.env` reference instead of hardcoding in `.mcp.json`

**`solo_vigentes` filter via string interpolation:**
- Risk: The `solo_vigentes` parameter in `search.ts` is injected via template literal directly into SQL
- Files: `src/mcp-server/tools/search.ts` line 60
- Code: `` ${args.solo_vigentes ? "AND o.estado IN ('vigente', 'modificada')" : ""} ``
- Current mitigation: `solo_vigentes` is a boolean (Zod-validated), so the interpolated value is always one of two fixed strings — not user-supplied text. True SQL injection is not possible with a boolean.
- Recommendation: While not exploitable, this pattern is fragile. Prefer parameterized approach or explicit SQL branches.

**`ILIKE` with user-supplied `%` wildcards in entity search:**
- Risk: `by-entity.ts` constructs `e.nombre ILIKE $1` with `%${args.nombre}%` — this is parameterized correctly
- Files: `src/mcp-server/tools/by-entity.ts` line 31-32
- Current mitigation: Value is passed as query parameter, not interpolated. Not vulnerable to SQL injection.
- Recommendation: If `args.nombre` contains `%` or `_` and exact matching is desired, escape wildcards before wrapping

## Performance Bottlenecks

**In-memory cosine similarity over all embeddings:**
- Problem: `getAllEmbeddingsForSimilarity()` loads ALL embedding vectors into Node.js memory every time `similar_ordenanzas` is called
- Files: `src/mcp-server/embeddings.ts` lines 127–148, `src/mcp-server/tools/similar.ts`
- Cause: No pgvector extension; similarity computed in JavaScript
- Impact: With thousands of ordinances at 1536 float dimensions each, a single request loads ~tens of MB; memory grows with corpus; response latency scales linearly
- Improvement path: Install pgvector on PostgreSQL and use `<=>` cosine distance operator; or add an in-process cache with invalidation

**N+1 query pattern in `get_ordenanza`:**
- Problem: `getOrdenanzaHandler` executes 7 separate sequential DB queries (main row + articulos + entidades + categorias + referencias + montos + anexos)
- Files: `src/mcp-server/tools/by-id.ts` lines 37–141
- Cause: Each relationship loaded separately, not JOINed
- Impact: 7 round-trips per `get_ordenanza` call; multiplied under concurrent usage
- Improvement path: Use a single query with JSON aggregation (similar to how `search_ordenanzas` aggregates categories with `jsonb_agg`)

**Connection pool exhaustion:**
- Problem: `src/mcp-server/db.ts` pool `max: 20`; `src/db/index.ts` pool has no `max` set (defaults to 10)
- Files: `src/mcp-server/db.ts` line 24, `src/db/index.ts` line 6
- Cause: No coordination between pools; each concurrent MCP tool call holds a connection
- Impact: At ~10 concurrent MCP requests the pool exhausts, subsequent queries queue or timeout (5s timeout configured)
- Improvement path: Lower pool max if on a shared server; add connection monitoring

## Fragile Areas

**MCP server logging to stderr:**
- Files: `src/mcp-server/logger.ts`
- Why fragile: If any code in the MCP server writes to stdout (e.g., a `console.log` accidentally added), it corrupts the JSON-RPC protocol and the entire MCP connection silently breaks
- Safe modification: Always use `logger.info/debug/error/warn(...)` from `src/mcp-server/logger.ts`; never use `console.log` in any file imported by the MCP server
- Test coverage: None

**`tools/index.ts` import pattern:**
- Files: `src/mcp-server/tools/index.ts`
- Why fragile: Uses explicit `import { ... } from "./search.js"` then re-exports. Adding a new tool requires: (1) create tool+handler, (2) add import, (3) add to re-export list, (4) add to `ALL_TOOLS` array — four separate touch points that must stay in sync
- Safe modification: Follow the existing four-step pattern precisely when adding tools

**`src/db/index.ts` pool has no configured limits:**
- Files: `src/db/index.ts`
- Why fragile: Drizzle pool defaults to `pg` defaults (10 connections). No `connectionTimeoutMillis` or `idleTimeoutMillis` set. Under processor load, connections may leak or accumulate
- Safe modification: Processor always calls `await pool.end()` at the end of `main()` — ensure this is not removed

## Scaling Limits

**Semantic similarity search:**
- Current capacity: Works for small corpora (< ~1000 ordinances cached)
- Limit: Memory-bound; 10,000 ordinances × 1536 floats × 8 bytes ≈ 120MB per request just for vector data
- Scaling path: pgvector extension with HNSW index; schema already has commented instructions in `src/db/schema-cache.ts`

**Batch processor queue:**
- Current capacity: `MAX_QUEUE_SIZE=50` ordinances enqueued; anything beyond is dropped with a warning
- Limit: Ordinances after position 50 in a run are rejected
- Scaling path: Increase `MAX_QUEUE_SIZE` or implement pagination over multiple runs; `--all` flag processes up to 10,000

## Dependencies at Risk

**`@xenova/transformers` (former dependency):**
- Risk: Referenced in `CLAUDE.md` (historical) but not in current `package.json`
- Impact: No current risk; indicates past dependency cleanup was done
- Migration plan: Already removed

**`vitest` missing from `package.json`:**
- Risk: Test framework not installed; CI would fail if configured
- Impact: All tests in `src/mcp-server/tests/` cannot run
- Migration plan: `npm install --save-dev vitest`

**`axios` unused:**
- Risk: Listed in `dependencies` but not observed in any active code path
- Impact: Unnecessary production bundle weight
- Migration plan: `npm uninstall axios` after confirming no usage

## Missing Critical Features

**No database migration tooling:**
- Problem: No `drizzle-kit` in `package.json`; no migration files directory
- Blocks: Cannot safely evolve schema in production without manual SQL
- Recommendation: Add `drizzle-kit` and generate migration files from `src/db/schema.ts`

**No health monitoring or alerting:**
- Problem: `health_check` MCP tool exists but only checks DB connectivity; no proactive monitoring
- Blocks: Cannot detect processor failures, API quota exhaustion, or DB degradation without manual inspection

## Test Coverage Gaps

**MCP tool handlers (real DB path):**
- What's not tested: All tool handlers execute against the real database (mock never injected)
- Files: `src/mcp-server/tests/tools.test.ts`
- Risk: Handler bugs caught only in production
- Priority: High

**Processor pipeline:**
- What's not tested: `DatabaseBatcher`, `CircuitBreaker`, `TaskQueue`, `DeepSeekWorker`, `parseExtractionResponse`
- Files: `src/processor/concurrent-deepseek.ts`, `src/processor/parser.ts`
- Risk: Processing errors or data corruption undetected until DB inspection
- Priority: High

**Scraper:**
- What's not tested: Link extraction, content parsing, file saving, retry logic
- Files: `src/scraper/`
- Risk: Website layout changes silently break scraping
- Priority: Medium

**Database schema constraints:**
- What's not tested: No integration tests for constraint violations, cascade deletes, unique index behavior
- Files: `src/db/schema.ts`, `database/schema.sql`
- Risk: Bad data inserted silently
- Priority: Medium

---

*Concerns audit: 2026-05-02*
