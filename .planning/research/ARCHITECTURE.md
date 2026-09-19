# Architecture Patterns

**Domain:** Batch embedding generation + semantic search MCP tool
**Researched:** 2026-05-02

---

## Recommended Architecture

### Overview

The new milestone adds two components that slot into the existing multi-tier pipeline without structural changes to any existing layer:

```
[Processor Layer]                      [MCP Server Layer]
  src/processor/
    concurrent-deepseek.ts  (exists)     src/mcp-server/
    generate-embeddings.ts  (NEW)          embeddings.ts        (extend)
                                           tools/similar.ts     (unchanged)
                                           tools/semantic-search.ts  (NEW)
                                           tools/index.ts       (add entry)

[Database Layer — shared, no schema change]
  embeddings_cache (ordenanza_id, modelo) UNIQUE
  ├─ rows with modelo='text-embedding-3-small'  (existing — similar_ordenanzas)
  └─ rows with modelo='text-embedding-3-large'  (new — semantic_search)
```

The two models coexist in `embeddings_cache` by their `modelo` column. The unique constraint is `(ordenanza_id, modelo)`, so `text-embedding-3-large` rows insert cleanly alongside existing `text-embedding-3-small` rows with zero conflict.

---

## Component Boundaries

| Component | Responsibility | Communicates With | Consumes Model |
|-----------|---------------|-------------------|----------------|
| `src/processor/generate-embeddings.ts` | Batch-generate `text-embedding-3-large` embeddings for all ordinances not yet in cache for that model | OpenAI API, `src/mcp-server/db.ts` (pg.Pool) or raw `pg` | `text-embedding-3-large` |
| `src/mcp-server/embeddings.ts` | Per-request get-or-create (on-demand), similarity helpers, cosine similarity math | OpenAI API, `src/mcp-server/db.ts` | `text-embedding-3-small` (default, unchanged) |
| `src/mcp-server/tools/similar.ts` | Find ordinances similar to a given ordinanza ID | `embeddings.ts` | `text-embedding-3-small` (unchanged) |
| `src/mcp-server/tools/semantic-search.ts` | Free-text semantic search using pre-generated large embeddings | `embeddings.ts` (extended), `src/mcp-server/db.ts` | `text-embedding-3-large` |
| `src/mcp-server/tools/index.ts` | Register all tools | imports `semantic-search.ts` | — |

---

## Data Flow

### Batch generation (offline, run once by developer)

```
npx tsx src/processor/generate-embeddings.ts
  │
  ├─ 1. Query DB: SELECT id, texto_completo, resumen FROM ordenanzas
  │        WHERE id NOT IN (
  │          SELECT ordenanza_id FROM embeddings_cache
  │          WHERE modelo = 'text-embedding-3-large'
  │        )
  │        → ~2000 rows on first run, 0 on re-run (resume-safe)
  │
  ├─ 2. For each ordinanza:
  │     text = len(texto_completo) <= 8000 chars ? texto_completo : resumen
  │
  ├─ 3. Rate-limited OpenAI call: embeddings.create({ model: 'text-embedding-3-large', input: text })
  │     → 3072-dimension float array
  │
  ├─ 4. INSERT INTO embeddings_cache (ordenanza_id, modelo, vector, dimensions)
  │        VALUES ($id, 'text-embedding-3-large', $json_array, '3072')
  │        ON CONFLICT (ordenanza_id, modelo) DO UPDATE SET vector = EXCLUDED.vector
  │
  └─ 5. Progress bar / counter to stderr; summary on completion
```

### Semantic search (live, per MCP tool call)

```
Claude Code → MCP tool call: semantic_search({ query: "permisos de construcción", limit: 10 })
  │
  ├─ 1. Generate query embedding:
  │     openai.embeddings.create({ model: 'text-embedding-3-large', input: query })
  │     → 3072-dimension float array  (not cached — query is ephemeral)
  │
  ├─ 2. Load all large-model embeddings from cache:
  │     SELECT ec.ordenanza_id, ec.vector, o.numero, o.anio, o.titulo, o.resumen
  │     FROM embeddings_cache ec JOIN ordenanzas o ON o.id = ec.ordenanza_id
  │     WHERE ec.modelo = 'text-embedding-3-large'
  │
  ├─ 3. Cosine similarity in Node.js memory over all loaded vectors
  │
  ├─ 4. Filter by threshold, sort desc, slice to limit
  │
  └─ 5. Return { resultados: [...], total, query, model }
```

