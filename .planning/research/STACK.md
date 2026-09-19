# Technology Stack

**Project:** Ordenanzas Saladillo — Semantic Search Milestone
**Researched:** 2026-05-02

## Recommended Stack

### Core: OpenAI Embeddings

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `openai` SDK | 6.22.0 (already installed) | Generate embeddings via `text-embedding-3-large` | Already in project; supports batch input arrays natively |
| `text-embedding-3-large` | current | 3072-dimension vectors for semantic search | Superior multilingual quality vs small; Spanish ordinances benefit from the larger model |

### Concurrency Control

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `p-limit` | ^6.x | Cap concurrent API requests during batch script | Pure ESM, TypeScript-native, zero deps; the project is already `"type": "module"` so p-limit's ESM-only requirement is not a constraint |

### In-Memory Similarity

| Approach | Notes | Why |
|----------|-------|-----|
| Float32Array + manual dot-product loop | Inline, no new dependency | Halves memory vs regular `number[]` arrays (24 MB vs 48 MB for 2000 × 3072); single O(n) pass for cosine similarity is fast enough for this dataset size |

### Token Counting / Truncation

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `tiktoken` (via `js-tiktoken`) | ^1.x | Count tokens before sending to API | Avoids silent 400 errors on oversized ordinances; `js-tiktoken` is WASM-free, works in Node ESM |

---

## API Limits (text-embedding-3-large, Tier 1)

These are the limits to design the batch script around. **Verify in platform.openai.com → Settings → Limits** before running, since tier determines exact values.

| Limit | Tier 1 (approximate) | Tier 2+ |
|-------|----------------------|---------|
| RPM (requests/min) | ~500 | ~3,000+ |
| TPM (tokens/min) | ~1,000,000 | ~5,000,000+ |
| Max tokens per single request (all inputs combined) | 300,000 | 300,000 |
| Max inputs per single API call | 2,048 | 2,048 |
| Max tokens per single input | 8,191 | 8,191 |

**Confidence:** MEDIUM — specific per-tier values not published in a single authoritative table; community sources and inference.net guide align on these approximate Tier 1 figures. Always check the dashboard before production runs.

---

## Batch Processing Strategy

### Regular Endpoint (Synchronous) — Recommended for this project

Use the regular `/v1/embeddings` endpoint with a controlled concurrency loop, **not** the OpenAI Batch API.

**Rationale:**
- The Batch API completes within 24 hours (sometimes 10–20 min in practice), which is acceptable for a one-time pre-generation run, but adds orchestration complexity: upload JSONL file, poll for job status, download results file, parse and insert into DB.
- The regular endpoint with 5–10 concurrent requests completes 2,000 ordinances in under 10 minutes at Tier 1 TPM limits, with no added complexity.
- The Batch API's 50% cost saving on ~2,000 ordinances is negligible: at $0.13/1M tokens, a 2,000-ordinance run averaging 500 tokens each costs ~$0.13 total synchronous vs ~$0.065 batch. Not worth the extra code.
- **Use the Batch API only if the corpus grows to 50,000+ ordinances or cost per run exceeds $10.**

### Batching Within Each API Call

Send multiple ordinance texts per API call (up to 100 items per call is a safe upper bound, well below the 2,048 input limit and the 300K combined token limit). Each ordinance ordinance averages ~500–2,000 tokens; batching 100 at a time stays safely under 200K tokens per request.

```
Outer loop: chunks of 100 ordinances
  → Single openai.embeddings.create({ model, input: [text1, text2, ..., text100] })
  → Insert 100 rows into embeddings_cache in one transaction
Concurrency: p-limit(5) — 5 simultaneous API calls = 500 ordinances in flight
```

**Why 100 inputs / 5 concurrent:**
- 100 × avg 1,000 tokens × 5 concurrent = 500,000 tokens in flight per ~1 second window.
- Tier 1 TPM = 1,000,000 → this stays at ~50% utilization, leaving headroom for retries.
- If rate-limited (HTTP 429), the `openai` SDK's built-in `maxRetries: 2` handles transient spikes; add exponential backoff at the script level for sustained 429s.

### Retry Pattern

```typescript
// openai SDK already handles transient 429s with maxRetries
// For the batch script, add outer retry with exponential backoff:
// 429 → wait (attempt * 10s) → retry
// The SDK exposes RateLimitError which can be caught and rethrown after delay
```

---

## Truncation Strategy

`text-embedding-3-large` max input: **8,191 tokens per item**.

Municipal ordinances in the Saladillo dataset range from short resolutions (~200 tokens) to lengthy zoning codes (~15,000+ tokens). The project already plans a threshold (~8,000 chars ≈ 2,000 tokens) to switch from full text to `resumen`. Refine this as follows:

