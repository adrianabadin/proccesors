#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generador de embeddings duales (summary y texto completo) para normas en SIBOM.

Utiliza sentence-transformers con modelo multilingüe ('paraphrase-multilingual-MiniLM-L12-v2'
o 'all-MiniLM-L6-v2' como alternativa rápida).
Almacena los vectores como BLOB float32 para búsquedas vectoriales ultrarrápidas con NumPy.
Soporta filtrado y generación selectiva por municipio (--municipio 130, 108, etc.).
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SIBOM_DIR = ROOT / "sibom"
DB_PATH = SIBOM_DIR / "sibom.db"

from scripts.sibom_municipios import resolver_municipio

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def get_model(model_name: str = DEFAULT_MODEL):
    """Carga el modelo SentenceTransformer priorizando cache local."""
    from sentence_transformers import SentenceTransformer
    import time
    
    # 1. Intentar cargar directamente del cache local sin conexión a red
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        pass

    # 2. Si no está en cache local, descargar con reintentos
    for intento in range(1, 4):
        try:
            print(f"Cargando modelo de embeddings: {model_name} (intento {intento}/3)...")
            return SentenceTransformer(model_name)
        except Exception as exc:
            if intento < 3:
                time.sleep(3)
            else:
                raise RuntimeError(f"Error fatal cargando modelo {model_name}: {exc}") from exc


