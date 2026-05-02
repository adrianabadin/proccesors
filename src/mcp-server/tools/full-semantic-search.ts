import * as z from "zod/v4";
import { SemanticSearchInputSchema } from "../types.js";
import { generateEmbeddingForModel } from "../embeddings.js";
import { searchSimilar, searchArticulosSimilar } from "../vector-store.js";
import { toolLogger } from "../utils.js";

const MODEL = "text-embedding-3-large" as const;

export const fullSemanticSearchTool = {
  name: "full_semantic_search",
  title: "Búsqueda Semántica Completa (Ordenanzas + Artículos)",
  description:
    "Busca simultáneamente en ordenanzas y artículos usando embeddings vectoriales. " +
    "Retorna resultados combinados y ordenados por score de similitud. " +
    "Ideal para encontrar toda la normativa relevante a un concepto, tanto a nivel de ordenanza como de artículo específico. " +
    "Requiere embeddings pre-generados para ambos (ordenanzas y artículos).",
  inputSchema: SemanticSearchInputSchema,
};

export async function fullSemanticSearchHandler(
  args: z.infer<typeof SemanticSearchInputSchema>,
  _ctx: any,
): Promise<any> {
  const log = toolLogger("full_semantic_search");

  try {
    log.info("Full semantic search", { query: args.query, limit: args.limit });

    // Generate query embedding once
    const queryEmbedding = await generateEmbeddingForModel(args.query, MODEL);

    // Search both in parallel
    const [ordenanzaResults, articuloResults] = await Promise.all([
      searchSimilar(queryEmbedding, args.limit * 2, args.umbral),
      searchArticulosSimilar(queryEmbedding, args.limit * 2, args.umbral),
    ]);

    // Format ordenanzas
    const ordenanzas = args.solo_vigentes
      ? ordenanzaResults.filter(r => r.estado === "vigente" || r.estado === "modificada")
      : ordenanzaResults;

    const ordenanzasOutput = ordenanzas.map(({ estado, ...rest }) => ({
      ...rest,
      tipo: "ordenanza" as const,
    }));

    // Format articulos
    const articulos = args.solo_vigentes
      ? articuloResults.filter(r => r.estado === "vigente" || r.estado === "modificada")
      : articuloResults;

    const articulosOutput = articulos.map(r => ({
      articulo_id: r.articulo_id,
      ordenanza_id: r.ordenanza_id,
      numero_articulo: r.numero_articulo,
      texto: r.texto,
      score: r.score,
      tipo: "articulo" as const,
      ordenanza: {
        numero: r.numero,
        anio: r.anio,
        titulo: r.titulo,
        estado: r.estado,
      },
    }));

    // Merge and sort by score desc
    const all = [...ordenanzasOutput, ...articulosOutput]
      .sort((a, b) => b.score - a.score)
      .slice(0, args.limit);

    const oCount = all.filter(x => x.tipo === "ordenanza").length;
    const aCount = all.filter(x => x.tipo === "articulo").length;

    log.info("Full search complete", {
      total: all.length,
      ordenanzas: oCount,
      articulos: aCount,
    });

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          resultados: all,
          total: all.length,
          ordenanzas: oCount,
          articulos: aCount,
          query: args.query,
          modelo: MODEL,
          umbral: args.umbral,
        }),
      }],
    };
  } catch (error) {
    log.error("Full search failed", {
      error: error instanceof Error ? error.message : String(error),
    });
    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          error: `Error en búsqueda completa: ${error instanceof Error ? error.message : String(error)}`,
        }),
      }],
      isError: true,
    };
  }
}