| Ordinance length | What to embed | Rationale |
|-----------------|---------------|-----------|
| ≤ 6,000 tokens | Full `original` text | Fits within limit; maximizes semantic fidelity |
| > 6,000 tokens | `resumen` + `palabras_clave` concatenated | Resúmenes already exist in DB; avoids chunking complexity; 6,000-token headroom leaves buffer for the token counter's +5% estimation error |

**Why not chunk-and-average:** For search, a single embedding per ordinance is simpler and sufficient. Chunking introduces retrieval complexity (which chunk to return?) without meaningful quality gain for legal-document search at this scale.

**Token counting:** Use `js-tiktoken` with the `cl100k_base` encoder (used by all `text-embedding-3-*` models) to count tokens before deciding which path to take.

```typescript
import { get_encoding } from "js-tiktoken";
const enc = get_encoding("cl100k_base");
const tokenCount = enc.encode(text).length;
enc.free(); // release WASM memory
```

**Confidence:** HIGH — 8,191 token limit confirmed by OpenAI docs and community sources.

---

## In-Memory Cosine Similarity: Performance Analysis

For 2,000 vectors × 3,072 dimensions:

| Representation | Memory | Perf Note |
|---------------|--------|-----------|
| `number[]` (regular JS array) | ~48 MB | JS engine may optimize, but irregular |
| `Float32Array` | ~24 MB | Typed array; JIT-friendly; predictable memory layout |

**Recommendation:** Store loaded vectors as `Float32Array`. At 2,000 vectors, computing all 2,000 cosine similarities for a single query takes:
- 2,000 × 3,072 multiplications + additions = ~12M floating-point ops
- Modern V8 on a laptop: ~50–100ms total — well within acceptable MCP tool response time

**No external library needed.** The existing `calculateCosineSimilarity` function in `embeddings.ts` is correct. Optimize by pre-normalizing stored vectors (compute magnitude once at load time), so each similarity comparison reduces to a dot product only.

```typescript
// Pre-normalize at load time (do once):
function normalize(v: Float32Array): Float32Array {
  let norm = 0;
  for (let i = 0; i < v.length; i++) norm += v[i] * v[i];
  norm = Math.sqrt(norm);
  return v.map(x => x / norm) as Float32Array;
}

// At query time (dot product of two unit vectors = cosine similarity):
function dotProduct(a: Float32Array, b: Float32Array): number {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}
```

**If the corpus grows past ~50,000 ordinances**, revisit pgvector. At that scale, loading all vectors into memory (~600 MB) and scanning linearly becomes impractical.

**Confidence:** HIGH for the math. MEDIUM for the V8 performance estimate — benchmarked pattern from community sources but not measured in this specific environment.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Batch mechanism | Regular endpoint + p-limit | OpenAI Batch API | Batch API adds 10-min to 24-hr latency and JSONL file upload/poll complexity; cost saving is <$0.10 for 2K ordinances |
| Token counting | `js-tiktoken` | `tiktoken` (Python port with WASM) | `tiktoken` has WASM init complexity in ESM; `js-tiktoken` is simpler, same encoder |
| Similarity library | Native Float32Array loop | `simsimd` npm | `simsimd` provides SIMD acceleration but adds a native binary dependency; unnecessary overhead at 2K vectors |
| Concurrency control | `p-limit` | `p-queue` | `p-queue` is more feature-rich (pause, priorities) but overkill for a linear batch script |
| Text selection | Summary for long texts | Chunking + averaging | Chunking adds retrieval complexity; summaries already exist; average embedding quality is adequate |

---

## Installation

```bash
# New dependencies needed:
npm install p-limit js-tiktoken
```

The `openai` SDK (6.22.0), `pg` (8.18.0), `dotenv`, and `pino` are already installed.

---

## Sources

- OpenAI rate limits guide: https://developers.openai.com/api/docs/guides/rate-limits
- OpenAI Batch API guide: https://platform.openai.com/docs/guides/batch
- OpenAI Embeddings guide: https://developers.openai.com/api/docs/guides/embeddings
- Embedding long inputs cookbook: https://cookbook.openai.com/examples/embedding_long_inputs
- OpenAI community — max batch size: https://community.openai.com/t/embeddings-api-max-batch-size/655329
- OpenAI community — max tokens per request: https://community.openai.com/t/max-total-embeddings-tokens-per-request/1254699
- Rate limits guide (inference.net, 2026): https://inference.net/content/openai-rate-limits-guide/
- p-limit npm: https://www.npmjs.com/package/p-limit
- Vercel AI SDK issue — Float32Array cosine optimization: https://github.com/vercel/ai/issues/4593