def cmd_status(municipio_filtro=None):
    """Muestra el estado de cobertura de embeddings en la base."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None
    where_sql = " WHERE codigo_localidad = ?" if mun_info else ""
    params = (mun_info["id"],) if mun_info else ()

    print("=" * 65)
    if mun_info:
        print(f"ESTADO DE EMBEDDINGS - [{mun_info['id']}] {mun_info['nombre'].upper()}")
    else:
        print("ESTADO DE EMBEDDINGS EN SIBOM.DB (CONSOLIDADO)")
    print("=" * 65)

    cur.execute(f"SELECT COUNT(*) FROM normas{where_sql}", params)
    total = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM normas WHERE summary IS NOT NULL{where_sql.replace('WHERE', 'AND')}", params)
    con_summary = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM normas WHERE embedding_summary IS NOT NULL{where_sql.replace('WHERE', 'AND')}", params)
    emb_summary = cur.fetchone()[0]

    cur.execute(f"SELECT COUNT(*) FROM normas WHERE embedding_texto IS NOT NULL{where_sql.replace('WHERE', 'AND')}", params)
    emb_texto = cur.fetchone()[0]

    if not mun_info:
        cur.execute("""
            SELECT codigo_localidad, localidad,
                   COUNT(*) as total,
                   SUM(CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END) as con_sum,
                   SUM(CASE WHEN embedding_summary IS NOT NULL THEN 1 ELSE 0 END) as emb_sum,
                   SUM(CASE WHEN embedding_texto IS NOT NULL THEN 1 ELSE 0 END) as emb_txt
            FROM normas
            GROUP BY codigo_localidad, localidad
        """)
        print("Desglose por Municipio:")
        for cid, loc, tot, c_sum, e_sum, e_txt in cur.fetchall():
            pct_sum = (e_sum / max(1, c_sum)) * 100
            pct_txt = (e_txt / max(1, tot)) * 100
            print(f"  * [{cid}] {loc:<22}: {tot} normas | Emb Summary: {e_sum}/{c_sum} ({pct_sum:.1f}%) | Emb Texto: {e_txt}/{tot} ({pct_txt:.1f}%)")
        print("-" * 65)

    conn.close()

    print(f"Total normas en ámbito:       {total}")
    print(f"Normas con summary:           {con_summary}")
    print(f"Embeddings de summary:        {emb_summary} ({emb_summary / max(1, con_summary) * 100:.1f}%)")
    print(f"Embeddings de texto completo: {emb_texto} ({emb_texto / max(1, total) * 100:.1f}%)")
    print("=" * 65)


def generate_embeddings(
    target: str = "all",
    batch_size: int = 64,
    limit: int | None = None,
    tipo: str | None = None,
    municipio_filtro=None,
    model_name: str = DEFAULT_MODEL,
):
    """Genera embeddings por lotes y los guarda en sibom.db."""
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None
    mun_lbl = f"[{mun_info['id']}] {mun_info['nombre']}" if mun_info else "TODOS"

    model = get_model(model_name)

    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    cur = conn.cursor()

    # 1. Procesar summary
    if target in ("all", "summary"):
        q = """
            SELECT id, summary FROM normas
            WHERE summary IS NOT NULL AND embedding_summary IS NULL
        """
        params = []
        if mun_info:
            q += " AND codigo_localidad = ?"
            params.append(mun_info["id"])
        if tipo:
            q += " AND tipo = ?"
            params.append(tipo)
        q += " ORDER BY id ASC"
        if limit:
            q += f" LIMIT {limit}"

        cur.execute(q, params)
        rows = cur.fetchall()
        total_sum = len(rows)
        print(f"\nGenerando embeddings para {total_sum} summaries ({mun_lbl}, tipo={tipo or 'todos'})...")

        for i in range(0, total_sum, batch_size):
            batch = rows[i : i + batch_size]
            ids = [r[0] for r in batch]
            texts = [r[1].strip() for r in batch]

            embs = model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)

            updates = []
            for id_, vec in zip(ids, embs):
                blob = np.array(vec, dtype=np.float32).tobytes()
                updates.append((blob, id_))

            cur.executemany("UPDATE normas SET embedding_summary = ? WHERE id = ?", updates)
            conn.commit()
            print(f"  [Summary {min(i + batch_size, total_sum)}/{total_sum}] procesados")

    # 2. Procesar texto_completo (primeros 2.500 caracteres representativos)
    if target in ("all", "texto"):
        q = """
            SELECT id, texto_completo FROM normas
            WHERE texto_completo IS NOT NULL AND embedding_texto IS NULL
        """
        params = []
        if mun_info:
            q += " AND codigo_localidad = ?"
            params.append(mun_info["id"])
        if tipo:
            q += " AND tipo = ?"
            params.append(tipo)
        q += " ORDER BY id ASC"
        if limit:
            q += f" LIMIT {limit}"

        cur.execute(q, params)
        rows = cur.fetchall()
        total_txt = len(rows)
        print(f"\nGenerando embeddings para {total_txt} textos completos ({mun_lbl}, tipo={tipo or 'todos'})...")

        for i in range(0, total_txt, batch_size):
            batch = rows[i : i + batch_size]
            ids = [r[0] for r in batch]
            texts = [r[1][:2500].strip() for r in batch]

            embs = model.encode(texts, batch_size=batch_size, show_progress_bar=False, normalize_embeddings=True)

            updates = []
            for id_, vec in zip(ids, embs):
                blob = np.array(vec, dtype=np.float32).tobytes()
                updates.append((blob, id_))

            cur.executemany("UPDATE normas SET embedding_texto = ? WHERE id = ?", updates)
            conn.commit()
            print(f"  [Texto {min(i + batch_size, total_txt)}/{total_txt}] procesados")

    conn.close()
    print("\nProceso de vectorización finalizado.")


def search_similar(query: str, top_k: int = 5, use_summary: bool = True, municipio_filtro=None, model_name: str = DEFAULT_MODEL):
    """Busca normas semánticamente similares por similitud coseno."""
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    model = get_model(model_name)
    q_vec = model.encode(query, normalize_embeddings=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    col = "embedding_summary" if use_summary else "embedding_texto"
    q = f"SELECT id, tipo, numero, anio, titulo, summary, localidad, codigo_localidad, {col} FROM normas WHERE {col} IS NOT NULL"
    params = []
    if mun_info:
        q += " AND codigo_localidad = ?"
        params.append(mun_info["id"])

    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No hay embeddings calculados aún para el criterio seleccionado.")
        return []

    matrix = np.array([np.frombuffer(r[8], dtype=np.float32) for r in rows])
    sims = np.dot(matrix, q_vec)

    top_indices = np.argsort(sims)[::-1][:top_k]

    results = []
    for idx in top_indices:
        r = rows[idx]
        score = float(sims[idx])
        results.append({
            "id": r[0],
            "tipo": r[1],
            "numero": r[2],
            "anio": r[3],
            "titulo": r[4],
            "summary": r[5],
            "localidad": r[6],
            "codigo_localidad": r[7],
            "score": score
        })

    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--status", action="store_true", help="Muestra estado de embeddings")
    ap.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio (ej: 130, 108)")
    ap.add_argument("--target", choices=["all", "summary", "texto"], default="all", help="Qué campo vectorizar")
    ap.add_argument("--batch-size", type=int, default=64, help="Tamaño de lote")
    ap.add_argument("--limit", type=int, default=None, help="Límite de registros a procesar")
    ap.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Modelo SentenceTransformer")
    ap.add_argument("--tipo", type=str, default=None, help="Filtrar por tipo (ordenanza o decreto)")
    ap.add_argument("--buscar", type=str, default=None, help="Consulta de búsqueda semántica")
    ap.add_argument("--top-k", type=int, default=5, help="Cantidad de resultados para búsqueda")
    args = ap.parse_args()

    if args.status:
        cmd_status(municipio_filtro=args.municipio)
        return

    if args.buscar:
        res = search_similar(args.buscar, top_k=args.top_k, use_summary=(args.target != "texto"), municipio_filtro=args.municipio, model_name=args.model)
        mun_lbl = f" en [{args.municipio}]" if args.municipio else ""
        print(f"\nResultados más similares a: '{args.buscar}'{mun_lbl}\n")
        for i, r in enumerate(res, 1):
            print(f"{i}. [{r['score']:.4f}] ({r['localidad']}) {r['tipo'].capitalize()} Nº {r['numero']}/{r['anio']} - {r['titulo']}")
            if r['summary']:
                print(f"   Summary: {r['summary'][:160]}...")
        return

    generate_embeddings(
        target=args.target,
        batch_size=args.batch_size,
        limit=args.limit,
        tipo=args.tipo,
        municipio_filtro=args.municipio,
        model_name=args.model,
    )


if __name__ == "__main__":
    main()
