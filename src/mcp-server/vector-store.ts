import * as lancedb from "@lancedb/lancedb";
import { logger } from "./logger.js";
import * as path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(__dirname, "..", "..", ".lancedb");

export interface OrdenanzaEmbedding {
  ordenanza_id: string;
  vector: number[];
  numero: number;
  anio: number;
  titulo: string;
  resumen: string;
  estado: string;
}

export interface SearchResult {
  ordenanza_id: string;
  score: number;
  numero: number;
  anio: number;
  titulo: string;
  resumen: string;
  estado: string;
}

// ── Artículo ────────────────────────────────────────────────────

export interface ArticuloEmbedding {
  articulo_id: string;
  ordenanza_id: string;
  numero_articulo: string;
  texto: string;
  numero: number;
  anio: number;
  titulo: string;
  estado: string;
  vector: number[];
}

export interface ArticuloSearchResult {
  articulo_id: string;
  ordenanza_id: string;
  score: number;
  numero_articulo: string;
  texto: string;
  numero: number;
  anio: number;
  titulo: string;
  estado: string;
}

// ── Estado ──────────────────────────────────────────────────────

let _db: lancedb.Connection | null = null;
let _table: lancedb.Table | null = null;
let _articuloTable: lancedb.Table | null = null;
const TABLE_NAME = "ordenanza_embeddings_large";
const ARTICULO_TABLE_NAME = "articulo_embeddings_large";

async function getDb(): Promise<lancedb.Connection> {
  if (!_db) {
    _db = await lancedb.connect(DB_PATH);
  }
  return _db;
}

export async function getTable(): Promise<lancedb.Table | null> {
  if (_table) return _table;
  const db = await getDb();
  const tableNames = await db.tableNames();
  if (tableNames.includes(TABLE_NAME)) {
    _table = await db.openTable(TABLE_NAME);
    return _table;
  }
  return null;
}

export async function createTable(embeddings: OrdenanzaEmbedding[]): Promise<lancedb.Table> {
  const db = await getDb();
  const tableNames = await db.tableNames();

  if (tableNames.includes(TABLE_NAME)) {
    await db.dropTable(TABLE_NAME);
    logger.info("Dropped existing LanceDB table");
  }

  const data = embeddings.map(e => ({
    vector: new Float32Array(e.vector),
    ordenanza_id: e.ordenanza_id,
    numero: e.numero,
    anio: e.anio,
    titulo: e.titulo,
    resumen: e.resumen || "",
    estado: e.estado,
  }));

  const table = await db.createTable(TABLE_NAME, data);

  _table = table;
  logger.info({ count: embeddings.length }, `Created LanceDB table '${TABLE_NAME}'`);
  return table;
}

export async function searchSimilar(
  queryVector: number[],
  limit: number,
  umbral: number,
): Promise<SearchResult[]> {
  const table = await getTable();
  if (!table) return [];

  const q = (table.search(new Float32Array(queryVector)) as lancedb.VectorQuery)
    .distanceType("cosine")
    .limit(limit * 5)
    .bypassVectorIndex();

  const results = await q.toArray();

  const mapped: SearchResult[] = [];
  for (const r of results) {
    const distance = (r as any)._distance ?? 1;
    const score = 1 - distance;

    if (score < umbral) continue;

    mapped.push({
      ordenanza_id: r.ordenanza_id as string,
      score: Math.round(score * 1e6) / 1e6,
      numero: r.numero as number,
      anio: r.anio as number,
      titulo: r.titulo as string,
      resumen: (r.resumen as string) || "",
      estado: r.estado as string,
    });

    if (mapped.length >= limit) break;
  }

  return mapped;
}

// ── Artículo operations ─────────────────────────────────────────

export async function getArticuloTable(): Promise<lancedb.Table | null> {
  if (_articuloTable) return _articuloTable;
  const db = await getDb();
  const tableNames = await db.tableNames();
  if (tableNames.includes(ARTICULO_TABLE_NAME)) {
    _articuloTable = await db.openTable(ARTICULO_TABLE_NAME);
    return _articuloTable;
  }
  return null;
}

export async function createArticuloTable(embeddings: ArticuloEmbedding[]): Promise<lancedb.Table> {
  const db = await getDb();
  const tableNames = await db.tableNames();

  if (tableNames.includes(ARTICULO_TABLE_NAME)) {
    await db.dropTable(ARTICULO_TABLE_NAME);
    logger.info("Dropped existing LanceDB articulo table");
  }

  const data = embeddings.map(e => ({
    vector: new Float32Array(e.vector),
    articulo_id: e.articulo_id,
    ordenanza_id: e.ordenanza_id,
    numero_articulo: e.numero_articulo,
    texto: e.texto,
    numero: e.numero,
    anio: e.anio,
    titulo: e.titulo,
    estado: e.estado,
  }));

  const table = await db.createTable(ARTICULO_TABLE_NAME, data);
  _articuloTable = table;
  logger.info({ count: embeddings.length }, `Created LanceDB articulo table`);
  return table;
}

export async function searchArticulosSimilar(
  queryVector: number[],
  limit: number,
  umbral: number,
): Promise<ArticuloSearchResult[]> {
  const table = await getArticuloTable();
  if (!table) return [];

  const q = (table.search(new Float32Array(queryVector)) as lancedb.VectorQuery)
    .distanceType("cosine")
    .limit(limit * 5)
    .bypassVectorIndex();

  const results = await q.toArray();

  const mapped: ArticuloSearchResult[] = [];
  for (const r of results) {
    const rAny = r as any;
    const distance = rAny._distance ?? 1;
    const score = 1 - distance;

    if (score < umbral) continue;

    mapped.push({
      articulo_id: rAny.articulo_id as string,
      ordenanza_id: rAny.ordenanza_id as string,
      score: Math.round(score * 1e6) / 1e6,
      numero_articulo: rAny.numero_articulo as string,
      texto: rAny.texto as string,
      numero: rAny.numero as number,
      anio: rAny.anio as number,
      titulo: rAny.titulo as string,
      estado: rAny.estado as string,
    });

    if (mapped.length >= limit) break;
  }

  return mapped;
}
