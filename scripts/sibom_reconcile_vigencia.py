#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor de Reconciliación de Vigencia y Derogaciones en Cascada para SIBOM.

1. Cruza las referencias normativas con las normas locales de la base de datos (poblando norma_destino_id).
2. Aplica el impacto en cascada sobre los estados de vigencia:
   - 'deroga_total' -> normas.estado = 'derogada_total' y articulos.estado = 'derogado'
   - 'deroga_parcial' -> normas.estado = 'derogada_parcial' y articulos específicos = 'derogado'
   - 'modifica'/'sustituye' -> normas.estado = 'modificada' y articulos específicos = 'modificado'
3. Genera reporte CSV en sibom/_estado/arbol-vigencia-resumen.csv.
"""

import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sibom_municipios import resolver_municipio, DB_PATH, STATE_DIR
REPORT_CSV = STATE_DIR / "arbol-vigencia-resumen.csv"


def parse_articulos_afectados(texto_articulos: str | None) -> list[str]:
    """Extrae números de artículos de strings como 'Arts. 1, 3 y 5', 'artículo 2', etc."""
    if not texto_articulos:
        return []
    matches = re.findall(r"\b(\d+(?:\s*bis)?)\b", texto_articulos, re.IGNORECASE)
    return [m.strip().lower() for m in matches]


def safe_exec(cur, conn, sql, params=()):
    """Ejecuta una consulta SQL con reintentos progresivos en caso de contención de lock."""
    import time
    for attempt in range(1, 25):
        try:
            return cur.execute(sql, params)
        except sqlite3.OperationalError as exc:
            if ("locked" in str(exc).lower() or "busy" in str(exc).lower()) and attempt < 25:
                time.sleep(0.5 * attempt)
            else:
                raise


def reconcile_vigencia(db_path: Path = DB_PATH, municipio_filtro=None):
    conn = sqlite3.connect(db_path, timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    cur = conn.cursor()

    mun_info = resolver_municipio(municipio_filtro) if municipio_filtro else None
    mun_lbl = f"[{mun_info['id']}] {mun_info['nombre']}" if mun_info else "TODOS LOS MUNICIPIOS"
    print(f"Iniciando cruce y reconciliación de vigencia para {mun_lbl}...")

    # 1. Cruzar referencias con normas locales (respetando codigo_localidad)
    where_c = " AND no.codigo_localidad = ?" if mun_info else ""
    params_c = (mun_info["id"],) if mun_info else ()

    safe_exec(cur, conn, f"""
        SELECT r.id, r.destino_tipo, r.destino_numero, r.destino_anio, no.codigo_localidad
        FROM referencias_normativas r
        JOIN normas no ON no.id = r.norma_origen_id
        WHERE r.norma_destino_id IS NULL
          AND r.destino_numero IS NOT NULL
          AND r.destino_anio IS NOT NULL
          {where_c}
    """, params_c)
    pendientes_cruce = cur.fetchall()
    print(f"Referencias pendientes de vincular a norma_destino_id: {len(pendientes_cruce)}")

    vinculadas = 0
    for idx, (ref_id, dest_tipo, dest_num, dest_anio, cod_loc) in enumerate(pendientes_cruce, 1):
        # Buscar en normas locales del mismo municipio
        safe_exec(cur, conn, """
            SELECT id FROM normas
            WHERE tipo = ? AND numero = ? AND anio = ? AND codigo_localidad = ?
            LIMIT 1
        """, (dest_tipo, dest_num, dest_anio, cod_loc))
        dest_row = cur.fetchone()
        if dest_row:
            dest_id = dest_row[0]
            safe_exec(cur, conn, "UPDATE referencias_normativas SET norma_destino_id = ? WHERE id = ?", (dest_id, ref_id))
            vinculadas += 1
        if idx % 50 == 0:
            conn.commit()

    conn.commit()
    print(f"Referencias vinculadas a normas locales en base: {vinculadas}")

    # 2. Aplicar impacto de vigencia en cascada
    where_i = " AND no.codigo_localidad = ?" if mun_info else ""
    params_i = (mun_info["id"],) if mun_info else ()

    cur.execute(f"""
        SELECT r.id, r.norma_origen_id, r.norma_destino_id, r.tipo_relacion,
               r.articulos_afectados, r.texto_cita,
               no.tipo, no.numero, no.anio
        FROM referencias_normativas r
        JOIN normas no ON no.id = r.norma_origen_id
        WHERE r.norma_destino_id IS NOT NULL
          AND r.tipo_relacion IN ('deroga_total', 'deroga_parcial', 'modifica', 'sustituye')
          {where_i}
    """, params_i)
    relaciones_impacto = cur.fetchall()
    print(f"Relaciones con impacto de vigencia: {len(relaciones_impacto)}")

    report_rows = []

    for idx, (r_id, orig_id, dest_id, tipo_rel, arts_afectados, texto_cita, o_tipo, o_num, o_anio) in enumerate(relaciones_impacto, 1):
        origen_label = f"{o_tipo.capitalize()} Nº {o_num}/{o_anio}"

        # Consultar norma destino
        safe_exec(cur, conn, "SELECT tipo, numero, anio, estado, notas_vigencia FROM normas WHERE id = ?", (dest_id,))
        dest_row = cur.fetchone()
        if not dest_row:
            continue
        d_tipo, d_num, d_anio, d_estado_prev, d_notas_prev = dest_row
        destino_label = f"{d_tipo.capitalize()} Nº {d_num}/{d_anio}"
        ya_notificada = bool(d_notas_prev and origen_label in d_notas_prev)

        if tipo_rel == "deroga_total":
            nota = f"Derogada totalmente por {origen_label}"
            if not ya_notificada:
                safe_exec(cur, conn, """
                    UPDATE normas
                    SET estado = 'derogada_total',
                        notas_vigencia = COALESCE(notas_vigencia || ' | ', '') || ?
                    WHERE id = ?
                """, (nota, dest_id))
            else:
                safe_exec(cur, conn, "UPDATE normas SET estado = 'derogada_total' WHERE id = ?", (dest_id,))

            # Todos los artículos a derogado
            safe_exec(cur, conn, """
                UPDATE articulos
                SET estado = 'derogado',
                    modificado_por_norma_id = ?
                WHERE norma_id = ?
            """, (orig_id, dest_id))

            report_rows.append({
                "norma_destino": destino_label,
                "estado_anterior": d_estado_prev,
                "nuevo_estado": "derogada_total",
                "tipo_impacto": "deroga_total",
                "norma_origen": origen_label,
                "articulos": "todos",
                "cita": texto_cita
            })

        elif tipo_rel == "deroga_parcial":
            nota = f"Derogada parcialmente por {origen_label}"
            # Solo actualizar a derogada_parcial si no está ya derogada_total
            if d_estado_prev != "derogada_total":
                if not ya_notificada:
                    safe_exec(cur, conn, """
                        UPDATE normas
                        SET estado = 'derogada_parcial',
                            notas_vigencia = COALESCE(notas_vigencia || ' | ', '') || ?
                        WHERE id = ?
                    """, (nota, dest_id))
                else:
                    safe_exec(cur, conn, "UPDATE normas SET estado = 'derogada_parcial' WHERE id = ?", (dest_id,))

            # Artículos específicos a derogado
            nums_arts = parse_articulos_afectados(arts_afectados)
            for na in nums_arts:
                safe_exec(cur, conn, """
                    UPDATE articulos
                    SET estado = 'derogado',
                        modificado_por_norma_id = ?
                    WHERE norma_id = ? AND numero_articulo = ?
                """, (orig_id, dest_id, na))

            report_rows.append({
                "norma_destino": destino_label,
                "estado_anterior": d_estado_prev,
                "nuevo_estado": "derogada_parcial",
                "tipo_impacto": "deroga_parcial",
                "norma_origen": origen_label,
                "articulos": arts_afectados or "parcial",
                "cita": texto_cita
            })

        elif tipo_rel in ("modifica", "sustituye"):
            nota = f"Modificada por {origen_label}"
            if d_estado_prev not in ("derogada_total", "derogada_parcial"):
                if not ya_notificada:
                    safe_exec(cur, conn, """
                        UPDATE normas
                        SET estado = 'modificada',
                            notas_vigencia = COALESCE(notas_vigencia || ' | ', '') || ?
                        WHERE id = ?
                    """, (nota, dest_id))
                else:
                    safe_exec(cur, conn, "UPDATE normas SET estado = 'modificada' WHERE id = ?", (dest_id,))

            # Artículos específicos a modificado
            nums_arts = parse_articulos_afectados(arts_afectados)
            for na in nums_arts:
                safe_exec(cur, conn, """
                    UPDATE articulos
                    SET estado = 'modificado',
                        modificado_por_norma_id = ?
                    WHERE norma_id = ? AND numero_articulo = ?
                """, (orig_id, dest_id, na))

            report_rows.append({
                "norma_destino": destino_label,
                "estado_anterior": d_estado_prev,
                "nuevo_estado": "modificada",
                "tipo_impacto": tipo_rel,
                "norma_origen": origen_label,
                "articulos": arts_afectados or "parcial",
                "cita": texto_cita
            })

        if idx % 50 == 0:
            conn.commit()

    conn.commit()

    # Guardar reporte en CSV
    if report_rows:
        REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "norma_destino", "estado_anterior", "nuevo_estado",
                "tipo_impacto", "norma_origen", "articulos", "cita"
            ])
            writer.writeheader()
            writer.writerows(report_rows)
        print(f"Reporte de vigencia generado en: {REPORT_CSV}")

    # Resumen de estados finales
    cur.execute("SELECT estado, COUNT(*) FROM normas GROUP BY estado")
    estados_normas = dict(cur.fetchall())
    cur.execute("SELECT estado, COUNT(*) FROM articulos GROUP BY estado")
    estados_articulos = dict(cur.fetchall())

    conn.close()

    print("\n" + "=" * 50)
    print("RECONCILIACIÓN DE VIGENCIA COMPLETADA")
    print("=" * 50)
    print(f"Distribución de estados en normas: {estados_normas}")
    print(f"Distribución de estados en artículos: {estados_articulos}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--municipio", type=str, default=None, help="ID, slug o nombre del municipio (ej: 130, 108, veinticinco-de-mayo)")
    args = ap.parse_args()
    reconcile_vigencia(municipio_filtro=args.municipio)


if __name__ == "__main__":
    main()