---

## How `embeddings.ts` Should Be Extended

The current `embeddings.ts` has two bugs to fix and one extension to add:

**Bug 1 — `getOrCreateEmbedding` ignores `modelo` column.**
The SELECT and INSERT both omit `modelo`, so they always match the first row regardless of model. When two models exist for the same `ordenanza_id`, this returns the wrong vector.

Fix: Add `AND modelo = $2` to the SELECT and pass `modelo` explicitly to the INSERT.

**Bug 2 — `getAllEmbeddingsForSimilarity` has no `modelo` filter.**
When `text-embedding-3-large` rows exist, this function will mix 1536-dim and 3072-dim vectors in memory. `calculateCosineSimilarity` throws on mismatched lengths.

Fix: Add `WHERE ec.modelo = $1` with `'text-embedding-3-small'` as default parameter.

**Extension — add model-parameterized variants.**

The cleanest approach without breaking `similar.ts` is to add two new exports alongside the existing ones:

```typescript
// New: model-aware versions used by semantic-search and batch script
export async function generateEmbeddingForModel(
  text: string,
  model: 'text-embedding-3-small' | 'text-embedding-3-large'
): Promise<number[]>

export async function getAllEmbeddingsByModel(
  model: 'text-embedding-3-small' | 'text-embedding-3-large'
): Promise<Array<{ ordenanza_id: string; vector: string }>>
```

`similar.ts` continues calling the existing `getOrCreateEmbedding` + `getAllEmbeddingsForSimilarity` after the bug fixes add the missing `modelo` filter — no interface change visible to that file.

`semantic-search.ts` calls `generateEmbeddingForModel` (no caching needed for query text) and `getAllEmbeddingsByModel('text-embedding-3-large')`.

---

## `generate-embeddings.ts` Internal Structure

Mirrors `concurrent-deepseek.ts` patterns but is simpler (no circuit breaker needed; OpenAI embeddings API is far more reliable than a chat completion endpoint):

```
CONFIG block
  BATCH_SIZE = 50          (ordinances fetched per DB page)
  CONCURRENCY = 5          (parallel OpenAI calls — well within RPM limits)
  TEXT_THRESHOLD = 8000    (chars; above this → use resumen)
  MODEL = 'text-embedding-3-large'

main()
  1. Load unembedded ordinances (paginated SELECT, WHERE NOT IN embeddings_cache for this model)
  2. RateLimit wrapper: token bucket or simple p-limit(CONCURRENCY)
  3. For each batch: process concurrently, INSERT results, log progress
  4. Print summary (total processed, skipped, errors, elapsed time)
```

Resume safety is free: the WHERE NOT IN subquery skips already-embedded ordinances. Re-running the script is always safe.

Use `p-limit` (already available in ecosystem, or simple semaphore class) for concurrency. No circuit breaker needed — on API error, log and skip the ordinanza; continue. Re-running the script will pick up skipped ones.

---

## Build Order Implications

1. **Fix `embeddings.ts` first** — both the batch script and the new tool depend on correct model-aware queries. Fixing the bugs before writing the new code avoids writing callers that inherit the broken behavior.

2. **Write `generate-embeddings.ts` second** — the tool is useless without data. The batch script must succeed and populate `embeddings_cache` before the semantic search tool can return meaningful results.

3. **Write `tools/semantic-search.ts` third** — at this point embeddings exist in DB and `embeddings.ts` exports the model-aware helpers.

4. **Register in `tools/index.ts` last** — add import + entry to `ALL_TOOLS`. This is a one-line addition per convention.

---

## Patterns to Follow

### Pattern: Standalone Batch Script
Mirrors `src/processor/concurrent-deepseek.ts` structure:
- `CONFIG` block at top (env-driven, with sensible defaults)
- `main()` async function, called at bottom
- `process.exit(0)` on success, `process.exit(1)` on fatal error
- `console.log` / `console.error` directly (no Pino — this is not the MCP server, stdout is not JSON-RPC)
- `npx tsx src/processor/generate-embeddings.ts` as the run command

