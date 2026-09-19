# Domain Pitfalls

**Domain:** Batch OpenAI embedding generation + in-memory cosine similarity search (Node.js/TypeScript)
**Project:** Ordenanzas Saladillo — semantic_search MCP tool
**Researched:** 2026-05-02
**Overall confidence:** HIGH (verified against official docs and existing codebase)

---

## Critical Pitfalls

Mistakes that cause silent data corruption, script crashes, or wrong search results.

---

### Pitfall 1: Character-based truncation instead of token-based truncation

**What goes wrong:** The existing codebase uses character length as a proxy for token length (`~8000 chars = ~2000 tokens` per PROJECT.md). OpenAI's limit for `text-embedding-3-large` is **8191 tokens**, not characters. Spanish municipal ordinance text averages ~3-4 chars per token (higher than English), so an 8000-char ordinance can be 2000-2500 tokens — well under the limit. But some ordinances contain tables, lists of legal references, or repeated boilerplate that pack more tokens per character. A 32000-char text sent as-is will throw HTTP 400 `context_length_exceeded` and abort the batch script with no partial save.

**Why it happens:** Character count is fast and requires no tokenizer dependency. The assumption holds for average text but fails for outliers.

**Consequences:** Batch script crashes mid-run. Ordinances processed before the crash are saved; the rest are not. Without a progress checkpoint file, the entire run must restart from zero — re-calling the API for already-processed ordinances and burning API quota.

**Prevention:**
- Use `tiktoken` (`js-tiktoken` npm package) to count tokens before each API call.
- Hard limit: if `tokenCount > 8000`, use `resumen` instead of `texto_completo`. Do not truncate mid-token — always use the full `resumen` field which is already available in the DB.
- Log which ordinances fell back to `resumen` for quality auditing.

**Detection:**
- A 400 error from OpenAI with message `This model's maximum context length is 8191 tokens`.
- If the script exits before completion without a checkpoint file, assume this hit.

**Phase:** Batch script implementation (Phase 1 / first milestone task).

---

### Pitfall 2: No progress checkpoint — script is not resumable

**What goes wrong:** The batch script processes ~2000 ordinances sequentially. If it is interrupted (network drop, Ctrl+C, VPS restart, rate-limit cascade), all progress is lost and the script must restart from ordinanza #1. This wastes API credits and time. With ~2000 documents at ~500-2000 tokens each, a full run costs real money and takes 10-30 minutes. Re-running from scratch doubles cost.

**Why it happens:** Naive implementations just loop over DB rows with no state tracking.

**Consequences:** Wasted API spend. Frustration. Risk of hitting daily quota caps if the script restarts multiple times.

**Prevention:**
- At startup, query `embeddings_cache` WHERE `modelo = 'text-embedding-3-large'` to build a `Set<string>` of already-processed `ordenanza_id` values.
- Skip any ordinanza already in that set.
- Since the DB insert happens immediately after each successful API call, the DB itself IS the checkpoint. This is the correct pattern for this project — no separate checkpoint file needed.
- Important: use `ON CONFLICT (ordenanza_id, modelo) DO UPDATE` (already present in the existing `getOrCreateEmbedding` INSERT) to make inserts idempotent.

**Detection:**
- Script produces fewer rows in `embeddings_cache` than expected after a partial run.
- Running `SELECT COUNT(*) FROM embeddings_cache WHERE modelo = 'text-embedding-3-large'` mid-run should show increasing count.

**Phase:** Batch script implementation.

---

### Pitfall 3: `getOrCreateEmbedding` query does NOT filter by `modelo` column

**What goes wrong:** The existing `getOrCreateEmbedding` in `src/mcp-server/embeddings.ts` runs:

```sql
SELECT vector FROM embeddings_cache WHERE ordenanza_id = $1
```

