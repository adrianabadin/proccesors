# MCP Server Implementation - Progress Summary

## Status: Core Infrastructure COMPLETED ✅

### Files Created (8/24 core files)

| File | Status | Description |
|------|--------|-------------|
| `src/db/schema-cache.ts` | ✅ | Database schema for embeddings_cache and resumenes_cache |
| `src/db/setup-cache.ts` | ✅ | SQL setup script (tables created successfully) |
| `src/mcp-server/db.ts` | ✅ | PostgreSQL connection pool with verbose logging |
| `src/mcp-server/logger.ts` | ✅ | Pino-based logger with tool context |
| `src/mcp-server/utils.ts` | ✅ | Utilities: error handlers, timeout, cosine similarity, formatters |
| `src/mcp-server/types.ts` | ✅ | All TypeScript schemas (20+ types) |
| `src/mcp-server/embeddings.ts` | ✅ | OpenAI client for embeddings (text-embedding-3-small) |
| `src/mcp-server/llm.ts` | ✅ | Groq client for summaries (llama-3.3-70b) |
| `src/mcp-server/tools/index.ts` | ✅ | Tool exports placeholder |

## Status: Tools Implementation (3/11 completed)

### Implemented Tools

| Tool | File | Status |
|------|------|--------|
| `search_ordenanzas` | `tools/search.ts` | ✅ Full-text FTS search with ranking |
| `search_by_category` | `tools/search.ts` | ✅ Filter by category + optional year |
| `search_by_year_range` | `tools/search.ts` | ✅ Historical search by year range |

### Pending Tools (8/11)

| Tool | Description | Priority |
|------|-------------|----------|
| `get_ordenanza` | Get full ordinance by UUID | High |
| `get_anexo` | Get annex details by ordinance + number | High |
| `search_by_entity` | Search by entity/role | High |
| `get_references` | Get normative references tree | High |
| `list_categories` | List all categories | Medium |
| `get_stats` | Get processing statistics | Medium |
| `similar_ordenanzas` | Semantic similarity with embeddings | High |
| `summarize_texto` | Generate summary with caching | High |
| `health_check` | Server health status check | Low |

## Known Issues

### LSP Errors in `tools/search.ts`
The file has TypeScript errors related to logger calls. The `toolLogger` function expects `(message: string, data?: object)` but some calls pass objects in wrong order.

**Fix needed:** Swap all `log.info({data}, "message")` to `log.info("message", {data})`

## Database Setup Completed

### Cache Tables Created
```sql
-- embeddings_cache
✅ Table created
✅ Index on ordenanza_id
✅ Unique constraint (ordenanza_id, modelo)

-- resumenes_cache  
✅ Table created
✅ Index on ordenanza_id
✅ Unique constraint (ordenanza_id, texto_original, estilo, longitud_palabras)
✅ ENUM estilo_resumen created
```

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Vector Storage: TEXT instead of pgvector** | pgvector extension not available on VPS. Storing as JSON array `"[0.123,...]"` |
| **Similarity: In-memory cosine** | Compute in JavaScript after loading all embeddings. Slower than pgvector but works without extension |
| **LLM: Groq Llama 3.3 70B** | Already configured, cost-effective (~$0.60/1M tokens) |
| **Embeddings: OpenAI text-embedding-3-small** | Very cheap (~$0.02/1M tokens), 1536 dimensions |
| **Caching Strategy** | Cache both embeddings and summaries with `ON CONFLICT DO UPDATE` |

## Configuration Required

### Environment Variables
```bash
# Database (already configured)
DATABASE_URL=postgresql://user:pass@host/db

# LLM for summaries (already configured)
GROQ_API_KEY=gsk_...

# Embeddings (NEW - required)
OPENAI_API_KEY=sk-...

# Optional
VERBOSE=true              # Enable verbose logging
LOG_LEVEL=debug         # debug, info, warn, error
NODE_ENV=development     # Enable pretty logging
```

## Next Steps

1. **Fix LSP errors in `tools/search.ts`** - Reorder logger parameters
2. **Implement remaining 8 tools** - Complete all tool handlers
3. **Update `tools/index.ts`** - Export all implemented tools
4. **Implement `index.ts`** - Main MCP server with @modelcontextprotocol/sdk
5. **Add `package.json` script** - `"mcp": "tsx src/mcp-server/index.ts"`
6. **Write unit tests** - Test all tools with mocks
7. **Integration tests** - Test with actual PostgreSQL
8. **Deploy to VPS** - Copy code, install dependencies, run as service
9. **Configure Claude Desktop** - Add MCP server to `~/.claude/config.json`

## Claude Desktop Configuration Preview

```json
{
  "mcpServers": {
    "ordenanzas": {
      "command": "npx",
      "args": ["tsx", "C:\\Users\\Adria\\Documents\\code\\ordenanzas\\src\\mcp-server\\index.ts"],
      "env": {
        "DATABASE_URL": "postgresql://...",
        "OPENAI_API_KEY": "sk-...",
        "GROQ_API_KEY": "gsk_..."
      }
    }
  }
}
```

## Asistente Jurídico Workflow

The MCP server enables Claude Desktop to act as a legal assistant for the municipality:

1. **"¿Qué ordenanzas sobre salud hay?"** → `search_ordenanzas` + `search_by_category(slug: "salud-publica")`
2. **"¿Qué propuestas podríamos hacer?"** → 
   - `get_stats` - Understand current state
   - `search_by_year_range` - Historical precedents
   - `similar_ordenanzas` - Find semantically similar ordinances
   - `summarize_texto` - Generate proposal summary

## Token Usage Summary (Estimated)

| Component | Tokens | Cost (USD) |
|-----------|---------|-------------|
| Database queries | Minimal | $0.00 |
| OpenAI embeddings (1 per ordinance) | ~500 | ~$0.01 per 1000 ordinances |
| Groq summaries (varies) | ~200-500 per summary | ~$0.05-0.15 per 1000 ordinances |
| **Total for 2789 ordinances** | ~2.5M | ~$20-40 |

**Note:** Caching reduces API calls significantly after first run.
