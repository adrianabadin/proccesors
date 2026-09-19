#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inicializa el esquema SQLite para SIBOM en sibom/sibom.db.

Crea las tablas:
- normas
- articulos
- referencias_normativas
- anexos
- normas_fts (FTS5 con triggers)
- v_arbol_vigencia (Vista unificada de vigencia entrante y saliente)
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIBOM_DIR = ROOT / "sibom"
DB_PATH = SIBOM_DIR / "sibom.db"

DDL = """
-- Habilitar foreign keys
PRAGMA foreign_keys = ON;

-- =============================================================================
-- TABLA: normas
-- =============================================================================
CREATE TABLE IF NOT EXISTS normas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo                    TEXT NOT NULL CHECK(tipo IN ('ordenanza', 'decreto')),
    numero                  INTEGER,
    anio                    INTEGER,
    numero_sibom            TEXT,
    fecha                   TEXT,                   -- YYYY-MM-DD
    boletin                 INTEGER,
    boletin_id              INTEGER,
    contenido_id            INTEGER UNIQUE NOT NULL,
    version                 TEXT NOT NULL CHECK(version IN ('completa', 'extractada')),
    titulo                  TEXT NOT NULL,
    seccion_visto           TEXT,
    seccion_considerando    TEXT,
    texto_completo          TEXT NOT NULL,
    estado                  TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificada', 'derogada_total', 'derogada_parcial', 'sin_determinar')),
    notas_vigencia          TEXT,
    summary                 TEXT,                   -- Resumen consolidado para lectura
    summary_trata           TEXT,                   -- Objeto / Materia
    summary_resuelve        TEXT,                   -- Disposición resolutiva
    summary_depende         TEXT,                   -- Antecedentes (expedientes, leyes, normas)
    embedding_summary       BLOB,                   -- Vector binario float32
    embedding_texto         BLOB,                   -- Vector binario float32
    tambien_en              TEXT,                   -- JSON array de republicaciones
    url                     TEXT NOT NULL,
    archivo_md              TEXT NOT NULL,
    localidad               TEXT NOT NULL DEFAULT 'Saladillo',
    codigo_localidad        INTEGER NOT NULL DEFAULT 108,
    procesado_llm           INTEGER NOT NULL DEFAULT 0, -- 0: pendiente, 1: hecho, 2: extractada_directa, -1: error
    fecha_procesado_llm     TEXT,
    created_at              TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_normas_tipo_num_anio ON normas(tipo, numero, anio);
CREATE INDEX IF NOT EXISTS idx_normas_localidad ON normas(codigo_localidad, tipo);
CREATE INDEX IF NOT EXISTS idx_normas_localidad_num ON normas(codigo_localidad, tipo, numero, anio);
CREATE INDEX IF NOT EXISTS idx_normas_boletin ON normas(boletin);
CREATE INDEX IF NOT EXISTS idx_normas_estado ON normas(estado);
CREATE INDEX IF NOT EXISTS idx_normas_procesado_llm ON normas(procesado_llm);

-- =============================================================================
-- TABLA: articulos
-- =============================================================================
CREATE TABLE IF NOT EXISTS articulos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_id                INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
    numero_articulo         TEXT NOT NULL,          -- "1", "2", "3 bis", etc.
    orden                   INTEGER NOT NULL,       -- 1, 2, 3...
    texto                   TEXT NOT NULL,
    resumen                 TEXT,
    estado                  TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificado', 'derogado', 'sin_determinar')),
    modificado_por_norma_id INTEGER REFERENCES normas(id) ON DELETE SET NULL,
    created_at              TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(norma_id, numero_articulo)
);

CREATE INDEX IF NOT EXISTS idx_articulos_norma ON articulos(norma_id);
CREATE INDEX IF NOT EXISTS idx_articulos_estado ON articulos(estado);

-- =============================================================================
-- TABLA: referencias_normativas (Grafo de Vigencia)
-- =============================================================================
CREATE TABLE IF NOT EXISTS referencias_normativas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_origen_id         INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
    norma_destino_id        INTEGER REFERENCES normas(id) ON DELETE SET NULL,
    destino_tipo            TEXT NOT NULL,          -- ordenanza, decreto, ley_provincial, decreto_provincial, ley_nacional, otro
    destino_numero          INTEGER,
    destino_anio            INTEGER,
    destino_referencia      TEXT,                   -- "Ley 11.723", "Decreto-Ley 6769/58", "Expte 145/2023"
    tipo_relacion           TEXT NOT NULL CHECK(tipo_relacion IN (
                                'deroga_total',
                                'deroga_parcial',
                                'modifica',
                                'sustituye',
                                'prorroga',
                                'convalida',
                                'adhiere',
                                'reglamenta',
                                'cita'
                            )),
    articulos_afectados     TEXT,                   -- "Arts. 1 y 3"
    texto_cita              TEXT,                   -- Texto exacto donde se formula la relación
    notas                   TEXT,
    created_at              TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_ref_origen ON referencias_normativas(norma_origen_id);
CREATE INDEX IF NOT EXISTS idx_ref_destino ON referencias_normativas(norma_destino_id);
CREATE INDEX IF NOT EXISTS idx_ref_tipo ON referencias_normativas(tipo_relacion);

-- =============================================================================
-- TABLA: anexos
-- =============================================================================
CREATE TABLE IF NOT EXISTS anexos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_id                INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
    nombre                  TEXT NOT NULL,
    archivo_pdf             TEXT,                   -- Ruta relativa en sibom/anexos/
    url                     TEXT NOT NULL,
    created_at              TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_anexos_norma ON anexos(norma_id);

-- =============================================================================
-- FULL TEXT SEARCH (FTS5)
-- =============================================================================
CREATE VIRTUAL TABLE IF NOT EXISTS normas_fts USING fts5(
    titulo,
    summary,
    texto_completo,
    seccion_visto,
    seccion_considerando,
    content='normas',
    content_rowid='id'
);

-- Triggers para mantener normas_fts sincronizada automáticamente
CREATE TRIGGER IF NOT EXISTS trg_normas_ai AFTER INSERT ON normas BEGIN
    INSERT INTO normas_fts(rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
    VALUES (new.id, new.titulo, new.summary, new.texto_completo, new.seccion_visto, new.seccion_considerando);
END;

CREATE TRIGGER IF NOT EXISTS trg_normas_ad AFTER DELETE ON normas BEGIN
    INSERT INTO normas_fts(normas_fts, rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
    VALUES('delete', old.id, old.titulo, old.summary, old.texto_completo, old.seccion_visto, old.seccion_considerando);
END;

CREATE TRIGGER IF NOT EXISTS trg_normas_au AFTER UPDATE ON normas BEGIN
    INSERT INTO normas_fts(normas_fts, rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
    VALUES('delete', old.id, old.titulo, old.summary, old.texto_completo, old.seccion_visto, old.seccion_considerando);
    INSERT INTO normas_fts(rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
    VALUES (new.id, new.titulo, new.summary, new.texto_completo, new.seccion_visto, new.seccion_considerando);
END;

-- =============================================================================
-- VISTA: v_arbol_vigencia
-- =============================================================================
DROP VIEW IF EXISTS v_arbol_vigencia;
CREATE VIEW v_arbol_vigencia AS
SELECT 
    'afecta_a' AS direccion,
    r.id AS referencia_id,
    r.norma_origen_id,
    no.tipo AS origen_tipo,
    no.numero AS origen_numero,
    no.anio AS origen_anio,
    r.tipo_relacion,
    r.norma_destino_id,
    nd.tipo AS destino_tipo,
    COALESCE(nd.numero, r.destino_numero) AS destino_numero,
    COALESCE(nd.anio, r.destino_anio) AS destino_anio,
    r.destino_referencia,
    r.articulos_afectados,
    r.texto_cita,
    r.notas
FROM referencias_normativas r
JOIN normas no ON no.id = r.norma_origen_id
LEFT JOIN normas nd ON nd.id = r.norma_destino_id
UNION ALL
SELECT 
    'afectada_por' AS direccion,
    r.id AS referencia_id,
    r.norma_destino_id AS norma_origen_id,
    nd.tipo AS origen_tipo,
    nd.numero AS origen_numero,
    nd.anio AS origen_anio,
    r.tipo_relacion,
    r.norma_origen_id AS norma_destino_id,
    no.tipo AS destino_tipo,
    no.numero AS destino_numero,
    no.anio AS destino_anio,
    NULL AS destino_referencia,
    r.articulos_afectados,
    r.texto_cita,
    r.notas
FROM referencias_normativas r
JOIN normas no ON no.id = r.norma_origen_id
JOIN normas nd ON nd.id = r.norma_destino_id;
"""


def init_db(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(DDL)
    conn.commit()
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    views = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")]
    conn.close()
    print(f"Base de datos SQLite inicializada exitosamente en: {db_path}")
    print(f"Tablas ({len(tables)}): {tables}")
    print(f"Vistas ({len(views)}): {views}")


if __name__ == "__main__":
    init_db()
