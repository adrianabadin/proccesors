---
phase: 01-semantic-search
plan: 01
subsystem: database
tags: [openai, embeddings, text-embedding-3-large, cosine-similarity, batch-processing, pg]

requires:
  - phase: existing
    provides: embeddings_cache table with modelo column, OpenAI client, MCP server infrastructure

provides:
  - Fixed embeddings.ts with model-aware queries (modelo filter on all SQL)
  - Zero-norm-safe cosine similarity in utils.ts
  - generateEmbeddingForModel and getAllEmbeddingsByModel exports
  - Batch embedding generation script (generate-embeddings.ts)

affects: [01-semantic-search]

tech-stack:
  added: [p-limit, js-tiktoken, text-embedding-3-large]
  patterns: [CONFIG+main() batch script, DB-as-checkpoint resumability, token-aware text selection]

key-files:
  created:
    - src/processor/generate-embeddings.ts
  modified:
    - src/mcp-server/embeddings.ts
    - src/mcp-server/utils.ts

key-decisions:
  - "Kept text-embedding-3-small as default EMBEDDING_MODEL in embeddings.ts for backward compatibility; new functions accept model parameter"
  - "Re-exported utils.ts functions from embeddings.ts for backward compat (parseEmbeddingVector, formatEmbeddingVector, calculateCosineSimilarity)"
  - "Used p-limit for concurrency control instead of custom worker pool (simpler for I/O-bound API calls)"

requirements-completed: [SS-01, SS-02, SS-05]

duration: 5 min
completed: 2026-05-02
---

# Phase 1 Plan 01: Embeddings Module Fix + Batch Script Summary

**Model-aware embedding queries with modelo filter, zero-norm cosine similarity guard, and batch text-embedding-3-large generation script**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-02T18:48:58Z
- **Completed:** 2026-05-02T18:55:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Fixed latent bugs in embeddings.ts: all SQL queries now filter by modelo column preventing cross-model contamination
- Added zero-norm guard to cosineSimilarity (returns 0 instead of NaN for empty vectors)
- Created batch embedding script following concurrent-deepseek.ts patterns with p-limit concurrency, js-tiktoken token counting, and DB-as-checkpoint resumability

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix embeddings model filter + consolidate utils + zero-norm guard** - `fdab757` (feat)
2. **Task 2: Create batch embedding generation script** - `6fc9b69` (feat)

## Files Created/Modified
- `src/mcp-server/embeddings.ts` - Added modelo filter to all SQL, removed duplicate functions, added generateEmbeddingForModel and getAllEmbeddingsByModel exports
- `src/mcp-server/utils.ts` - Added zero-norm guard to cosineSimilarity
- `src/processor/generate-embeddings.ts` - Batch embedding generation script with resumability
- `package.json` - Added p-limit and js-tiktoken dependencies

## Decisions Made
- **Backward compat re-exports:** Kept parseEmbeddingVector, formatEmbeddingVector, calculateCosineSimilarity as aliases to utils.ts exports — avoids breaking similar.ts and any other consumers
- **p-limit over custom workers:** Batch script uses p-limit for concurrency (I/O-bound API calls don't need worker pool complexity)
- **Token threshold 6000:** Conservative limit for text-embedding-3-large (8191 max context) with room for API overhead

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing TypeScript errors in unrelated files (pg types, drizzle-kit, MCP SDK) — out of scope, not introduced by this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- embeddings.ts is ready for semantic_search tool to consume via generateEmbeddingForModel and getAllEmbeddingsByModel
- Batch script is ready to run: `npx tsx src/processor/generate-embeddings.ts` (requires OPENAI_API_KEY in .env)
- Next plan should implement the semantic_search MCP tool

## Self-Check: PASSED

- [x] fdab757 exists in git log
- [x] 6fc9b69 exists in git log
- [x] src/mcp-server/embeddings.ts exists
- [x] src/mcp-server/utils.ts exists
- [x] src/processor/generate-embeddings.ts exists
- [x] 01-01-SUMMARY.md exists

---
*Phase: 01-semantic-search*
*Completed: 2026-05-02*
