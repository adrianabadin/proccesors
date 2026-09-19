# Graph Report - .  (2026-05-02)

## Corpus Check
- 69 files · ~35,742 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 303 nodes · 384 edges · 45 communities detected
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.76)
- Token cost: 2,800 input · 1,650 output

## God Nodes (most connected - your core abstractions)
1. `TaskQueue` - 9 edges
2. `DatabaseBatcher` - 9 edges
3. `DeepSeekWorker` - 8 edges
4. `extractStructure()` - 8 edges
5. `main()` - 7 edges
6. `ScraperLogger` - 7 edges
7. `main()` - 6 edges
8. `Concurrent DeepSeek Processor` - 6 edges
9. `main()` - 5 edges
10. `logVerbose()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Scraper Logger Module (logger.ts)` --semantically_similar_to--> `Concurrent DeepSeek Processor`  [INFERRED] [semantically similar]
  src/scraper/README-SCRAPER.md → src/processor/README-concurrent-deepseek.md
- `PostgreSQL Database` --semantically_similar_to--> `Ordenanza TXT Files (Output Storage)`  [INFERRED] [semantically similar]
  src/processor/README-concurrent-deepseek.md → src/scraper/README-SCRAPER.md
- `Ordenanza TXT Files (Output Storage)` --shares_data_with--> `Concurrent DeepSeek Processor`  [INFERRED]
  src/scraper/README-SCRAPER.md → src/processor/README-concurrent-deepseek.md

## Hyperedges (group relationships)
- **Concurrent Processing Pipeline: Queue -> Workers -> Batcher -> DB** — task_queue, worker_pool, database_batcher, postgresql_db [EXTRACTED 1.00]
- **Scraper Module System: Config, Types, Utils, Logger, Extractor, Downloader** — scraper_config, scraper_types, scraper_utils, scraper_logger, link_extractor, ordinance_downloader [EXTRACTED 1.00]
- **Error Resilience Pattern: Circuit Breaker + Retry + ERROR_v1 Marker** — circuit_breaker, exponential_backoff, error_v1_marker [EXTRACTED 0.95]
- **Ordenanzas Full Data Pipeline: Scraper -> TXT Files -> Processor -> PostgreSQL** — scraper_playwright, ordenanza_txt_files, concurrent_deepseek_processor, postgresql_db [INFERRED 0.80]

## Communities

### Community 0 - "PBA Normas Scraper"
Cohesion: 0.06
Nodes (11): callGLMAPI(), loadCategoryLookup(), main(), persistExtraction(), sleep(), generateSummary(), getOrCreateSummary(), generateEmbedding() (+3 more)

### Community 1 - "Concurrent Processor Core"
Cohesion: 0.1
Nodes (8): CircuitBreaker, DatabaseBatcher, DeepSeekWorker, loadCategoryLookup(), logVerbose(), main(), sleep(), TaskQueue

### Community 2 - "Processing Pipeline Design"
Cohesion: 0.07
Nodes (25): Circuit Breaker (Fail Fast), Concurrent DeepSeek Processor, Database Batcher (Batch Size 5), DeepSeek API (OpenAI-compatible), DeepSeek-V3.2 Model (128K context), ERROR_v1 Resumibility Marker, Exponential Backoff Retry, HCD Saladillo Website (hcd.saladillo.gob.ar) (+17 more)

### Community 3 - "Utility Functions"
Cohesion: 0.15
Nodes (2): errorMessage(), toolError()

### Community 4 - "Embedding System"
Cohesion: 0.23
Nodes (5): formatVector(), generateEmbedding(), getEmbedding(), getOrCreateEmbedding(), parseVector()

### Community 5 - "Logging Infrastructure"
Cohesion: 0.22
Nodes (1): ScraperLogger

### Community 6 - "Gemini Classifier"
Cohesion: 0.36
Nodes (6): callGeminiAPI(), isGeminiAPIError(), loadCategoryLookup(), main(), persistExtraction(), sleep()

### Community 7 - "Ordinance Field Extractor"
Cohesion: 0.42
Nodes (8): extractArticulos(), extractExpediente(), extractFechaSancion(), extractMontos(), extractReferencias(), extractSeccionConsiderando(), extractSeccionVisto(), extractStructure()

### Community 8 - "DeepSeek Classifier"
Cohesion: 0.39
Nodes (5): callDeepSeekAPI(), loadCategoryLookup(), main(), persistExtraction(), sleep()

### Community 9 - "Groq Classifier"
Cohesion: 0.39
Nodes (5): callGroqAPI(), loadCategoryLookup(), main(), persistExtraction(), sleep()

### Community 10 - "Base Classifier"
Cohesion: 0.39
Nodes (5): callGeminiAPI(), loadCategoryLookup(), main(), persistExtraction(), sleep()

### Community 11 - "Local NLP Classifier"
Cohesion: 0.46
Nodes (7): classifyText(), detectEstado(), generateKeywords(), getClassifier(), getSummarizer(), processWithAI(), summarizeText()