This query has no `AND modelo = $2` clause. When the batch script calls this function (or a variant of it) for `text-embedding-3-large`, it will find the existing `text-embedding-3-small` vector and return it — silently returning 1536-dimensional data where 3072-dimensional data is expected. The cosine similarity comparison between a 3072-dim query vector and a 1536-dim cached vector will either throw `Vectors must have the same length` or produce garbage if dimension checking is skipped.

**Why it happens:** The cache was designed before multi-model support was a concern. The `modelo` column exists in the schema but is not used in lookup queries.

**Consequences:** Silent wrong results in `semantic_search`. The tool returns results but they are meaningless because the vectors are from incompatible embedding spaces.

**Detection:**
- `calculateCosineSimilarity` throws `Vectors must have the same length` if the dimension guard is in place.
- If the guard is NOT in place, scores will look plausible (0.3-0.7) but results will be semantically wrong — hard to detect without ground-truth test cases.

**Prevention:**
- Add `AND modelo = $2` to ALL `embeddings_cache` lookups.
- The batch script must pass `modelo = 'text-embedding-3-large'` explicitly.
- The `semantic_search` tool must load only `WHERE modelo = 'text-embedding-3-large'` vectors.
- Do NOT reuse `getOrCreateEmbedding` from `embeddings.ts` as-is — write a model-aware version.

**Phase:** Both batch script AND `semantic_search` tool implementation.

---

### Pitfall 4: Cosine similarity called on zero-norm vector (division by zero)

**What goes wrong:** The `calculateCosineSimilarity` function divides by `Math.sqrt(normA) * Math.sqrt(normB)`. If either vector has all-zero values (e.g., a corrupt DB row, a failed parse), this results in `0 / 0 = NaN`. `NaN` comparisons always return false, so a corrupt vector causes it to sort to an unpredictable position in results — it neither appears at the top nor is filtered out.

**Why it happens:** The existing implementation (both in `utils.ts` and `embeddings.ts`) has no zero-norm guard. The `parseVector` function will successfully parse `[0,0,0,...]` as a valid vector.

**Consequences:** Corrupt rows silently pollute `semantic_search` results with `NaN` scores.

**Prevention:**
```typescript
const denom = Math.sqrt(normA) * Math.sqrt(normB);
if (denom === 0) return 0; // treat zero-norm vector as no similarity
```
Add this guard to `cosineSimilarity` in `utils.ts`.

**Detection:**
- Any `semantic_search` result where `score` is `NaN` or `null`.
- Run: `SELECT id, ordenanza_id FROM embeddings_cache WHERE vector = '[0.0,...]'` to find zero vectors (unlikely but possible after partial API failures).

**Phase:** `semantic_search` tool implementation.

---

## Moderate Pitfalls

---

### Pitfall 5: Rate limit cascade — concurrent requests hit 429 at burst start

**What goes wrong:** The existing `concurrent-deepseek.ts` uses a worker pool with 6 concurrent API workers. If the embedding batch script applies the same pattern without rate-limit awareness, the first 10-20 requests may succeed but OpenAI's TPM counter fills up quickly when sending full-text ordinances (each can be 500-3000 tokens). A burst of 10 simultaneous large-text requests can consume 30,000 tokens instantly against a Tier 1 limit of 1,000,000 TPM — but RPM (requests per minute) limits at Tier 1 are typically 3,000 RPM for embedding models, which is more than enough. The real risk is if the account is on a free or very new tier where limits are much lower.

**Why it happens:** The OpenAI Node.js SDK has `maxRetries: 2` by default (already set in the existing client). But with 6+ concurrent workers, all retries collide and create a retry storm.

**Prevention:**
- For a 2000-document dataset, sequential processing with a small inter-request delay (200-500ms) is simpler and sufficient. At 500ms/request, 2000 docs takes ~17 minutes — acceptable for a one-time batch.
- If concurrency is used, cap at 3 concurrent requests and add 100ms delay between dispatches.
- Always check `error.status === 429` vs `error.status === 400` — they require different responses (retry vs fix input).
- The SDK's built-in exponential backoff handles most 429s automatically with `maxRetries: 3`.

