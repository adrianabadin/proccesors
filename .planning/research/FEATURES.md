# Feature Landscape

**Domain:** Semantic search MCP tool for a municipal ordinances corpus
**Researched:** 2026-05-02

---

## Context: What Already Exists

The existing server has 12 tools. Two are directly relevant to this milestone:

- `search_ordenanzas`: PostgreSQL full-text search via `websearch_to_tsquery`. Returns rank, ts_headline snippet, categories. Input: `query`, `limit`, `solo_vigentes`.
- `similar_ordenanzas`: Finds ordinances similar to a given ordinance by UUID. Generates embedding on-demand using `text-embedding-3-small`, loads all cached embeddings into memory, runs cosine similarity. Input: `ordenanza_id`, `limit`, `umbral`.

`semantic_search` is the missing third shape: free-text query → semantically similar ordinances, using pre-generated `text-embedding-3-large` embeddings from the batch script.

---

## Table Stakes

Features `semantic_search` must have or it is useless for an AI assistant.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `query` parameter (string, required) | The natural language input. Without it there is no semantic search. | Low | Must accept Spanish text. No length restriction needed for queries — typical NL queries are short. |
| `limit` parameter (integer, optional, default 10) | AI assistants need predictable result counts. Default of 10 matches `similar_ordenanzas` convention. | Low | Existing pattern: `min(1).max(50)`. Keep same bounds. |
| Similarity score in each result | Without a score, the AI can't assess confidence or explain relevance. | Low | Field name: `score`, range 0–1. Same as `similar_ordenanzas.OrdenanzaSimilarSchema`. |
| Ordinance metadata in each result | `id`, `numero`, `anio`, `titulo`, `resumen`, `estado`, `categorias`. AI needs this to answer questions without a second tool call. | Low | Reuse `OrdenanzaSimilarSchema` — it already has all these fields. |
| `umbral` parameter (float 0–1, optional, default 0.7) | Without a threshold, low-quality matches pollute results. Existing tools use 0.7 as default. | Low | Same default as `similar_ordenanzas`. Keep consistent. |
| Model-specific cache query | The batch generates `text-embedding-3-large` embeddings with `modelo` column. The tool must query by `modelo = 'text-embedding-3-large'` or results will be empty / mixed-dimension. | Medium | `getOrCreateEmbedding()` in `embeddings.ts` does NOT filter by model — this must be extended or the query written explicitly in the tool. |
| Query embedding generated at call time | The query text has no pre-existing embedding. Must call OpenAI `text-embedding-3-large` to embed it before comparing. | Medium | Must use the same model as the cached corpus embeddings. Dimension mismatch (3072 vs 1536) causes cosine similarity to throw. |
| Graceful error when no embeddings exist | If the batch has not run yet, `embeddings_cache` will have no `text-embedding-3-large` rows. Return a clear error, not a crash. | Low | Message: "No hay embeddings pre-generados. Ejecuta el script de generación batch primero." |
| `isError: true` on failure | Consistent with all 12 existing tools. AI assistants inspect this flag to decide retry vs surface-to-user. | Low | Copy pattern from `searchOrdenanzasHandler`. |

---

## Differentiators

Nice-to-have features that improve AI assistant UX without being blockers.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `solo_vigentes` filter (boolean, optional, default false) | An AI answering a legal question should prefer to surface currently valid ordinances. Matching `search_ordenanzas` parameter name reduces cognitive load. | Low | Adds a WHERE clause on `o.estado IN ('vigente', 'modificada')` after loading embeddings but before scoring, or post-filter on results. Post-filter is simpler given in-memory approach. |
| Result count in response envelope | `total: N` tells the AI how many results passed the threshold before the `limit` cap. Lets it say "found 3 relevant ordinances" vs "found 20, showing top 10". | Low | `total` is already in all other tool responses. Include both `total_above_threshold` and `returned`. |
| `modelo` in response envelope | Tells consuming AI (or developer debugging) which embedding model powered the search. Useful when both small and large embeddings coexist. | Low | Single string field in top-level response: `"modelo": "text-embedding-3-large"`. |
| Description that distinguishes from `search_ordenanzas` | The tool's MCP description is what AI assistants read to choose which tool to call. A description that explains "use this when you know a concept but not the keywords" prevents the AI from defaulting to full-text search. | Low | This is a description-writing task, not a code task. High leverage. |
| Description that distinguishes from `similar_ordenanzas` | "Use `semantic_search` when you have a concept or question; use `similar_ordenanzas` when you already have an ordinance ID and want related ones." | Low | Same — description text, not code. |

---

## Anti-Features

