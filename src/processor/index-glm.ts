/**
 * Procesador de ordenanzas con GLM 4.7 Flash (Zhipu AI).
 * 
 * Usa la API OpenAI-compatible de Zhipu AI.
 * Base URL: https://open.bigmodel.cn/api/paas/v4/
 */

import OpenAI, { APIError } from "openai";
import "dotenv/config";
import { eq, and, sql } from "drizzle-orm";
import { db, pool } from "../db/index.js";
import {
  ordenanzas,
  articulos,
  entidades,
  ordenanzaEntidades,
  ordenanzaCategorias,
  categorias,
  referenciasNormativas,
  montos,
  anexos,
} from "../db/schema.js";
import { SYSTEM_PROMPT, PROMPT_VERSION, buildUserPrompt } from "./prompts.js";
import { parseExtractionResponse, type ExtractionResult } from "./parser.js";

// ─── Config ───────────────────────────────────────────────────

const BATCH_SIZE = parseInt(process.env.BATCH_SIZE ?? "50", 10);
const RATE_LIMIT_MS = parseInt(process.env.RATE_LIMIT_MS ?? "1000", 10);
const MODEL = process.env.MODEL ?? "glm-4.7-flash";
const PROCESS_ALL = process.argv.includes("--all");

// ─── GLM Client (OpenAI-compatible) ────────────────────────────

const client = new OpenAI({
  apiKey: process.env.GLM_API_KEY,
  baseURL: "https://open.bigmodel.cn/api/paas/v4/",
});

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

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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
 * Llama a GLM API para analizar una ordenanza.
 */
async function callGLMAPI(
  numero: number,
  anio: number,
  textoCompleto: string,
): Promise<ExtractionResult> {
  const userPrompt = buildUserPrompt(numero, anio, textoCompleto);

  const response = await client.chat.completions.create({
    model: MODEL,
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: userPrompt },
    ],
    temperature: 0.2,
    max_tokens: 8192,
  });

  const text = response.choices[0]?.message?.content;
  if (!text) {
    throw new Error("GLM no devolvió texto en la respuesta");
  }

  return parseExtractionResponse(text);
}

/**
 * Busca o crea una entidad y devuelve su ID.
 */