**Detection:**
- Multiple `429 Too Many Requests` errors in sequence despite exponential backoff.
- Script stalls for 60+ seconds without progress.

**Phase:** Batch script implementation.

---

### Pitfall 6: Memory spike when loading 2000 x 3072 float vectors for similarity

**What goes wrong:** Each `text-embedding-3-large` vector has 3072 float64 values. Stored as a JSON string in the DB (as the current code does with `JSON.stringify`), each vector is ~24KB on disk. Loaded and parsed as a JavaScript `number[]` array, each vector occupies ~24KB in V8 heap (8 bytes per float64 x 3072 = 24,576 bytes). For 2000 vectors: `2000 x 24KB = ~48MB` just for the vector data, plus V8 object overhead (array metadata, GC pointers) which multiplies this by 3-5x in practice. Total heap impact: **150-240MB** for the vector corpus alone.

The VPS runs 4GB RAM. The MCP server pool uses 20 connections. This is probably fine but leaves less margin. The risk is if `semantic_search` is called concurrently multiple times — each call re-loads all vectors from DB.

**Why it happens:** `getAllEmbeddingsForSimilarity` fetches all rows on every call with no caching.

**Prevention:**
- Cache the loaded vector corpus in a module-level variable (not re-queried on every tool call). Invalidate cache on a TTL (e.g., 5 minutes) or on batch script completion signal.
- For the 2000-doc dataset, `Float32Array` instead of `number[]` would halve memory (4 bytes vs 8 bytes per component), saving ~24MB — worth doing if heap is tight.
- Log `process.memoryUsage().heapUsed` before and after loading to confirm actual impact.

**Detection:**
- Node.js heap OOM crash during `semantic_search` under load.
- `process.memoryUsage().heapUsed` exceeds 500MB while MCP server is running.

**Phase:** `semantic_search` tool implementation.

---

### Pitfall 7: `texto_completo` quality varies — empty or HTML-encoded text produces garbage embeddings

**What goes wrong:** The scraper stored ordinance text from hcd.saladillo.gob.ar. Some older ordinances (pre-2000) may have empty `texto_completo`, contain only a title, or have HTML entities (`&nbsp;`, `&amp;`) that were not stripped during scraping. Embedding these produces a vector that represents noise or boilerplate, not the ordinance content.

**Why it happens:** Scraper inconsistencies and data quality issues accumulate over 30+ years of ordinances.

**Prevention:**
- Before embedding, validate: `texto_completo.trim().length > 100`. If too short, fall back to `resumen`. If `resumen` is also empty, skip and log a warning — do not embed an empty string (the API will return a vector but it is meaningless).
- Decode HTML entities before embedding using a library like `he` or `decode-html`. The existing code does not appear to do this.
- Track which ordinanzas were skipped and why — include a `noEmbedding` count in batch output.

**Detection:**
- Ordinances with `texto_completo = ''` or `texto_completo IS NULL` in the DB.
- Query: `SELECT COUNT(*) FROM ordenanzas WHERE texto_completo IS NULL OR LENGTH(texto_completo) < 100`.

**Phase:** Batch script implementation (preprocessing step before embedding).

---

## Minor Pitfalls

---

### Pitfall 8: Duplicate `cosineSimilarity` / `parseVector` / `formatVector` functions

**What goes wrong:** `embeddings.ts` and `utils.ts` both define `parseVector`, `formatVector`, `cosineSimilarity`, and `calculateCosineSimilarity` (two versions of the same function with different names in `embeddings.ts`). The batch script and `semantic_search` tool will need to import these functions. If they import from the wrong module or mix imports, divergent implementations cause subtle bugs (e.g., if one version gets a bug fix applied to only one copy).

**Prevention:**
- Before implementing new code, consolidate: keep the implementations in `utils.ts` as the single source of truth, and have `embeddings.ts` re-export from `utils.ts` rather than redefining. Remove the duplicate `calculateCosineSimilarity` from `embeddings.ts` (it is identical to `cosineSimilarity` in `utils.ts`).

