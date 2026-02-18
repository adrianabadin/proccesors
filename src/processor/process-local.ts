/**
 * Procesador local de ordenanzas (sin API externa).
 * 
 * Combina:
 * 1. Extracción estructural (Regex)
 * 2. Clasificación semántica (IA local con Xenova/Transformers)
 * 3. Persistencia en DB (misma lógica que index.ts)
 * 
 * Uso:
 *   BATCH_SIZE=5 npx tsx src/processor/process-local.ts      # test con 5
 *   npx tsx src/processor/process-local.ts                    # default 50
 *   npx tsx src/processor/process-local.ts --all              # todas
 */

import { eq, and, sql } from "drizzle-orm";
import { db, pool } from "../db/index.js";
import {
  ordenanzas,
  articulos,
  ordenanzaCategorias,
  categorias,
  referenciasNormativas,
  montos,
} from "../db/schema.js";
import { extractStructure, type ExtractedStructure } from "./local-extractor.js";
import { processWithAI, type ClassificationResult } from "./local-classifier.js";

// ─── Config ───────────────────────────────────────────────────

const BATCH_SIZE = parseInt(process.env.BATCH_SIZE ?? "50", 10);
const PROCESS_ALL = process.argv.includes("--all");
const PROMPT_VERSION = "local-v1";

// ─── Types ────────────────────────────────────────────────────

interface OrdenanzaRow {
  id: string;
  numero: number;
  anio: number;
  titulo: string;
  textoCompleto: string;
}

interface CategoryLookup {
  [slug: string]: number;
}

// ─── Helpers ──────────────────────────────────────────────────

/**
 * Precarga todas las categorías para lookup rápido slug -> id.
 */
async function loadCategoryLookup(): Promise<CategoryLookup> {
  const rows = await db
    .select({ id: categorias.id, slug: categorias.slug })
    .from(categorias);

  const lookup: CategoryLookup = {};
  for (const row of rows) {
    lookup[row.slug] = row.id;
  }
  return lookup;
}

/**
 * Resuelve una referencia a ordenanza local (numero+anio) a su UUID.
 */
async function resolveOrdenanzaId(
  tx: Parameters<Parameters<typeof db.transaction>[0]>[0],
  numero: number,
  anio: number,
): Promise<string | null> {
  const rows = await tx
    .select({ id: ordenanzas.id })
    .from(ordenanzas)
    .where(and(eq(ordenanzas.numero, numero), eq(ordenanzas.anio, anio)))
    .limit(1);

  return rows.length > 0 ? rows[0].id : null;
}

/**
 * Persiste el resultado combinado en la DB.
 */
async function persistExtraction(
  ordenanzaId: string,
  structural: ExtractedStructure,
  aiResult: ClassificationResult,
  categoryLookup: CategoryLookup,
): Promise<void> {
  await db.transaction(async (tx) => {
    // 1. UPDATE ordenanza principal
    await tx
      .update(ordenanzas)
      .set({
        resumen: aiResult.resumen,
        palabrasClave: aiResult.palabras_clave,
        expediente: structural.expediente,
        fechaSancion: structural.fecha_sancion,
        estado: aiResult.estado,
        seccionVisto: structural.seccion_visto,
        seccionConsiderando: structural.seccion_considerando,
        procesadoIa: true,
        fechaProcesadoIa: new Date(),
        versionPrompt: PROMPT_VERSION,
      })
      .where(eq(ordenanzas.id, ordenanzaId));

    // 2. INSERT artículos
    if (structural.articulos.length > 0) {
      await tx.insert(articulos).values(
        structural.articulos.map((art, idx) => ({
          ordenanzaId,
          numeroArticulo: art.numero,
          orden: idx + 1,
          texto: art.texto,
          resumen: art.texto.slice(0, 200) + "...", // Resumen simple por truncado
        })),
      );
    }

    // 3. INSERT ordenanza_categorias
    const catValues = aiResult.categorias
      .filter((cat) => categoryLookup[cat.slug] !== undefined)
      .map((cat) => ({
        ordenanzaId,
        categoriaId: categoryLookup[cat.slug],
        relevancia: cat.relevancia,
      }));

    if (catValues.length > 0) {
      await tx.insert(ordenanzaCategorias).values(catValues);
    }

    // 4. INSERT referencias_normativas
    for (const ref of structural.referencias) {
      let ordenanzaDestinoId: string | null = null;

      // Si referencia una ordenanza local, intentar resolver su UUID
      if (ref.destino_numero && ref.destino_anio) {
        ordenanzaDestinoId = await resolveOrdenanzaId(
          tx,
          ref.destino_numero,
          ref.destino_anio,
        );
      }

      await tx.insert(referenciasNormativas).values({
        ordenanzaOrigenId: ordenanzaId,
        ordenanzaDestinoId,
        tipo: ref.tipo as any, // casting porque regex devuelve strings
        normaExternaTipo: ref.norma_externa_tipo,
        normaExternaReferencia: ref.norma_externa_referencia,
        articulosAfectados: null,
        notas: null,
      });
    }

    // 5. INSERT montos
    if (structural.montos_detallados.length > 0) {
      await tx.insert(montos).values(
        structural.montos_detallados.map((m) => ({
          ordenanzaId,
          concepto: m.concepto,
          valor: m.valor.toString(),
          moneda: m.moneda,
          unidad: null,
          esPorcentaje: m.es_porcentaje,
        })),
      );
    }
  });
}

