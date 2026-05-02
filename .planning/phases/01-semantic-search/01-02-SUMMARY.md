---
phase: 01-semantic-search
plan: 02
subsystem: api
tags: [openai, embeddings, text-embedding-3-large, cosine-similarity, semantic-search, mcp-tool]

requires:
  - phase: 01-semantic-search/01
    provides: generateEmbeddingForModel, getAllEmbeddingsByModel, cosineSimilarity, parseVector, toolLogger

provides:
  - semantic_search MCP tool for free-text semantic search over ordinances
  - SemanticSearchInputSchema for query, limit, umbral, solo_vigentes
  - Threshold filtering, solo_vigentes post-filter, scored results

affects: [01-semantic-search]

tech-stack:
  added: []
  patterns: [ephemeral query embedding, corpus-wide cosine similarity, post-filter vigente status]

key-files:
  created:
    - src/mcp-server/tools/semantic-search.ts
  modified:
    - src/mcp-server/types.ts
    - src/mcp-server/tools/index.ts

key-decisions:
  - "Query embedding is ephemeral (NOT cached) — avoids polluting embeddings_cache with one-off search queries"
  - "solo_vigentes is a post-filter on results, not a DB filter — simpler given in-memory approach"
  - "Model hard-coded to text-embedding-3-large in tool (not user-supplied) — prevents dimension mismatch attacks (T-01-07 mitigation)"
  - "Clear error when 0 large-model embeddings exist — prevents silent empty results"

requirements-completed: [SS-03, SS-04]

duration: 5 min
completed: 2026-05-02
---

# Phase 1 Plan 02: Semantic Search Tool Summary

**semantic_search MCP tool for free-text semantic search over ordinances using text-embedding-3-large embeddings with threshold filtering and solo_vigentes support**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-02T19:00:31Z
- **Completed:** 2026-05-02T19:05:47Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created semantic_search MCP tool that searches ordinances by natural language concept using pre-generated embeddings
- Registered tool in ALL_TOOLS (total: 13 tools), immediately callable by MCP clients
- Tool distinguishes itself from search_ordenanzas (keyword) and similar_ordenanzas (by-ID) in description
- Handles edge cases: missing embeddings, solo_vigentes filter, threshold-based scoring

## Task Commits

Each task was committed atomically:

1. **Task 1: Add input schema + create semantic-search.ts tool** - `f06799e` (feat)
2. **Task 2: Register semantic_search in tools/index.ts** - `2886e42` (feat)

## Files Created/Modified
- `src/mcp-server/tools/semantic-search.ts` - Semantic search tool: generates query embedding, loads corpus, computes similarity, filters by threshold and vigente status
- `src/mcp-server/types.ts` - Added SemanticSearchInputSchema (query, limit, umbral, solo_vigentes)
- `src/mcp-server/tools/index.ts` - Registered semanticSearchTool in ALL_TOOLS (12 → 13 tools)

## Decisions Made
- **Ephemeral query embedding:** Query embeddings not cached — avoids polluting embeddings_cache with one-off search queries, keeps cache clean for batch-generated corpus embeddings
- **Post-filter for vigente status:** solo_vigentes filters results after similarity computation — simpler given in-memory approach where all embeddings are loaded regardless
- **Hard-coded model:** text-embedding-3-large is not user-supplied — prevents dimension mismatch attacks per threat model T-01-07
- **Empty corpus error:** Returns clear error message when no large-model embeddings exist instead of silently returning empty results

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- semantic_search tool is registered and callable via MCP protocol
- Requires batch embedding generation to populate corpus: `npx tsx src/processor/generate-embeddings.ts`
- Phase 1 (Semantic Search) is now complete — both plans done

## Self-Check: PASSED

- [x] f06799e exists in git log
- [x] 2886e42 exists in git log
- [x] src/mcp-server/tools/semantic-search.ts exists
- [x] src/mcp-server/types.ts contains SemanticSearchInputSchema
- [x] src/mcp-server/tools/index.ts contains semanticSearchTool
- [x] ALL_TOOLS has 13 entries
- [x] npx tsc --noEmit passes for our files (pre-existing pg/MCP SDK errors out of scope)

---
*Phase: 01-semantic-search*
*Completed: 2026-05-02*