**Phase:** Cleanup before implementing `semantic_search`.

---

### Pitfall 9: OpenAI SDK `maxRetries: 2` is too low for a long batch run

**What goes wrong:** The existing `openai` client in `embeddings.ts` is configured with `maxRetries: 2` and `timeout: 30_000`. For interactive MCP tool calls, 2 retries is appropriate to fail fast. For a batch script that runs overnight or unattended, 2 retries on a transient 429 may abort a 30-minute run unnecessarily.

**Prevention:**
- Instantiate a **separate** OpenAI client for the batch script with `maxRetries: 5` and `timeout: 60_000`. Do not reuse the MCP server's client.
- This also prevents the batch script client configuration from affecting MCP server behavior.

**Phase:** Batch script implementation.

---

### Pitfall 10: `semantic_search` result scores are not normalized or bounded

**What goes wrong:** Cosine similarity returns values in `[-1, 1]`. For embeddings from OpenAI models, results in practice range from ~0.5 (semantically unrelated) to ~0.99 (near-identical). Returning raw scores to MCP consumers without context is confusing — a score of 0.72 means nothing to a caller without domain knowledge.

**Prevention:**
- Apply a minimum similarity threshold (e.g., 0.6) and discard results below it before returning.
- Return the score as a `0-100` percentage or a `low/medium/high` label alongside the raw value.
- Document the threshold in the tool description so Claude knows what score level is "meaningful".

**Phase:** `semantic_search` tool implementation.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Batch script — text selection | Character-based truncation (Pitfall 1) | Use `js-tiktoken` for token counting; fall back to `resumen` |
| Batch script — resumability | No checkpoint = re-run from zero (Pitfall 2) | Query existing `embeddings_cache` rows at startup to skip already-processed |
| Batch script — API calls | 429 cascade with concurrency (Pitfall 5) | Sequential with 200-500ms delay OR max 3 concurrent; `maxRetries: 5` |
| Batch script — data quality | Empty/HTML text = garbage embeddings (Pitfall 7) | Validate `texto_completo` length; decode HTML entities before embedding |
| `semantic_search` tool — vector loading | Missing `modelo` filter returns wrong dimensions (Pitfall 3) | Always add `AND modelo = 'text-embedding-3-large'` to all cache queries |
| `semantic_search` tool — similarity math | Zero-norm vector → NaN score (Pitfall 4) | Add `if (denom === 0) return 0` guard to `cosineSimilarity` |
| `semantic_search` tool — memory | Vector corpus re-loaded on every call (Pitfall 6) | Module-level cache with TTL; log `process.memoryUsage()` to confirm 150-240MB estimate |
| Code organization | Duplicate utility functions cause divergent fixes (Pitfall 8) | Consolidate `parseVector`/`cosineSimilarity` into `utils.ts` before starting |

---

## Sources

- OpenAI rate limits guide: https://developers.openai.com/api/docs/guides/rate-limits (MEDIUM confidence — page inaccessible, content inferred from search results)
- OpenAI Cookbook — embedding long inputs: https://cookbook.openai.com/examples/embedding_long_inputs (MEDIUM confidence — referenced in multiple community sources)
- OpenAI Cookbook — handling rate limits: https://developers.openai.com/cookbook/examples/how_to_handle_rate_limits (MEDIUM confidence)
- OpenAI community — Tier 1 limits for text-embedding-3-small (1,000,000 TPM, 3,000 RPM): https://community.openai.com/t/rate-limits-for-new-embedding-v3-models/618110 (LOW confidence — community post, not official docs)
- MDN Float32Array memory characteristics: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Float32Array (HIGH confidence)
- Existing codebase analysis: `src/mcp-server/embeddings.ts`, `src/mcp-server/utils.ts`, `.planning/PROJECT.md` (HIGH confidence — direct code inspection)
