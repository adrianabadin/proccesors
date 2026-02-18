import { query } from "../db.js";
import * as z from "zod/v4";
import {
  GetOrdenanzaInputSchema,
  GetAnexoInputSchema,
  OrdenanzaCompletaSchema,
  ArticuloSchema,
  EntidadSchema,
  ReferenciaSchema,
  MontoSchema,
  AnexoSchema,
  CategoriaSummarySchema,
} from "../types.js";
import { toolLogger, truncate } from "../utils.js";

// =============================================================================
// TOOL 1: get_ordenanza
// =============================================================================

export const getOrdenanzaTool = {
  name: "get_ordenanza",
  title: "Obtener Ordenanza Completa",
  description:
    "Obtiene todos los detalles de una ordenanza municipal incluyendo artículos, entidades, referencias, montos y anexos.",
  inputSchema: GetOrdenanzaInputSchema,
};

export async function getOrdenanzaHandler(
  args: z.infer<typeof GetOrdenanzaInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("get_ordenanza");

  try {
    log.info("Fetching ordinance details...", { id: args.id });

    const rows = await query(`
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        o.texto_completo,
        o.resumen,
        o.palabras_clave,
        o.expediente,
        o.fecha_sancion,
        o.estado,
        o.notas_vigencia,
        o.seccion_visto,
        o.seccion_considerando,
        o.monto_principal,
        o.moneda
      FROM ordenanzas o
      WHERE o.id = $1
    `, [args.id]);

    if (rows.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: `No se encontró ordenanza con id: ${args.id}`,
            }),
          },
        ],
        isError: true,
      };
    }

    const ord = rows[0];

    // Cargar artículos
    const articulos = await query(
      `
      SELECT numero_articulo, texto, resumen
      FROM articulos
      WHERE ordenanza_id = $1
      ORDER BY orden
    `,
      [args.id]
    );

    // Cargar entidades
    const entidades = await query(
      `
      SELECT e.nombre, e.tipo, oe.rol, e.cuit, oe.contexto
      FROM entidades e
      JOIN ordenanza_entidades oe ON oe.entidad_id = e.id
      WHERE oe.ordenanza_id = $1
      `,
      [args.id]
    );

    // Cargar categorías
    const categorias = await query(
      `
      SELECT c.nombre, c.slug, oc.relevancia
      FROM ordenanza_categorias oc
      JOIN categorias c ON oc.categoria_id = c.id
      WHERE oc.ordenanza_id = $1
      `,
      [args.id]
    );

    // Cargar referencias
    const referencias = await query(
      `
      SELECT 
        id, direccion, tipo,
        ordenanza_relacionada_id, numero, anio, titulo,
        norma_externa, articulos_afectados, notas
      FROM referencias_normativas
      WHERE ordenanza_origen_id = $1
      `,
      [args.id]
    );

    // Cargar montos
    const montos = await query(
      `
      SELECT concepto, valor, moneda, unidad, es_porcentaje
      FROM montos
      WHERE ordenanza_id = $1
      `,
      [args.id]
    );

    // Cargar anexos
    const anexos = await query(
      `
      SELECT numero, titulo, tipo, contenido
      FROM anexos
      WHERE ordenanza_id = $1
      ORDER BY numero
    `,
      [args.id]
    );

    const result = {
      id: ord.id,
      numero: ord.numero,
      anio: ord.anio,
      titulo: ord.titulo,
      texto_completo: ord.texto_completo,
      resumen: ord.resumen,
      palabras_clave: ord.palabras_clave || [],
      expediente: ord.expediente,
      fecha_sancion: ord.fecha_sancion,
      estado: ord.estado,
      notas_vigencia: ord.notas_vigencia,
      seccion_visto: ord.seccion_visto,
      seccion_considerando: ord.seccion_considerando,
      monto_principal: ord.monto_principal,
      moneda: ord.moneda,
      articulos: articulos.map((a) => ({
        numero: a.numero_articulo,
        texto: a.texto,
        resumen: a.resumen,
      })),
      entidades: entidades.map((e) => ({
        nombre: e.nombre,
        tipo: e.tipo,
        rol: e.rol,
        cuit: e.cuit || undefined,
        contexto: e.contexto || undefined,
      })),
      referencias: referencias.map((r) => ({
        id: r.id,
        direccion: r.direccion,
        tipo: r.tipo,
        ordenanza_relacionada_id: r.ordenanza_relacionada_id || undefined,
        numero: r.numero || undefined,
        anio: r.anio || undefined,
        titulo: r.titulo || undefined,
        norma_externa: r.norma_externa || undefined,
        articulos_afectados: r.articulos_afectados || undefined,
        notas: r.notas || undefined,
      })),
      montos: montos.map((m) => ({
        concepto: m.concepto,
        valor: Number(m.valor),
        moneda: m.moneda,
        unidad: m.unidad || undefined,
        es_porcentaje: m.es_porcentaje,
      })),
      anexos: anexos.map((a) => ({
        numero: a.numero,
        titulo: a.titulo || undefined,
        tipo: a.tipo || undefined,
        contenido: a.contenido || undefined,
      })),
      categorias: categorias.map((c) => ({
        nombre: c.nombre,
        slug: c.slug,
        relevancia: c.relevancia,
      })),
    };

    log.info("Ordinance fetched successfully", {
      id: args.id,
      articulos: result.articulos.length,
      entidades: result.entidades.length,
      referencias: result.referencias.length,
      montos: result.montos.length,
      anexos: result.anexos.length,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result),
        },
      ],
    };
  } catch (error) {
    log.error("Fetch failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al obtener ordenanza: ${
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
// TOOL 2: get_anexo
// =============================================================================

export const getAnexoTool = {
  name: "get_anexo",
  title: "Obtener Anexo de Ordenanza",
  description:
    "Obtiene el contenido completo de un anexo específico de una ordenanza.",
  inputSchema: GetAnexoInputSchema,
};

export async function getAnexoHandler(
  args: z.infer<typeof GetAnexoInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("get_anexo");

  try {
    log.info("Fetching annex...", {
      ordenanza_id: args.ordenanza_id,
      anexo_numero: args.anexo_numero,
    });

    const rows = await query(
      `
      SELECT a.numero, a.titulo, a.tipo, a.contenido, o.numero, o.anio
      FROM anexos a
      JOIN ordenanzas o ON o.id = a.ordenanza_id
      WHERE a.ordenanza_id = $1 AND a.numero = $2
      `,
      [args.ordenanza_id, args.anexo_numero]
    );

    if (rows.length === 0) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: `No se encontró anexo ${args.anexo_numero} en ordenanza ${args.ordenanza_id}`,
            }),
          },
        ],
        isError: true,
      };
    }

    const anexo = rows[0];

    log.info("Annex fetched successfully", {
      ordenanza_id: args.ordenanza_id,
      anexo_numero: args.anexo_numero,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            ordenanza_id: args.ordenanza_id,
            ordenanza_numero: anexo.numero,
            ordenanza_anio: anexo.anio,
            numero: anexo.numero,
            titulo: anexo.titulo,
            tipo: anexo.tipo,
            contenido: anexo.contenido,
          }),
        },
      ],
    };
  } catch (error) {
    log.error("Fetch failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al obtener anexo: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
