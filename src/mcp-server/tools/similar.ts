import { query } from "../db.js";
import * as z from "zod/v4";
import {
  SimilarOrdenanzasInputSchema,
  SimilarOrdenanzasOutputSchema,
  OrdenanzaSimilarSchema,
  CategoriaSummarySchema,
} from "../types.js";
import {
  getOrCreateEmbedding,
  getAllEmbeddingsForSimilarity,
  calculateCosineSimilarity,
  parseEmbeddingVector,
  formatEmbeddingVector,
} from "../embeddings.js";
import { toolLogger } from "../utils.js";

// =============================================================================
// TOOL 1: similar_ordenanzas
// =============================================================================

export const similarOrdenanzasTool = {
  name: "similar_ordenanzas",
  title: "Buscar Ordenanzas Similares (Semántica)",
  description:
    "Encuentra ordenanzas semánticamente similares usando embeddings vectoriales. Genera embeddings on-the-fly usando OpenAI y los cachea para reuso. Calcula cosine similarity en memoria.",
  inputSchema: SimilarOrdenanzasInputSchema,
};

export async function similarOrdenanzasHandler(
  args: z.infer<typeof SimilarOrdenanzasInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("similar_ordenanzas");

  try {
    log.info("Finding similar ordinances...", {
      ordenanza_id: args.ordenanza_id,
      limit: args.limit,
      umbral: args.umbral,
    });

    // 1. Obtener o generar embedding de la ordenanza de referencia
    const refEmbedding = await getOrCreateEmbedding(
      args.ordenanza_id,
      "" // Pasamos vacío para que use el texto_completo de la DB
    );

    // 2. Obtener todos los embeddings de memoria
    const allEmbeddings = await getAllEmbeddingsForSimilarity();

    log.debug("Comparing embeddings...", {
      total_embeddings: allEmbeddings.length,
      ref_vector_length: refEmbedding.length,
    });

    // 3. Calcular similitud con cada embedding
    const similarities = allEmbeddings
      .filter((emb) => emb.ordenanza_id !== args.ordenanza_id)
      .map((emb) => {
        const embedding = parseEmbeddingVector(emb.vector);
        const score = calculateCosineSimilarity(refEmbedding, embedding);

        return {
          id: emb.ordenanza_id,
          numero: emb.numero,
          anio: emb.anio,
          titulo: emb.titulo,
          resumen: emb.resumen,
          score,
          categorias: emb.categorias
            ? JSON.parse(emb.categorias).map((c: any) => ({
                nombre: c.nombre,
                slug: c.slug,
                relevancia: c.relevancia,
              }))
            : [],
        };
      })
      .filter((sim) => sim.score >= args.umbral)
      .sort((a, b) => b.score - a.score)
      .slice(0, args.limit);

    log.info("Similar ordinances found", {
      count: similarities.length,
      threshold: args.umbral,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            similares: similarities,
            total: similarities.length,
            threshold: args.umbral,
          }),
        },
      ],
    };
  } catch (error) {
    log.error("Similarity search failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error al buscar similares: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
