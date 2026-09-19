import { query } from "../db.js";
import * as z from "zod/v4";
import {
  SearchOrdenanzasInputSchema,
  SearchByCategoryInputSchema,
  SearchByYearRangeInputSchema,
  OrdenanzaSummarySchema,
  OrdenanzaCompletaSchema,
} from "../types.js";
import { toolLogger, truncate } from "../utils.js";

// =============================================================================
// TOOL 1: search_ordenanzas
// =============================================================================

export const searchOrdenanzasTool = {
  name: "search_ordenanzas",
  title: "Buscar Ordenanzas",
  description:
    "Búsqueda full-text de ordenanzas municipales con ranking de relevancia usando PostgreSQL Full-Text Search.",
  inputSchema: SearchOrdenanzasInputSchema,
};

/**
 * Handler para búsqueda full-text de ordenanzas
 */
export async function searchOrdenanzasHandler(
  args: z.infer<typeof SearchOrdenanzasInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("search_ordenanzas");

  try {
    const results = await query(`
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        o.resumen,
        o.estado,
        ts_rank_cd(o.fts_documento, websearch_to_tsquery('espanol', $1), 32) as rank,
        ts_headline('espanol', o.texto_completo, websearch_to_tsquery('espanol', $1),
          'StartSel=<<, StopSel=>>, MaxWords=50, MinWords=20, MaxFragments=3'
        ) as headline,
        COALESCE(
          jsonb_agg(
            jsonb_build_object(
              'nombre', c.nombre,
              'slug', c.slug,
              'relevancia', oc.relevancia
            )
          ),
          '[]'::jsonb
        ) as categorias
      FROM ordenanzas o
      LEFT JOIN ordenanza_categorias oc ON o.id = oc.ordenanza_id
      LEFT JOIN categorias c ON oc.categoria_id = c.id
      WHERE o.fts_documento @@ websearch_to_tsquery('espanol', $1)
        ${args.solo_vigentes ? "AND o.estado IN ('vigente', 'modificada')" : ""}
      GROUP BY o.id, o.numero, o.anio, o.titulo, o.resumen, o.estado
      ORDER BY rank DESC
      LIMIT $2
    `, [args.query, args.limit]);

    const formatted = results.map((row: any) => ({
      id: row.id,
      numero: row.numero,
      anio: row.anio,
      titulo: row.titulo,
      resumen: row.resumen,
      estado: row.estado,
      rank: row.rank,
      headline: row.headline,
      categorias: row.categorias || [],
    }));

    log.info("Search completed", { count: formatted.length });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            results: formatted,
            total: formatted.length,
            query: args.query,
          }),
        },
      ],
    };
  } catch (error) {
    log.error(
      "Search failed",
      { error: error instanceof Error ? error.message : String(error) }
    );
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al buscar ordenanzas: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}

// =============================================================================
// TOOL 2: search_by_category
// =============================================================================

export const searchByCategoryTool = {
  name: "search_by_category",
  title: "Buscar por Categoría",
  description:
    "Filtra ordenanzas por categoría específica y opcionalmente por año.",
  inputSchema: SearchByCategoryInputSchema,
};

/**
 * Handler para búsqueda por categoría
 */
export async function searchByCategoryHandler(
  args: z.infer<typeof SearchByCategoryInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("search_by_category");

  try {
    log.info("Searching...", { slug: args.slug });

    let whereClause = "c.slug = $1";
    const params: any[] = [args.slug];

    if (args.anio) {
      whereClause += " AND o.anio = $2";
      params.push(args.anio);
    }

    params.push(args.limit);
    const results = await query(`
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        o.resumen,
        o.estado,
        COALESCE(
          jsonb_agg(
            jsonb_build_object(
              'nombre', c.nombre,
              'slug', c.slug,
              'relevancia', oc.relevancia
            )
          ),
          '[]'::jsonb
        ) as categorias
      FROM ordenanzas o
      JOIN ordenanza_categorias oc ON o.id = oc.ordenanza_id
      JOIN categorias c ON oc.categoria_id = c.id
      WHERE ${whereClause}
      GROUP BY o.id, o.numero, o.anio, o.titulo, o.resumen, o.estado
      ORDER BY o.anio DESC, o.numero DESC
      LIMIT $${params.length}
    `, params);

    const formatted = results.map((row: any) => ({
      id: row.id,
      numero: row.numero,
      anio: row.anio,
      titulo: row.titulo,
      resumen: row.resumen,
      estado: row.estado,
      categorias: row.categorias || [],
    }));

    log.info("Search completed", { count: formatted.length });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            results: formatted,
            total: formatted.length,
            category: args.slug,
            year: args.anio,
          }),
        },
      ],
    };
  } catch (error) {
    log.error(
      "Search failed",
      { error: error instanceof Error ? error.message : String(error) }
    );
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al buscar por categoría: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}

// =============================================================================
// TOOL 3: search_by_year_range
// =============================================================================

export const searchByYearRangeTool = {
  name: "search_by_year_range",
  title: "Buscar por Rango de Años",
  description:
    "Busca ordenanzas en un rango de años específico. Útil para análisis históricos.",
  inputSchema: SearchByYearRangeInputSchema,
};

/**
 * Handler para búsqueda por rango de años
 */
export async function searchByYearRangeHandler(
  args: z.infer<typeof SearchByYearRangeInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("search_by_year_range");

  try {
    log.info("Searching...", { desde: args.desde, hasta: args.hasta });

    if (args.desde > args.hasta) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: "El año 'desde' debe ser menor o igual a 'hasta'",
            }),
          },
        ],
        isError: true,
      };
    }

    const results = await query(`
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        o.resumen,
        o.estado,
        COALESCE(
          jsonb_agg(
            jsonb_build_object(
              'nombre', c.nombre,
              'slug', c.slug,
              'relevancia', oc.relevancia
            )
          ),
          '[]'::jsonb
        ) as categorias
      FROM ordenanzas o
      LEFT JOIN ordenanza_categorias oc ON o.id = oc.ordenanza_id
      LEFT JOIN categorias c ON oc.categoria_id = c.id
      WHERE o.anio BETWEEN $1 AND $2
      GROUP BY o.id, o.numero, o.anio, o.titulo, o.resumen, o.estado
      ORDER BY o.anio DESC, o.numero DESC
      LIMIT $3
    `, [args.desde, args.hasta, args.limit]);

    const formatted = results.map((row: any) => ({
      id: row.id,
      numero: row.numero,
      anio: row.anio,
      titulo: row.titulo,
      resumen: row.resumen,
      estado: row.estado,
      categorias: row.categorias || [],
    }));

    log.info("Search completed", { count: formatted.length });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            results: formatted,
            total: formatted.length,
            year_range: `${args.desde}-${args.hasta}`,
          }),
        },
      ],
    };
  } catch (error) {
    log.error(
      "Search failed",
      { error: error instanceof Error ? error.message : String(error) }
    );
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al buscar por rango: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