// ─── Main ─────────────────────────────────────────────────────

async function main() {
  console.log("=== Procesador Local de Ordenanzas (Sin API) ===\n");
  console.log(`Batch size: ${PROCESS_ALL ? "TODAS" : BATCH_SIZE}`);
  console.log(`Prompt version: ${PROMPT_VERSION}\n`);

  // Precargar lookup de categorías
  const categoryLookup = await loadCategoryLookup();
  const numCategories = Object.keys(categoryLookup).length;
  console.log(`Categorías cargadas: ${numCategories}\n`);

  if (numCategories === 0) {
    console.error(
      "No hay categorías en la DB. Ejecutá `npx tsx src/db/setup.ts` primero.",
    );
    process.exit(1);
  }

  // Query ordenanzas sin procesar
  const limit = PROCESS_ALL ? 10000 : BATCH_SIZE;
  const pendientes: OrdenanzaRow[] = await db
    .select({
      id: ordenanzas.id,
      numero: ordenanzas.numero,
      anio: ordenanzas.anio,
      titulo: ordenanzas.titulo,
      textoCompleto: ordenanzas.textoCompleto,
    })
    .from(ordenanzas)
    .where(eq(ordenanzas.procesadoIa, false))
    .orderBy(ordenanzas.anio, ordenanzas.numero)
    .limit(limit);

  console.log(`Ordenanzas pendientes: ${pendientes.length}\n`);

  if (pendientes.length === 0) {
    console.log("No hay ordenanzas pendientes de procesar.");
    await pool.end();
    return;
  }

  // Procesar una por una
  let procesadas = 0;
  let errores = 0;
  const startTime = Date.now();

  for (const ord of pendientes) {
    const label = `Ordenanza N° ${ord.numero}/${ord.anio}`;
    try {
      process.stdout.write(
        `[${procesadas + 1}/${pendientes.length}] ${label}...\n`,
      );

      // 1. Extracción estructural (Regex)
      const structural = extractStructure(ord.textoCompleto);
      console.log(`  📋 Estructura: ${structural.articulos.length} arts, ${structural.referencias.length} refs`);

      // 2. Procesamiento con IA local
      const aiResult = await processWithAI(ord.textoCompleto, structural.referencias);
      console.log(`  📊 Categorías: ${aiResult.categorias.map((c) => c.slug).join(", ")}`);

      // 3. Persistir en DB
      await persistExtraction(ord.id, structural, aiResult, categoryLookup);

      console.log(`  ✅ Completado\n`);
      procesadas++;
    } catch (error) {
      errores++;
      const msg = error instanceof Error ? error.message : String(error);
      console.log(`  ❌ ERROR: ${msg.slice(0, 150)}\n`);
    }
  }

  // Resumen
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log("\n=== Procesamiento completado ===");
  console.log(`Procesadas: ${procesadas}`);
  console.log(`Errores: ${errores}`);
  console.log(`Tiempo: ${elapsed}s`);
  console.log(
    `Velocidad: ${(procesadas / (parseFloat(elapsed) / 60)).toFixed(1)} ord/min`,
  );

  await pool.end();
}

// Ejecutar
main().catch((error) => {
  console.error("\nError fatal:", error);
  process.exit(1);
});
