# Testing Patterns

**Analysis Date:** 2026-05-02

## Test Framework

**Runner:**
- Vitest (referenced in `src/mcp-server/tests/tools.test.ts`)
- **CRITICAL:** `vitest` is NOT listed in `package.json` dependencies or devDependencies
- Tests cannot run without first installing: `npm install --save-dev vitest`

**Assertion Library:**
- Vitest built-in (`expect`, `describe`, `it`, `beforeEach`, `afterEach`)

**Mocking:**
- `vi` from vitest: `vi.fn()`, `vi.clearAllMocks()`, `vi.restoreAllMocks()`

**Run Commands:**
```bash
# Tests cannot run currently — vitest not installed
# After installing vitest:
npx vitest                           # Run all tests
npx vitest --watch                   # Watch mode
npx vitest --coverage                # Coverage (requires @vitest/coverage-v8)
```

## Test File Organization

**Location:**
- `src/mcp-server/tests/tools.test.ts` — single test file for all 12 MCP tools
- No co-located test files (no `*.test.ts` alongside source files)

**Naming:**
- Suite file: `tools.test.ts`
- No consistent `*.spec.ts` pattern; only `*.test.ts` seen

**Structure:**
```
src/
└── mcp-server/
    └── tests/
        └── tools.test.ts    # All tool tests in one file
```

## Test Structure

**Suite Organization:**
```typescript
describe("MCP Server Tools", () => {
  beforeEach(() => { vi.clearAllMocks(); });
  afterEach(() => { vi.restoreAllMocks(); });

  describe("search_ordenanzas", () => {
    it("debería buscar ordenanzas con query FTS", async () => { ... });
    it("debería manejar errores de búsqueda", async () => { ... });
  });

  describe("get_ordenanza", () => {
    it("debería obtener ordenanza completa", async () => { ... });
    it("debería retornar error si no existe", async () => { ... });
  });
  // ... one describe block per tool
});
```

**Patterns:**
- One `describe` block per MCP tool
- Test names in Spanish: `"debería buscar..."`, `"debería manejar errores..."`
- All tests are `async/await`
- Standard pattern: mock DB → call handler → parse JSON response → assert

**Assertion pattern:**
```typescript
const result = await searchOrdenanzasTool.handler({ query: "test" }, {});
expect(result.content).toBeDefined();
const data = JSON.parse(result.content[0].text);
expect(data.results).toHaveLength(2);
```

## Mocking

**Framework:** `vi.fn()` from vitest

**DB Mock pattern:**
```typescript
const mockDB = {
  query: vi.fn(),
};

// In test:
mockDB.query.mockResolvedValue([{ id: "test-id-1", titulo: "Ordenanza Test" }]);
// For sequential calls:
mockDB.query
  .mockResolvedValueOnce([mainRow])
  .mockResolvedValueOnce([articulos])
  .mockResolvedValueOnce([entidades]);
```

**IMPORTANT — Mock disconnect:**
The `mockDB` object in the test file is defined but **never actually injected** into the real `query` function from `src/mcp-server/db.ts`. The tests call `searchOrdenanzasTool.handler()` which internally imports `query` from `../db.js` — a real pg.Pool that would hit the actual database. The mock has no effect as currently written. Tests would need either:
- `vi.mock("../db.js", ...)` module-level mock, or
- Dependency injection refactor

**What to Mock:**
- Database queries (to avoid requiring real DB in CI)
- External API calls (OpenAI, Groq)

**What NOT to Mock:**
- Zod validation (test real validation)
- JSON parsing logic

## Fixtures and Factories

**Test Data:**
- Inline in each test — no shared fixtures file
- Pattern: define row object matching DB column names directly in the test:
```typescript
const ordenanzaRow = {
  id: "test-id",
  numero: 123,
  anio: 2024,
  titulo: "Ordenanza Test",
  texto_completo: "Texto completo",
};
```

**Location:**
- No `fixtures/` or `factories/` directory
- All test data defined inline within test blocks

## Coverage

**Requirements:** None enforced (no coverage config found)

**View Coverage:**
```bash
# After installing vitest and coverage provider:
npx vitest --coverage
```

## Test Types

**Unit Tests:**
- Only type present: `src/mcp-server/tests/tools.test.ts`
- Scope: MCP tool handler logic (input validation, response shape, error cases)

**Integration Tests:**
- None — no tests that exercise real DB connections

**E2E Tests:**
- None

## Common Patterns

**Async Testing:**
```typescript
it("debería buscar ordenanzas", async () => {
  mockDB.query.mockResolvedValue([...]);
  const result = await searchOrdenanzasTool.handler({ query: "test" }, {});
  expect(result.content).toBeDefined();
});
```

**Error Testing:**
```typescript
it("debería manejar errores", async () => {
  mockDB.query.mockRejectedValue(new Error("DB error"));
  const result = await searchOrdenanzasTool.handler({ query: "test" }, {});
  expect(result.isError).toBe(true);
  const data = JSON.parse(result.content[0].text);
  expect(data.error).toContain("Error al buscar ordenanzas");
});
```

**Testing not-found:**
```typescript
it("debería retornar error si no existe", async () => {
  mockDB.query.mockResolvedValueOnce([]); // Empty result = not found
  const result = await getOrdenanzaTool.handler({ id: "test-id" }, {});
  expect(result.isError).toBe(true);
});
```

## Testing Gaps (Summary)

- `vitest` not installed — entire test suite is non-runnable
- `mockDB` mock never injected into production `query()` — tests would hit real DB
- No tests for scraper, processor, or DB layer
- No integration tests
- No coverage enforcement

See `CONCERNS.md` for full test coverage assessment.

---

*Testing analysis: 2026-05-02*
