#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Herramienta CLI de Consulta y Análisis de SIBOM en SQLite.

Soporta múltiples municipios con --municipio <id, slug o nombre>.

Subcomandos:
  stats [--municipio ID]                                      Estadísticas generales o por municipio
  buscar "termino" [--municipio ID] [--limit N]               Búsqueda full-text FTS5 (BM25)
  buscar-semantica "termino" [--municipio ID] [--top-k N]     Búsqueda vectorial con SentenceTransformers
  ver --tipo ordenanza --numero N --anio Y [--municipio ID]   Detalle de norma, artículos y vigencia
  arbol --tipo ordenanza --numero N --anio Y [--municipio ID] Árbol de vigencia (afecta a / afectada por)
"""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SIBOM_DIR = ROOT / "sibom"
DB_PATH = SIBOM_DIR / "sibom.db"

from scripts.sibom_municipios import resolver_municipio


def cmd_stats(conn: sqlite3.Connection, municipio_filtro=None):
    cur = conn.cursor()
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    where_sql = " WHERE codigo_localidad = ?" if mun_info else ""
    params = (mun_info["id"],) if mun_info else ()

    cur.execute(f"SELECT COUNT(*) FROM normas{where_sql}", params)
    total_normas = cur.fetchone()[0]

    cur.execute(f"SELECT tipo, COUNT(*) FROM normas{where_sql} GROUP BY tipo", params)
    by_tipo = dict(cur.fetchall())

    cur.execute(f"SELECT estado, COUNT(*) FROM normas{where_sql} GROUP BY estado", params)
    by_estado = dict(cur.fetchall())

    cur.execute(f"SELECT procesado_llm, COUNT(*) FROM normas{where_sql} GROUP BY procesado_llm", params)
    p_map = {0: "pendiente", 1: "enriquecido_glm", 2: "extractada_directa", -1: "error"}
    by_llm = {p_map.get(r[0], str(r[0])): r[1] for r in cur.fetchall()}

    cur.execute(f"""
        SELECT COUNT(*) FROM articulos a
        JOIN normas n ON n.id = a.norma_id
        {where_sql.replace('WHERE', 'WHERE n.')}
    """, params)
    total_articulos = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*) FROM referencias_normativas r
        JOIN normas n ON n.id = r.norma_origen_id
        {where_sql.replace('WHERE', 'WHERE n.')}
    """, params)
    total_referencias = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*) FROM anexos a
        JOIN normas n ON n.id = a.norma_id
        {where_sql.replace('WHERE', 'WHERE n.')}
    """, params)
    total_anexos = cur.fetchone()[0]

    print("=" * 65)
    if mun_info:
        print(f"ESTADÍSTICAS SIBOM - [{mun_info['id']}] {mun_info['nombre'].upper()}")
    else:
        print("ESTADÍSTICAS SIBOM (CONSOLIDADO MULTI-MUNICIPIO)")
    print("=" * 65)

    if not mun_info:
        cur.execute("SELECT localidad, codigo_localidad, COUNT(*) FROM normas GROUP BY localidad, codigo_localidad")
        print("Desglose por Municipio:")
        for loc, cid, count in cur.fetchall():
            print(f"  * [{cid}] {loc:<22}: {count} normas")
        print("-" * 65)

    print(f"Normas totales        : {total_normas} {by_tipo}")
    print(f"Estados de vigencia   : {by_estado}")
    print(f"Procesamiento LLM     : {by_llm}")
    print(f"Artículos registrados : {total_articulos}")
    print(f"Referencias/Derogac.  : {total_referencias}")
    print(f"Anexos registrados    : {total_anexos}")
    print(f"Ubicación de base     : {DB_PATH}")
    print("=" * 65)


def cmd_buscar(conn: sqlite3.Connection, query: str, limit: int = 10, municipio_filtro=None):
    cur = conn.cursor()
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    where_mun = " AND n.codigo_localidad = ?" if mun_info else ""
    params = [query]
    if mun_info:
        params.append(mun_info["id"])
    params.append(limit)

    sql = f"""
        SELECT n.id, n.tipo, n.numero, n.anio, n.fecha, n.titulo, n.estado,
               n.localidad, n.codigo_localidad,
               snippet(normas_fts, 1, '<<', '>>', '...', 15) AS match_summary,
               snippet(normas_fts, 2, '<<', '>>', '...', 25) AS match_texto
        FROM normas_fts f
        JOIN normas n ON n.id = f.rowid
        WHERE normas_fts MATCH ?
          {where_mun}
        ORDER BY rank
        LIMIT ?
    """
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
    except Exception:
        # Fallback si el query tiene caracteres especiales FTS5
        escaped = '"' + query.replace('"', '""') + '"'
        params[0] = escaped
        cur.execute(sql, params)
        rows = cur.fetchall()

    mun_lbl = f" en [{mun_info['nombre']}]" if mun_info else ""
    print("=" * 65)
    print(f"RESULTADOS FTS5 PARA: '{query}'{mun_lbl} ({len(rows)} encontrados)")
    print("=" * 65)
    for r in rows:
        n_id, tipo, num, anio, fecha, titulo, estado, loc, cod_loc, s_sum, s_txt = r
        lbl = f"[{loc}] [{tipo.upper()}] Nº {num}/{anio}" if num and anio else f"[{loc}] [{tipo.upper()}] {titulo}"
        print(f"\n* {lbl} (Estado: {estado}, Fecha: {fecha})")
        print(f"  Título: {titulo}")
        if s_sum:
            print(f"  Resumen: {s_sum}")
        if s_txt:
            print(f"  Coincidencia: {s_txt}")


def cmd_ver(conn: sqlite3.Connection, tipo: str, numero: int, anio: int, municipio_filtro=None):
    cur = conn.cursor()
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    where_mun = " AND codigo_localidad = ?" if mun_info else ""
    params = [tipo, numero, anio]
    if mun_info:
        params.append(mun_info["id"])

    cur.execute(f"""
        SELECT id, tipo, numero, anio, fecha, boletin, version, titulo, estado,
               notas_vigencia, summary, summary_trata, summary_resuelve, summary_depende,
               url, archivo_md, localidad, codigo_localidad
        FROM normas
        WHERE tipo = ? AND numero = ? AND anio = ?
          {where_mun}
    """, params)
    rows = cur.fetchall()

    if not rows:
        mun_txt = f" en {mun_info['nombre']}" if mun_info else ""
        print(f"No se encontró {tipo} Nº {numero}/{anio}{mun_txt}")
        return

    if len(rows) > 1:
        print(f"Existe más de una norma {tipo} Nº {numero}/{anio} en diferentes municipios:")
        for r in rows:
            print(f"  - [{r[17]}] {r[16]} (ID: {r[0]}): {r[7]}")
        print("\nPor favor, especificá el municipio con --municipio <id o slug> para ver el detalle.")
        return

    row = rows[0]
    n_id = row[0]
    print("=" * 65)
    print(f"[{row[16].upper()}] {row[1].upper()} Nº {row[2]}/{row[3]} — {row[7]}")
    print("=" * 65)
    print(f"Municipio: {row[16]} (Cód. SIBOM: {row[17]})")
    print(f"Fecha: {row[4]} | Boletín: {row[5]} | Versión: {row[6]} | Estado: {row[8]}")
    if row[9]:
        print(f"Notas de Vigencia: {row[9]}")
    print(f"URL: {row[14]}")
    print(f"Archivo: {row[15]}")

    print("\n--- RESUMEN ---")
    if row[11]:
        print(f"* Trata sobre : {row[11]}")
    if row[12]:
        print(f"* Resuelve    : {row[12]}")
    if row[13]:
        print(f"* Depende de  : {row[13]}")
    if row[10] and not (row[11] or row[12] or row[13]):
        print(row[10])

    # Artículos
    cur.execute("SELECT numero_articulo, texto, resumen, estado FROM articulos WHERE norma_id = ? ORDER BY orden", (n_id,))
    arts = cur.fetchall()
    if arts:
        print(f"\n--- ARTÍCULOS ({len(arts)}) ---")
        for a_num, a_txt, a_res, a_est in arts:
            print(f"\n[Art. {a_num}] (Estado: {a_est})")
            if a_res:
                print(f"  Resumen: {a_res}")
            print(f"  Texto: {a_txt[:200]}..." if len(a_txt) > 200 else f"  Texto: {a_txt}")

    # Árbol de vigencia
    _mostrar_arbol(cur, n_id)


def _mostrar_arbol(cur: sqlite3.Cursor, n_id: int):
    cur.execute("""
        SELECT direccion, tipo_relacion, destino_tipo, destino_numero, destino_anio,
               destino_referencia, articulos_afectados, texto_cita
        FROM v_arbol_vigencia
        WHERE norma_origen_id = ?
    """, (n_id,))
    rows = cur.fetchall()

    afecta_a = [r for r in rows if r[0] == "afecta_a"]
    afectada_por = [r for r in rows if r[0] == "afectada_por"]

    print("\n--- ÁRBOL DE VIGENCIA Y RELACIONES ---")
    if afecta_a:
        print(f"\nEsta norma AFECTA A ({len(afecta_a)} relaciones salientes):")
        for _, rel, d_tipo, d_num, d_anio, d_ref, arts, cita in afecta_a:
            dest_lbl = f"{d_tipo} Nº {d_num}/{d_anio}" if d_num and d_anio else (d_ref or d_tipo)
            arts_lbl = f" ({arts})" if arts else ""
            print(f"  -> [{rel.upper()}]{arts_lbl} {dest_lbl}")
            if cita:
                print(f"     \"{cita}\"")
    else:
        print("\nNo tiene relaciones salientes registradas.")

    if afectada_por:
        print(f"\nEsta norma es AFECTADA POR ({len(afectada_por)} relaciones entrantes):")
        for _, rel, o_tipo, o_num, o_anio, _, arts, cita in afectada_por:
            orig_lbl = f"{o_tipo} Nº {o_num}/{o_anio}"
            arts_lbl = f" ({arts})" if arts else ""
            print(f"  <- [{rel.upper()}]{arts_lbl} por {orig_lbl}")
            if cita:
                print(f"     \"{cita}\"")
    else:
        print("\nNo tiene relaciones entrantes registradas (se mantiene en su estado original).")


def cmd_arbol(conn: sqlite3.Connection, tipo: str, numero: int, anio: int, municipio_filtro=None):
    cur = conn.cursor()
    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None

    where_mun = " AND codigo_localidad = ?" if mun_info else ""
    params = [tipo, numero, anio]
    if mun_info:
        params.append(mun_info["id"])

    cur.execute(f"""
        SELECT id, localidad, codigo_localidad FROM normas
        WHERE tipo = ? AND numero = ? AND anio = ?
          {where_mun}
    """, params)
    rows = cur.fetchall()
    if not rows:
        print(f"No se encontró {tipo} Nº {numero}/{anio}")
        return

    if len(rows) > 1:
        print(f"Existe más de una norma {tipo} Nº {numero}/{anio} en diferentes municipios:")
        for r in rows:
            print(f"  - [{r[2]}] {r[1]} (ID: {r[0]})")
        print("\nPor favor, especificá el municipio con --municipio <id o slug>.")
        return

    n_id = rows[0][0]
    _mostrar_arbol(cur, n_id)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    # stats
    st = sub.add_parser("stats")
    st.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio")

    # buscar
    b = sub.add_parser("buscar")
    b.add_argument("query", type=str, help="Término o frase de búsqueda")
    b.add_argument("--municipio", type=str, default=None, help="Filtrar por municipio")
    b.add_argument("--limit", type=int, default=10, help="Cantidad máxima de resultados")

    # ver
    v = sub.add_parser("ver")
    v.add_argument("--tipo", type=str, default="ordenanza", choices=["ordenanza", "decreto"])
    v.add_argument("--numero", type=int, required=True)
    v.add_argument("--anio", type=int, required=True)
    v.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio")

    # arbol
    a = sub.add_parser("arbol")
    a.add_argument("--tipo", type=str, default="ordenanza", choices=["ordenanza", "decreto"])
    a.add_argument("--numero", type=int, required=True)
    a.add_argument("--anio", type=int, required=True)
    a.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio")

    # buscar-semantica
    bs = sub.add_parser("buscar-semantica")
    bs.add_argument("query", type=str, help="Texto o consulta conceptual")
    bs.add_argument("--municipio", type=str, default=None, help="Filtrar por municipio")
    bs.add_argument("--top-k", type=int, default=5, help="Cantidad máxima de resultados")
    bs.add_argument("--texto", action="store_true", help="Buscar en embedding de texto completo (por defecto: summary)")

    args = ap.parse_args()
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")

    if args.cmd == "stats":
        cmd_stats(conn, municipio_filtro=args.municipio)
    elif args.cmd == "buscar":
        cmd_buscar(conn, args.query, limit=args.limit, municipio_filtro=args.municipio)
    elif args.cmd == "buscar-semantica":
        from scripts.sibom_generate_embeddings import search_similar
        conn.close()
        res = search_similar(args.query, top_k=args.top_k, use_summary=not args.texto, municipio_filtro=args.municipio)
        mun_lbl = f" en [{args.municipio}]" if args.municipio else ""
        print("=" * 65)
        print(f"BÚSQUEDA SEMÁNTICA VECTORIAL PARA: '{args.query}'{mun_lbl}")
        print("=" * 65)
        for i, r in enumerate(res, 1):
            print(f"\n{i}. [{r['score']:.4f}] ({r['localidad']}) {r['tipo'].upper()} Nº {r['numero']}/{r['anio']} — {r['titulo']}")
            if r['summary']:
                print(f"   Summary: {r['summary'][:200]}...")
        return
    elif args.cmd == "ver":
        cmd_ver(conn, args.tipo, args.numero, args.anio, municipio_filtro=args.municipio)
    elif args.cmd == "arbol":
        cmd_arbol(conn, args.tipo, args.numero, args.anio, municipio_filtro=args.municipio)

    conn.close()


if __name__ == "__main__":
    main()