Things to deliberately NOT build in v1.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| On-demand embedding generation for missing ordinances | `similar_ordenanzas` does this and it causes latency on first call. `semantic_search` is designed around pre-generated embeddings — if an ordinance has no embedding, skip it, don't generate on the fly. | Silently exclude ordinances without `text-embedding-3-large` embeddings. The batch script is the path to completeness. |
| Hybrid search (semantic + full-text combined) | Combining cosine similarity scores with ts_rank requires calibration and introduces complexity. The AI already has both `search_ordenanzas` and `semantic_search` available and can call both if needed. | Let the AI orchestrate both tools separately when it wants hybrid coverage. |
| Pagination (offset/cursor) | Loading all embeddings into memory to compute cosine similarity already materializes the full result set. Offset-based pagination just slices that array and adds API surface complexity for no real benefit. | Use `limit` and instruct the AI to use filters if the desired result is not in the top N. |
| Caching the query embedding | Query embeddings are one-off, short texts. The cache overhead (DB write, conflict check) exceeds the benefit. The batch script handles corpus-side caching. | Generate query embedding inline, discard after use. |
| Exposing raw vector in response | Vectors are 3072 floats. Including them in MCP tool output would exceed context window budgets. | Never include the vector in the response payload. |
| Configurable embedding model as a tool parameter | Allowing callers to pass `modelo = 'text-embedding-3-small'` creates dimension mismatch risk and exposes infrastructure details. Model selection is a deployment concern. | Hard-code `text-embedding-3-large` in the tool. Document in the description which model it uses. |
| Rewriting `getAllEmbeddingsForSimilarity()` | That function doesn't filter by `modelo`. Rather than modifying it (which could break `similar_ordenanzas`), write a new targeted query in the semantic search handler. | New private query: `SELECT ... FROM embeddings_cache WHERE modelo = 'text-embedding-3-large'`. |

---

## Feature Dependencies

```
Batch script generates text-embedding-3-large embeddings
  → semantic_search tool can load them from embeddings_cache WHERE modelo = 'text-embedding-3-large'
    → Query embedding generated at call time (same model, same dimensions)
      → Cosine similarity computed in memory
        → Results filtered by umbral
          → Optional solo_vigentes post-filter
            → Results sorted desc by score, sliced to limit
              → Response returned with score, metadata, total_above_threshold, modelo
```

The `solo_vigentes` filter has no dependency on anything above it — it is a simple array post-filter.

The `modelo` field in the response envelope has no dependency — it is a hardcoded string.

---

## Input Schema (Recommended)

Based on analysis of existing input schemas in `types.ts`, the new schema should be:

```typescript
export const SemanticSearchInputSchema = z.object({
  query: z.string().min(1).describe(
    "Consulta en lenguaje natural. Ejemplo: 'ordenanzas sobre habilitación de comercios nocturnos'"
  ),
  limit: z.number().min(1).max(50).optional().default(10),
  umbral: z.number().min(0).max(1).optional().default(0.7),
  solo_vigentes: z.boolean().optional().default(false),
});
```

This is consistent with all existing schemas: same `limit` bounds as `similar_ordenanzas`, same `umbral` defaults, same `solo_vigentes` name as `search_ordenanzas`.

---

## Output Shape (Recommended)

```typescript
{
  resultados: OrdenanzaSimilar[],    // reuse existing schema (id, numero, anio, titulo, resumen, score, categorias)
  total_above_threshold: number,     // results before limit cap
  returned: number,                  // actual count returned (≤ limit)
  query: string,                     // echo the input query (existing tools echo their inputs)
  modelo: string,                    // "text-embedding-3-large"
  umbral: number,                    // echo the threshold used
}
```

---

## MVP Recommendation

Prioritize (in order):

1. `query`, `limit`, `umbral` parameters — core functionality
2. `OrdenanzaSimilar` result shape with `score` — required for usefulness
3. Clear error when no large-model embeddings exist — prevents silent broken experience
4. Model-filtered cache query — correctness, not an optimization
5. `solo_vigentes` — immediate practical value for legal queries
6. Tool description text distinguishing from `search_ordenanzas` and `similar_ordenanzas` — AI routing correctness

Defer:

- `total_above_threshold` vs `total`: either works for v1; start with `total` (simpler, matches existing tools)
- `modelo` in response envelope: add after core works, it's informational only

---

## Sources

- Codebase analysis: `src/mcp-server/tools/similar.ts`, `src/mcp-server/embeddings.ts`, `src/mcp-server/types.ts`, `src/mcp-server/tools/search.ts`
- Project requirements: `.planning/PROJECT.md`
- Confidence: HIGH — derived from direct code analysis, no external sources needed for feature design decisions
