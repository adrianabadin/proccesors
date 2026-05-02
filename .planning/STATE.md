# Project State

**Project:** Ordenanzas Saladillo MCP — Semantic Search
**Updated:** 2026-05-02

---

## Current Phase

**Phase:** 1 — Semantic Search Implementation
**Status:** In Progress — Plan 01 complete, Plan 02 next

## Decisions

- Tech stack: TypeScript + Node.js (ESM) + OpenAI SDK + pg
- Embedding model: text-embedding-3-large (3072 dimensions)
- Similarity: cosine similarity in memory (no pgvector)
- Batch script: standalone, resumable via DB-as-checkpoint pattern
- New tool coexists with existing 12 tools, no replacements
- Backward compat re-exports maintained in embeddings.ts for similar.ts consumers
- p-limit chosen for batch script concurrency (simpler than worker pool for I/O-bound)

## Blockers

None.

## Todos

- Run batch embedding script to populate embeddings_cache with text-embedding-3-large vectors
- Implement semantic_search MCP tool (Plan 02)
