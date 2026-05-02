---
status: resolved
trigger: "semantic_search MCP tool times out (error -32001) when computing cosine similarity"
created: 2026-05-02
updated: 2026-05-02
---

## Root Cause

Transferring 2778 vectors × ~30KB (JSON TEXT) = **161.5 MB** from remote PostgreSQL at `thecodersteam.com` over the network took **83 seconds**, dwarfing all other operations (OpenAI API: 1.4s, compute: 2s). Total pipeline: 87s vs 30s MCP timeout.

Previous fix (single-pass cosine) only addressed the compute step (2s → 2s), which was not the bottleneck.

## Fix

Replaced PostgreSQL vector transfer with **LanceDB** — an embedded vector database that stores vectors locally on disk.

- Created `src/mcp-server/vector-store.ts` — LanceDB wrapper for local vector search
- Created `src/processor/sync-vectors.ts` — one-time sync script (PostgreSQL → LanceDB)
- Modified `semantic-search.ts` to use `searchSimilar()` from LanceDB instead of `getEmbeddingsForSimilarity()` from PostgreSQL

**Result:** Search time: **87s → 90ms** (970x improvement)

## Files Changed

- `src/mcp-server/vector-store.ts` (new)
- `src/processor/sync-vectors.ts` (new)
- `src/mcp-server/tools/semantic-search.ts` (modified)
- `.gitignore` (added `.lancedb/`)
- `package.json` (added `@lancedb/lancedb`)

## Verification

🚀 MCP server must be RESTARTED to pick up the fix.