### Community 12 - "Database Ingestion"
Cohesion: 0.52
Nodes (6): escanearDirectorios(), extraerExtracto(), insertarBatch(), main(), parseNumeroFromFilename(), procesarArchivo()

### Community 13 - "Article Generator"
Cohesion: 0.48
Nodes (5): extractArticulosFromText(), generateEmbedding(), insertArticuloToDatabase(), main(), processArticulos()

### Community 14 - "LLM-based Extractor"
Cohesion: 0.6
Nodes (5): extractCleanTextFromHtml(), extractNormaDetailsWithBigModel(), fetchHtml(), main(), processAllNormas()

### Community 15 - "Database Pool"
Cohesion: 0.6
Nodes (3): execute(), healthCheck(), query()

### Community 16 - "Local Processing Pipeline"
Cohesion: 0.6
Nodes (3): loadCategoryLookup(), main(), persistExtraction()

### Community 17 - "Interactive CLI Runner"
Cohesion: 0.7
Nodes (4): ask(), main(), printMenu(), runProcessor()

### Community 18 - "PBA Normas DeepSeek Extractor"
Cohesion: 0.6
Nodes (4): extractNormaDetails(), fetchHtmlWithProxy(), main(), processAllNormas()

### Community 19 - "Embedding Generator"
Cohesion: 0.5
Nodes (2): main(), saveNormasToDatabase()

### Community 20 - "BigModel Embedding Generator"
Cohesion: 0.6
Nodes (3): generateBigModelEmbedding(), main(), saveNormasToDatabase()

### Community 21 - "DB Population Script"
Cohesion: 0.7
Nodes (4): generateEmbedding(), insertNormaToDatabase(), main(), saveNormasToDatabase()

### Community 22 - "Extraction Test Suite"
Cohesion: 0.7
Nodes (4): extractNormaDetails(), fetchHtmlWithProxy(), main(), testSingleNorma()

### Community 23 - "BigModel Extraction Tests"
Cohesion: 0.7
Nodes (4): extractNormaDetailsWithGroq(), fetchHtmlWithProxy(), main(), testSingleNorma()

### Community 24 - "MCP Search Tools"
Cohesion: 0.5
Nodes (0): 

### Community 25 - "Model Comparison Tests"
Cohesion: 0.83
Nodes (3): callGroqAPI(), main(), sleep()

### Community 26 - "PBA Normas Parser"
Cohesion: 0.67
Nodes (3): extract_norma_from_html(), main(), Extrae información estructurada de HTML usando DeepSeek API.      Args:

### Community 27 - "MCP By-ID Tools"
Cohesion: 0.67
Nodes (0): 

### Community 28 - "Response Parser"
Cohesion: 0.67
Nodes (0): 

### Community 29 - "Data Cleanup"
Cohesion: 1.0
Nodes (2): cleanAndSaveData(), main()

### Community 30 - "MCP By-Entity Tools"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "MCP Categories Tool"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "MCP Health Check"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "MCP References Tool"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "MCP Similar Ordinances"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "MCP Stats Tool"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "MCP Summarize Tool"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Prompt Builder"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "SINDMA Crawler"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "SINDMA Debug"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Schema Cache"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Database Schema"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Type Definitions"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Tool Tests"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Simple Scraper"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **14 isolated node(s):** `Extrae información estructurada de HTML usando DeepSeek API.      Args:`, `ERROR_v1 Resumibility Marker`, `DeepSeek-V3.2 Model (128K context)`, `Rationale: Concurrent Architecture for VPS Constraints`, `Rationale: Batch Size 5 for RAM Optimization` (+9 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `MCP By-Entity Tools`** (2 nodes): `by-entity.ts`, `searchByEntityHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP Categories Tool`** (2 nodes): `categories.ts`, `listCategoriesHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP Health Check`** (2 nodes): `health.ts`, `healthCheckHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP References Tool`** (2 nodes): `references.ts`, `getReferencesHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP Similar Ordinances`** (2 nodes): `similar.ts`, `similarOrdenanzasHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP Stats Tool`** (2 nodes): `stats.ts`, `getStatsHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `MCP Summarize Tool`** (2 nodes): `summarize.ts`, `summarizeTextoHandler()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Prompt Builder`** (2 nodes): `prompts.ts`, `buildUserPrompt()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SINDMA Crawler`** (2 nodes): `crawler_sindma.ts`, `runLimitedCrawl()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `SINDMA Debug`** (2 nodes): `debug_sindma.ts`, `debugPageStructure()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Schema Cache`** (1 nodes): `schema-cache.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Database Schema`** (1 nodes): `schema.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Type Definitions`** (1 nodes): `types.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tool Tests`** (1 nodes): `tools.test.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Simple Scraper`** (1 nodes): `scraper-simple.ts`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `Extrae información estructurada de HTML usando DeepSeek API.      Args:`, `ERROR_v1 Resumibility Marker`, `DeepSeek-V3.2 Model (128K context)` to the rest of the system?**
  _14 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `PBA Normas Scraper` be split into smaller, more focused modules?**
  _Cohesion score 0.06 - nodes in this community are weakly interconnected._
- **Should `Concurrent Processor Core` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `Processing Pipeline Design` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._