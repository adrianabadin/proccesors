# Technology Stack

**Analysis Date:** 2026-05-02

## Languages

**Primary:**
- TypeScript 5.9+ - All source files in `src/`, `app.ts`, root scripts
- SQL - Schema definitions in `database/schema.sql`, raw queries throughout MCP tools

**Secondary:**
- JavaScript - Legacy browser scraper variant `cosa.js` (DevTools runner)
- Python - Utility scripts `convert_to_word.py`, `extract_ids.py` at project root

## Runtime

**Environment:**
- Node.js (ES2022 target, ESNext modules)
- `"type": "module"` in `package.json` — all files use ESM `import`/`export`

**Package Manager:**
- npm
- Lockfile: `package-lock.json` present

## Frameworks

**Core:**
- `@modelcontextprotocol/sdk` 1.26.0 - MCP server protocol via `McpServer` + `StdioServerTransport`
- `drizzle-orm` 0.45.1 - ORM for processor pipeline (`src/processor/`, `src/db/`)
- `zod` 4.3.6 - Input validation for all MCP tool schemas (`src/mcp-server/types.ts`)

**Scraping:**
- `playwright` / `playwright-chromium` 1.48.0 - Primary scraper (`src/scraper/scraper-playwright.ts`)
- `jsdom` 26.1.0 - HTML parsing in legacy scraper (`app.ts`)

**AI / LLM:**
- `openai` 6.22.0 - Used as OpenAI-compatible client for both DeepSeek API and Groq API
  - DeepSeek API (`src/processor/concurrent-deepseek.ts`): extraction/classification
  - OpenAI embeddings (`src/mcp-server/embeddings.ts`): `text-embedding-3-small`
  - Groq (`src/mcp-server/llm.ts`): `llama-3.3-70b-versatile` for summarization

**Database:**
- `pg` 8.18.0 - Direct PostgreSQL pool for MCP server (`src/mcp-server/db.ts`)
- `drizzle-orm/node-postgres` - ORM layer for processor (`src/db/index.ts`)

**Logging:**
- `pino` 10.3.1 - Structured JSON logging to stderr (`src/mcp-server/logger.ts`)
- `pino-pretty` 13.1.3 - Dev-mode colored output (destination fd 2 to avoid corrupting MCP stdio)

**Testing:**
- `vitest` - Test runner (used in `src/mcp-server/tests/tools.test.ts`)
- Note: vitest is not in `package.json` dependencies — tests reference it but it is not installed

**HTTP:**
- `axios` 1.13.5 - Listed as dependency, not observed in active code paths
- Native `fetch` - Used in legacy `app.ts` scraper

## Key Dependencies

**Critical:**
- `@modelcontextprotocol/sdk` 1.26.0 - Core MCP server; uses `McpServer` (not deprecated `Server`). Any upgrade needs API compatibility check.
- `drizzle-orm` 0.45.1 - Used for processor pipeline persistence. Schema in `src/db/schema.ts`.
- `pg` 8.18.0 - Two separate pool instances exist: one in `src/mcp-server/db.ts`, one in `src/db/index.ts`

**Infrastructure:**
- `dotenv` 17.3.1 - Loaded via `import "dotenv/config"` at module level across all entry points
- `zod` 4.3.6 - Imported as `zod/v4` (new Zod v4 API) for all input schemas

## Configuration

**Environment:**
- Configured via `.env` file (loaded automatically with `dotenv/config`)
- Key vars: `DATABASE_URL`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `VERBOSE`, `LOG_LEVEL`, `NODE_ENV`
- See `.env.example` for all required values

**Build:**
- `tsconfig.json`: `target: es2022`, `module: esnext`, `moduleResolution: bundler`, `strict: true`
- `noEmit: true` — TypeScript is not compiled to `dist/`; everything runs via `tsx`
- `rootDir: "."` — includes root-level scripts alongside `src/`

**MCP Server Registration:**
- `.mcp.json` at project root configures Claude Code to launch the MCP server
- Command: `npx tsx src/mcp-server/index.ts`

## Platform Requirements

**Development:**
- Node.js with `tsx` for direct TypeScript execution: `npx tsx <file>`
- PostgreSQL database accessible at `DATABASE_URL`
- Optional: `OPENAI_API_KEY` (embeddings), `GROQ_API_KEY` (summaries), `DEEPSEEK_API_KEY` (processor)

**Production:**
- Deployed on VPS 2 cores / 4GB RAM (processor comments reference this)
- PostgreSQL at `thecodersteam.com:5432/ordenanzas`
- MCP server runs as stdio subprocess launched by Claude Code via `.mcp.json`

---

*Stack analysis: 2026-05-02*
