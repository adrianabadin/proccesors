# Coding Conventions

**Analysis Date:** 2026-05-02

## Naming Patterns

**Files:**
- kebab-case for all source files: `by-entity.ts`, `concurrent-deepseek.ts`, `scraper-playwright.ts`
- Tool group files named after query dimension: `search.ts`, `by-id.ts`, `by-entity.ts`, `references.ts`, `categories.ts`
- Entry points: `index.ts` for library modules, descriptive names for scripts

**Functions:**
- camelCase: `searchOrdenanzasHandler`, `getOrCreateEmbedding`, `loadCategoryLookup`
- Tool handlers: `{toolName}Handler` — always paired with `{toolName}Tool` definition object
- Async functions are the norm; pure sync helpers are rare

**Variables:**
- camelCase for local variables: `taskQueue`, `dbBatcher`, `categoryLookup`
- ALL_CAPS for module-level config constants: `CONFIG`, `ALL_TOOLS`, `EMBEDDING_MODEL`, `PROMPT_VERSION`
- `_` prefix not used; unused vars avoided

**Types / Interfaces:**
- PascalCase for interfaces, types, classes: `OrdenanzaRow`, `ProcessingResult`, `CircuitBreaker`
- Zod schemas suffixed with `Schema`: `SearchOrdenanzasInputSchema`, `OrdenanzaSummarySchema`
- Zod-inferred types have no suffix: `type SearchOrdenanzasInput = z.infer<typeof SearchOrdenanzasInputSchema>`

**Database columns:**
- Drizzle schema: camelCase property names mapping to snake_case column names
  - `textoCompleto` → `texto_completo`, `procesadoIa` → `procesado_ia`
- Raw SQL queries: snake_case column names matching PostgreSQL convention

**Exports:**
- Named exports only — no default exports observed
- Tool files export both the definition and handler:
  ```typescript
  export const searchOrdenanzasTool = { name, title, description, inputSchema };
  export async function searchOrdenanzasHandler(args, ctx) { ... }
  ```

## Code Style

**Formatting:**
- No Prettier or ESLint config file present at root (`.eslintrc*`, `.prettierrc*` not found)
- Indentation: 2 spaces
- Strings: double quotes preferred (TypeScript files), single quotes in some scraper files
- Semicolons: used
- Trailing commas: used in multi-line arrays/objects

**Type Safety:**
- `strict: true` in tsconfig — all strict checks enabled
- `any` used sparingly and only in specific places: handler `ctx: any`, tool registration cast `handler as any`
- All function parameters typed explicitly; return types often inferred
- Zod used for runtime validation of external inputs (MCP tool args)

## Import Organization

**Order (observed pattern):**
1. External packages: `import { McpServer } from "@modelcontextprotocol/sdk/server/mcp"`
2. Node built-ins: `import { existsSync, mkdirSync } from "fs"`
3. Internal modules: `import { logger } from "./logger.js"`
4. Types: `import type { ... }` (occasionally)

**Path style:**
- Relative imports with `.js` extension: `import { query } from "../db.js"`
- Required because `moduleResolution: bundler` resolves ESM imports literally
- No path aliases configured

**Zod import:**
- Always imported as namespace: `import * as z from "zod/v4"` (not `from "zod"`)
- This is the new Zod v4 API; do not use `from "zod"` in this codebase

## Error Handling

**MCP Tool Pattern:**
```typescript
try {
  // ... query and format result
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
} catch (error) {
  log.error("Operation failed", { error: error instanceof Error ? error.message : String(error) });
  return {
    content: [{ type: "text", text: JSON.stringify({ error: `Error message: ${...}` }) }],
    isError: true,
  };
}
```

**Processor Pattern:**
- Per-item errors caught, logged, and recorded as `ERROR_v1` in DB
- Fatal configuration errors: `process.exit(1)`
- Network errors retried with exponential backoff (base 2s, up to 3 attempts)

**Guard pattern for optional services:**
```typescript
if (!isLLMConfigured()) {
  return { content: [...], isError: true };
}
```

## Logging

**Framework:** Pino (MCP server), console.log (processor)

**Pino API — CRITICAL:**
- Data object goes FIRST, message string goes SECOND:
  ```typescript
  logger.info({ count: results.length }, "Search completed");  // CORRECT
  logger.info("Search completed", { count: results.length });  // WRONG - breaks pino
  ```
- Use `toolLogger(toolName)` wrapper for tool-level logging — it prepends `{ tool: toolName }` to all entries
- All logs go to stderr to avoid corrupting MCP stdio protocol on stdout

**Log levels:**
- `debug`: query details, cache hits, vector operations
- `info`: operation start/completion, server lifecycle events
- `warn`: missing optional config (API keys), circuit breaker trips
- `error`: DB failures, API errors, fatal conditions

## Comments

**When to Comment:**
- JSDoc on exported functions and types (common in `src/mcp-server/`)
- Section dividers with `// ===...===` headers for large files
- "NOTA:" prefix for important implementation decisions (e.g., why pgvector not used)

**JSDoc style:**
```typescript
/**
 * Wrapper para query con logging verbose
 * 
 * @param sql - SQL query string
 * @param params - Query parameters
 * @returns Array of result rows
 */
export async function query<T = any>(sql: string, params?: any[]): Promise<T[]>
```

**Spanish vs English:**
- Comments and JSDoc in Spanish throughout the MCP server and processor
- Variable/function names mix both (e.g., `ordenanza`, `categorias` are Spanish domain terms; `logger`, `pool`, `query` are English)
- Error messages to MCP clients in Spanish: `"Error al buscar ordenanzas: ..."`

## Function Design

**Size:** Handlers are typically 50–80 lines; helper functions 10–30 lines

**Parameters:**
- Tool handlers always: `(args: z.infer<typeof InputSchema>, ctx: any)`
- Utility functions use explicit typed params
- Config objects preferred for functions with 3+ related params

**Return Values:**
- Tool handlers return `Promise<any>` (MCP protocol shape)
- DB helpers return `Promise<T[]>` where T defaults to `any`
- Boolean flag functions end in `isConfigured()`, `isEmpty()`, `isFinished()`

## Module Design

**Exports:** Named exports exclusively; barrel `index.ts` files used in `src/mcp-server/tools/`

**Barrel Files:** `src/mcp-server/tools/index.ts` re-exports all tools and exports `ALL_TOOLS` array. Pattern: import first, then re-export:
```typescript
import { searchOrdenanzasTool, searchOrdenanzasHandler } from "./search.js";
// ... more imports
export { searchOrdenanzasTool, searchOrdenanzasHandler, ... };
export const ALL_TOOLS = [...];
```

**Class usage:** Classes only used in processor (`CircuitBreaker`, `TaskQueue`, `DatabaseBatcher`, `DeepSeekWorker`) and scraper (`LinkExtractor`, `OrdinanceDownloader`, `ScraperLogger`). MCP tools are functional.

---

*Convention analysis: 2026-05-02*
