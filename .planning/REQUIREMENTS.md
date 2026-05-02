# Requirements

**Project:** Ordenanzas Saladillo MCP — Semantic Search

---

## SS-01: Batch Embedding Generation Script ✅

**Priority:** Must
**Phase:** 1

Create a standalone batch script (`src/processor/generate-embeddings.ts`) that generates `text-embedding-3-large` embeddings for all ordinances not yet cached. Must support resumability (skip already-processed), token-based text selection (full text ≤ 6000 tokens, resumen otherwise), rate-limited concurrency, and progress output.

**Acceptance:** `npx tsx src/processor/generate-embeddings.ts` runs to completion, inserts rows into `embeddings_cache` with `modelo = 'text-embedding-3-large'`, and is safe to re-run.

---

## SS-02: Fix Embeddings Module Model Filter ✅

**Priority:** Must
**Phase:** 1

Fix `src/mcp-server/embeddings.ts` so all `embeddings_cache` queries include `WHERE modelo = $N`. Add model-parameterized exports (`generateEmbeddingForModel`, `getAllEmbeddingsByModel`) alongside existing functions. Fix zero-norm vector guard in cosine similarity. Consolidate duplicate `parseVector`/`cosineSimilarity` functions.

**Acceptance:** `getOrCreateEmbedding` and `getAllEmbeddingsForSimilarity` include `modelo` filter. New exports exist. Zero-norm vector returns 0 instead of NaN.

---

## SS-03: Semantic Search MCP Tool ✅

**Priority:** Must
**Phase:** 1

Create `src/mcp-server/tools/semantic-search.ts` implementing a new `semantic_search` MCP tool. Accepts `query` (string), `limit` (1-50, default 10), `umbral` (0-1, default 0.7), `solo_vigentes` (bool, default false). Generates query embedding with `text-embedding-3-large`, loads pre-generated embeddings from cache, computes cosine similarity, filters by threshold, returns scored results.

**Acceptance:** MCP tool registered and callable. Returns ordinances with similarity scores ≥ umbral. Error message when no `text-embedding-3-large` embeddings exist in cache.

---

## SS-04: Tool Registration and Integration ✅

**Priority:** Must
**Phase:** 1

Add `SemanticSearchInputSchema` to `src/mcp-server/types.ts`. Register the new tool in `src/mcp-server/tools/index.ts` `ALL_TOOLS` array following existing patterns.

**Acceptance:** `semantic_search` appears in `ALL_TOOLS`. Input schema validated with Zod v4. Tool description distinguishes from `search_ordenanzas` and `similar_ordenanzas`.

---

## SS-05: Data Quality Validation in Batch Script ✅

**Priority:** Should
**Phase:** 1

The batch script must validate ordinance text before embedding: skip ordinances with empty or very short `texto_completo` (< 100 chars), fall back to `resumen`, skip entirely if both are empty/short. Log skipped count in summary.

**Acceptance:** Batch script logs count of skipped ordinances. No empty or near-empty text sent to OpenAI API.

---
