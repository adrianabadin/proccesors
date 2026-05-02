# Project State

**Project:** Ordenanzas Saladillo MCP — Semantic Search
**Updated:** 2026-05-02

---

## Current Phase

**Phase:** 1 — Semantic Search Implementation
**Status:** Planning

## Decisions

- Tech stack: TypeScript + Node.js (ESM) + OpenAI SDK + pg
- Embedding model: text-embedding-3-large (3072 dimensions)
- Similarity: cosine similarity in memory (no pgvector)
- Batch script: standalone, resumable via DB-as-checkpoint pattern
- New tool coexists with existing 12 tools, no replacements

## Blockers

None.

## Todos

None.
