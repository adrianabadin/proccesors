# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **web scraping and NLP pipeline** for municipal ordinances ("ordenanzas") from the Saladillo city council website (hcd.saladillo.gob.ar). The project scrapes ordinance texts, stores them as `.txt` files organized by year, and experiments with AI-based classification and summarization.

## Tech Stack

- **Runtime**: Node.js with TypeScript (ts-node/tsx for execution)
- **Scraping**: Native `fetch` + `jsdom` for HTML parsing
- **NLP/AI**: `@xenova/transformers` (zero-shot classification, summarization)
- **Database**: Knex.js with PostgreSQL (`pg`) and SQLite3 (currently commented out / experimental)
- **Linting**: ESLint with TypeScript plugin + Prettier

## Commands

```bash
# Run TypeScript files directly
npx tsx app.ts        # Main scraper
npx tsx ia.ts         # Classification/NLP experiments
npx tsx otro.ts       # Alternative classification approach

# Linting
npm run lint          # ESLint check
npm run lint:fix      # ESLint auto-fix
```

## Architecture

- **`app.ts`** — Main scraper. Fetches paginated ordinance listings from the council website, extracts links, downloads full text, and saves to `{year}/Ordenanza N° {number}.txt`.
- **`ia.ts`** — NLP experiments using Xenova/transformers. Zero-shot classification of ordinances into ~33 municipal categories (e.g., "Servicios Públicos", "Tasas y Tarifas"). Contains commented-out Knex/PostgreSQL code for storing results.
- **`otro.ts`** — Alternative classification approach combining summarization + classification pipelines.
- **`cosa.js`** — Browser-based scraper variant (runs in DevTools, uses DOMParser).
- **Year directories (`1986/`–`2025/`)** — Scraped ordinance text files, one per ordinance.

## Key Patterns

- The scraper uses randomized delays (`Math.random()*2000`) to avoid rate limiting.
- Ordinance titles follow the pattern `Ordenanza N° {number}/{year}`.
- Classification uses Spanish-language hypothesis templates: `"El documento legal trata sobre {}"`.
- The codebase is in Spanish (variable names, comments, labels).

## Database Schema (experimental)

```typescript
interface Ordenanzas {
    id: string,        // UUID
    title: string,
    original: string,  // Full text or source URL
    sumary: string,
    classification: string
}
```

## Notes

- TypeScript is configured with `es2022` target and `esnext` modules.
- The `tsconfig.json` expects source in `src/` but current scripts live at the root — run with `tsx` directly rather than compiling.
- The `undefined/` directory is a bug artifact from ordinances missing year data in their title.