async function upsertEntidad(
  tx: Parameters<Parameters<typeof db.transaction>[0]>[0],
  entidad: ExtractionResult["entidades"][0],
): Promise<number> {
  const existing = await tx
    .select({ id: entidades.id })
    .from(entidades)
    .where(
      and(
        eq(entidades.nombre, entidad.nombre),
        eq(entidades.tipo, entidad.tipo),
      ),
    )
    .limit(1);

  if (existing.length > 0) {
    if (entidad.cuit && existing[0].id) {
      await tx
        .update(entidades)
        .set({ cuit: entidad.cuit })
        .where(
          and(
            eq(entidades.id, existing[0].id),
            sql`${entidades.cuit} IS NULL`,
          ),
        );
    }
    return existing[0].id;
  }

  const [inserted] = await tx
    .insert(entidades)
    .values({
      nombre: entidad.nombre,
      tipo: entidad.tipo,
      cuit: entidad.cuit,
    })
    .returning({ id: entidades.id });

  return inserted.id;
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
 * Persiste todo el resultado de extracción en la DB dentro de una transacción.
 */
async function persistExtraction(
  ordenanzaId: string,
  extraction: ExtractionResult,
  categoryLookup: CategoryLookup,
): Promise<void> {
  await db.transaction(async (tx) => {
    // 1. UPDATE ordenanza principal
    await tx
      .update(ordenanzas)
      .set({
        resumen: extraction.resumen,
        palabrasClave: extraction.palabras_clave,
        expediente: extraction.expediente,
        fechaSancion: extraction.fecha_sancion,
        estado: extraction.estado,
        notasVigencia: extraction.notas_vigencia,
        montoPrincipal: extraction.monto_principal?.toString() ?? null,
        moneda: extraction.moneda,
        seccionVisto: extraction.seccion_visto,
        seccionConsiderando: extraction.seccion_considerando,
        procesadoIa: true,
        fechaProcesadoIa: new Date(),
        versionPrompt: PROMPT_VERSION,
      })
      .where(eq(ordenanzas.id, ordenanzaId));

    // 2. INSERT artículos
    // Deduplicar por numero_articulo: ON CONFLICT DO NOTHING solo protege contra
    // filas existentes en la tabla, no contra duplicados dentro del mismo batch.
    const seenNums = new Set<string>();
    const articulosUnicos = extraction.articulos.filter((art) => {
      if (seenNums.has(art.numero)) return false;
      seenNums.add(art.numero);
      return true;
    });
    if (articulosUnicos.length > 0) {
      await tx
        .insert(articulos)
        .values(
          articulosUnicos.map((art, idx) => ({
            ordenanzaId,
            numeroArticulo: art.numero,
            orden: idx + 1,
            texto: art.texto,
            resumen: art.resumen,
          })),
        )
        .onConflictDoNothing();
    }

    // 3. UPSERT entidades + INSERT ordenanza_entidades
    for (const ent of extraction.entidades) {
      const entidadId = await upsertEntidad(tx, ent);

      await tx
        .insert(ordenanzaEntidades)
        .values({
          ordenanzaId,
          entidadId,
          rol: ent.rol,
          contexto: ent.contexto,
        })
        .onConflictDoNothing();
    }

    // 4. INSERT ordenanza_categorias
    const catValues = extraction.categorias
      .filter((cat) => categoryLookup[cat.slug] !== undefined)
      .map((cat) => ({
        ordenanzaId,
        categoriaId: categoryLookup[cat.slug],
        relevancia: cat.relevancia,
      }));

    if (catValues.length > 0) {
      await tx.insert(ordenanzaCategorias).values(catValues);
    }

    // 5. INSERT referencias_normativas (skip si viola ck_destino_presente)
    for (const ref of extraction.referencias) {
      let ordenanzaDestinoId: string | null = null;

      if (ref.destino_numero && ref.destino_anio) {
        ordenanzaDestinoId = await resolveOrdenanzaId(
          tx,
          ref.destino_numero,
          ref.destino_anio,
        );
      }

      // Skip si no hay destino válido NI referencia externa (viola constraint)
      if (!ordenanzaDestinoId && !ref.norma_externa_referencia) {
        continue;
      }

      await tx.insert(referenciasNormativas).values({
        ordenanzaOrigenId: ordenanzaId,
        ordenanzaDestinoId,
        tipo: ref.tipo,
        normaExternaTipo: ref.norma_externa_tipo,
        normaExternaReferencia: ref.norma_externa_referencia,
        normaExternaDescripcion: ref.norma_externa_descripcion,
        articulosAfectados: ref.articulos_afectados,
        notas: ref.notas,
      });
    }

    // 6. INSERT montos
    if (extraction.montos_detallados.length > 0) {
      const montosValues = extraction.montos_detallados
        .filter((m) => m.valor !== null && m.concepto !== null)
        .map((m) => ({
          ordenanzaId,
          concepto: m.concepto!,
          valor: m.valor!.toString(),
          moneda: m.moneda || "ARS",
          unidad: m.unidad,
          esPorcentaje: m.es_porcentaje || false,
        }));

      if (montosValues.length > 0) {
        await tx.insert(montos).values(montosValues);
      }
    }

    // 7. INSERT anexos
    if (extraction.anexos.length > 0) {
      const anexosValues = extraction.anexos
        .filter((a) => a.numero !== null)
        .map((a) => ({
          ordenanzaId,
          numero: a.numero!,
          titulo: a.titulo,
          tipo: a.tipo,
          contenido: a.contenido,
        }));

      if (anexosValues.length > 0) {
        await tx.insert(anexos).values(anexosValues);
      }
    }
  });
}

// ─── Main ─────────────────────────────────────────────────────

async function main() {
  console.log("=== Procesador de Ordenanzas con GLM API ===\n");
  console.log(`Modelo: ${MODEL}`);
  console.log(`Batch size: ${PROCESS_ALL ? "TODAS" : BATCH_SIZE}`);
  console.log(`Rate limit: ${RATE_LIMIT_MS}ms entre llamadas`);
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
        `[${procesadas + 1}/${pendientes.length}] ${label}... `,
      );

      // Llamar a GLM API
      const extraction = await callGLMAPI(
        ord.numero,
        ord.anio,
        ord.textoCompleto,
      );

      // Persistir en DB
      await persistExtraction(ord.id, extraction, categoryLookup);

      const cats = extraction.categorias.map((c) => c.slug).join(", ");
      const arts = extraction.articulos.length;
      const ents = extraction.entidades.length;
      const refs = extraction.referencias.length;

      console.log(
        `OK [${arts} arts, ${ents} ents, ${refs} refs] -> ${cats}`,
      );

      procesadas++;
    } catch (error) {
      errores++;
      const msg = error instanceof Error ? error.message : String(error);

      if (error instanceof APIError) {
        // Error de la API (red, auth, rate limit) - no marcar, reintentar próxima vez
        console.log(`ERROR API [${error.status}]: ${msg.slice(0, 200)}`);
        if (error.status === 429) {
          console.log("  -> Rate limit hit, esperando 60s...");
          await sleep(60_000);
        }
      } else {
        // Error de parseo o DB - marcar como ERROR_v1 para no bloquear el pipeline
        console.log(`ERROR (marcando ERROR_v1): ${msg.slice(0, 200)}`);
        try {
          await db
            .update(ordenanzas)
            .set({
              procesadoIa: true,
              versionPrompt: "ERROR_v1",
              resumen: `__ERROR__: ${msg.slice(0, 500)}`,
              fechaProcesadoIa: new Date(),
            })
            .where(eq(ordenanzas.id, ord.id));
        } catch (dbErr) {
          console.log(`  -> No se pudo marcar ERROR_v1: ${dbErr}`);
        }
      }
    }

    // Rate limit entre llamadas
    if (procesadas + errores < pendientes.length) {
      await sleep(RATE_LIMIT_MS);
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