### Pattern: MCP Tool File
Each tool file exports `{name}Tool` (object with `name`, `title`, `description`, `inputSchema`) and `{name}Handler` (async function). `semantic-search.ts` follows this exactly. Input schema defined in `src/mcp-server/types.ts` as a Zod v4 schema.

### Pattern: Model-Scoped DB Queries
All reads from `embeddings_cache` must include `WHERE modelo = $n`. Never query without the model filter now that multiple models exist. This is the key invariant introduced by this milestone.

---

## Anti-Patterns to Avoid

### Anti-Pattern: Caching Query Embeddings
**What:** Storing the semantic search query text as an embedding in `embeddings_cache`
**Why bad:** Queries are not ordinances; storing them pollutes the cache and wastes DB space. The cosine similarity loop iterates over all cached vectors — including junk query vectors would degrade search quality.
**Instead:** Generate query embedding on-demand, use it, discard it.

### Anti-Pattern: Mixing Dimensions in Memory
**What:** Loading all embeddings regardless of model into a single array before comparing
**Why bad:** `text-embedding-3-small` is 1536-dim, `text-embedding-3-large` is 3072-dim. `calculateCosineSimilarity` throws `"Vectors must have the same length"`. The existing `getAllEmbeddingsForSimilarity` has this bug latent — it becomes active once large-model rows exist.
**Instead:** Always filter by `modelo` in the DB query before loading into memory.

### Anti-Pattern: Re-using `getOrCreateEmbedding` in Batch Script
**What:** Calling the MCP server's on-demand function from the batch processor
**Why bad:** `getOrCreateEmbedding` is designed for single requests from a running MCP server (uses `src/mcp-server/db.ts` pool, Pino logger). The batch script should have its own DB connection (Drizzle or raw pg.Pool) and direct OpenAI calls, matching the processor pattern.
**Instead:** The batch script is standalone and self-contained. It may share the `generateEmbeddingForModel` pure function from `embeddings.ts` only if that function is extracted to have no side effects — otherwise, duplicate the OpenAI call logic in the batch script.

### Anti-Pattern: Replacing `similar_ordenanzas`
**What:** Changing `similar_ordenanzas` to use `text-embedding-3-large`
**Why bad:** `similar_ordenanzas` generates embeddings on-demand for arbitrary ordinances — this works with `small` because cost and latency are acceptable per-request. Switching to `large` (3x the cost, slightly higher latency) for on-demand generation is not warranted. The two tools serve different use cases.
**Instead:** Leave `similar_ordenanzas` using `text-embedding-3-small`. `semantic_search` uses pre-generated `text-embedding-3-large` embeddings.

---

## Scalability Considerations

| Concern | Current (~2000 ordinances) | At 10K ordinances |
|---------|---------------------------|-------------------|
| Memory for cosine similarity | ~2000 × 3072 × 8 bytes ≈ 47MB in-memory — acceptable | ~10K × 3072 × 8 bytes ≈ 234MB — review at this point |
| Batch generation time | ~2000 / 5 concurrent ≈ 400 API calls at ~200ms each ≈ 80 seconds | ~2000 seconds — add chunked resumability |
| DB query for all large embeddings | Single SELECT, ~2000 rows of TEXT — fast | Consider adding an index on `(modelo)` |

---

## File Locations Summary

```
src/
  processor/
    concurrent-deepseek.ts      (exists — reference for patterns)
    generate-embeddings.ts      (NEW — batch script)
  mcp-server/
    embeddings.ts               (MODIFY — fix modelo bugs, add model-aware exports)
    tools/
      similar.ts                (unchanged — no interface change needed)
      semantic-search.ts        (NEW — free-text semantic search tool)
      index.ts                  (MODIFY — add import + ALL_TOOLS entry)
  db/
    schema-cache.ts             (unchanged — embeddings_cache already supports multi-model)
```

---

## Sources

- Codebase analysis: `src/mcp-server/embeddings.ts`, `src/db/schema-cache.ts`, `src/mcp-server/tools/similar.ts`, `src/processor/concurrent-deepseek.ts` — HIGH confidence
- `embeddings_cache` schema confirms `(ordenanza_id, modelo)` unique constraint — HIGH confidence
- Dimension counts: OpenAI text-embedding-3-large = 3072, text-embedding-3-small = 1536 — HIGH confidence (well-documented API spec)
- Memory estimate for 2000 × 3072-dim embeddings: 47MB — calculated from first principles, HIGH confidence
