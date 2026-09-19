# Codebase Structure

**Analysis Date:** 2026-05-02

## Directory Layout

```
ordenanzas/                    # Project root
├── app.ts                     # Legacy scraper entry point
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript config
├── .env.example               # Environment variable template
├── .mcp.json                  # MCP server config for Claude Code (gitignored)
├── .planning/                 # GSD planning documents
│   └── codebase/              # Codebase map documents
├── database/                  # SQL schema and design docs
│   ├── schema.sql             # Raw SQL schema definition
│   └── DESIGN.md              # Database design document
├── docs/                      # Design plans and implementation notes
│   └── plans/                 # Historical planning documents
├── src/                       # All active TypeScript source
│   ├── db/                    # Database layer (Drizzle ORM + pg)
│   ├── mcp-server/            # MCP server and tools
│   │   ├── tools/             # Individual tool implementations
│   │   └── tests/             # Tool test suite
│   ├── processor/             # AI extraction pipeline
│   └── scraper/               # Playwright scraper
├── scripts/                   # Utility and setup scripts
├── 1986/ ... 2025/            # Scraped ordinance .txt files (per year)
├── undefined/                 # Bug artifact — ordinances with unparseable year
├── data/                      # Additional data files
│   └── pba/                   # PBA legislation data
├── graphify-out/              # Knowledge graph outputs
└── prompts/                   # Prompt template files
```

## Directory Purposes

**`src/db/`:**
- Purpose: Database schema and Drizzle ORM client used by the processor pipeline
- Contains: `schema.ts` (full Drizzle table definitions), `index.ts` (db + pool exports), `schema-cache.ts` (embeddings_cache + resumenes_cache tables), `setup.ts` (DB initialization), `setup-cache.ts` (cache table setup)
- Key files: `src/db/schema.ts`, `src/db/index.ts`

**`src/mcp-server/`:**
- Purpose: MCP server implementation — the primary user-facing component
- Contains: Server entry point, tool registry, DB abstraction, logger, type schemas, AI clients, utilities
- Key files: `src/mcp-server/index.ts`, `src/mcp-server/db.ts`, `src/mcp-server/types.ts`, `src/mcp-server/logger.ts`

**`src/mcp-server/tools/`:**
- Purpose: One file per group of related MCP tools
- Contains: `search.ts` (3 tools), `by-id.ts` (2 tools), `by-entity.ts` (1 tool), `references.ts`, `categories.ts`, `stats.ts`, `similar.ts`, `summarize.ts`, `health.ts`, `index.ts` (ALL_TOOLS registry)
- Key files: `src/mcp-server/tools/index.ts` (central registry)

**`src/mcp-server/tests/`:**
- Purpose: Test suite for MCP tools
- Contains: `tools.test.ts` — vitest-based unit tests
- Status: Tests reference `vitest` which is not in `package.json`; cannot run without installing

**`src/processor/`:**
- Purpose: Batch AI extraction pipeline
- Contains: Multiple processor variants (deepseek, groq, gemini, glm), concurrent processor, prompts, parser, test scripts
- Key files: `src/processor/concurrent-deepseek.ts`, `src/processor/prompts.ts`, `src/processor/parser.ts`

**`src/scraper/`:**
- Purpose: Playwright-based ordinance scraper (current generation)
- Contains: `scraper-playwright.ts` (entry), `config.ts`, `link-extractor.ts`, `ordinance-downloader.ts`, `utils.ts`, `logger.ts`, `types.ts`
- Key files: `src/scraper/scraper-playwright.ts`, `src/scraper/config.ts`

**`{year}/` (1986–2025):**
- Purpose: Scraped ordinance text files, one per ordinance
- Format: `Ordenanza N° {number}.txt` inside `./{year}/`
- Generated: Yes, by scraper
- Committed: Yes (data corpus)

**`undefined/`:**
- Purpose: Bug artifact — ordinances whose title could not be parsed for a year
- Generated: Yes, by legacy `app.ts` when `title.split("/")[1]` is undefined
- Do not put new code here

**`database/`:**
- Purpose: SQL-level schema definition and design documentation
- Key files: `database/schema.sql`, `database/DESIGN.md`

## Key File Locations

**Entry Points:**
- `app.ts` — Legacy fetch-based scraper
- `src/scraper/scraper-playwright.ts` — Current Playwright scraper
- `src/processor/concurrent-deepseek.ts` — Primary AI processor (concurrent)
- `src/mcp-server/index.ts` — MCP server (launched by Claude Code)

**Configuration:**
- `tsconfig.json` — TypeScript compiler config
- `package.json` — Scripts and dependencies
- `.env` / `.env.example` — Environment variables
- `.mcp.json` — MCP server launch config (gitignored)
- `src/scraper/config.ts` — Scraper settings (BASE_URL, pages, delays)

**Core Logic:**
- `src/mcp-server/types.ts` — All Zod schemas and TypeScript types for MCP tools
- `src/mcp-server/db.ts` — PostgreSQL pool + `query()` and `execute()` helpers
- `src/db/schema.ts` — Drizzle table definitions (canonical schema)
- `src/mcp-server/tools/index.ts` — `ALL_TOOLS` array used for MCP registration
- `src/processor/prompts.ts` — DeepSeek extraction prompts

**Testing:**
- `src/mcp-server/tests/tools.test.ts` — Unit tests for all 12 MCP tools

## Naming Conventions

**Files:**
- kebab-case: `scraper-playwright.ts`, `concurrent-deepseek.ts`, `by-entity.ts`
- Noun or hyphenated noun phrase for modules
- Entry points named after their function: `index.ts`, `app.ts`

**Directories:**
- kebab-case for multi-word: `mcp-server/`, `pba/`
- All lowercase single words for others: `scraper/`, `processor/`, `tools/`, `tests/`
- Year directories auto-generated as integers: `1986/`, `2025/`

**Exports:**
- Tools: `{camelName}Tool` (definition object) + `{camelName}Handler` (async function)
- Example: `searchOrdenanzasTool`, `searchOrdenanzasHandler`

## Where to Add New Code

**New MCP Tool:**
1. Add tool definition and handler to appropriate file in `src/mcp-server/tools/` (or create new file for new category)
2. Import and register in `src/mcp-server/tools/index.ts` — add to `ALL_TOOLS` array
3. Add input schema to `src/mcp-server/types.ts`
4. Add tests to `src/mcp-server/tests/tools.test.ts`

**New Processor Variant:**
- Implementation: `src/processor/{name}-{provider}.ts`
- Reuse prompts from `src/processor/prompts.ts`

**New Scraper:**
- Implementation: `src/scraper/`
- Follow `scraper-playwright.ts` pattern: use `CONFIG` from `config.ts`, `ScraperLogger`

**Shared DB Utilities:**
- For MCP server queries: `src/mcp-server/db.ts`
- For processor/ORM usage: `src/db/index.ts`

**Schema Changes:**
- Update Drizzle schema: `src/db/schema.ts`
- Update SQL schema: `database/schema.sql`
- Run setup script: `npx tsx src/db/setup.ts`

## Special Directories

**`.planning/`:**
- Purpose: GSD planning documents and codebase analysis
- Generated: Yes, by GSD tooling
- Committed: Yes

**`graphify-out/`:**
- Purpose: Knowledge graph cache files
- Generated: Yes, by graphify tooling
- Committed: Partially (gitignore may exclude some)

---

*Structure analysis: 2026-05-02*
