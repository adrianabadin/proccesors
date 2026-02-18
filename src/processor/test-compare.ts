/**
 * Test comparativo GLM vs Groq
 * 
 * Toma 3 ordenanzas ya procesadas con GLM, las procesa con Groq,
 * y muestra una comparación lado a lado SIN persistir los cambios.
 */

import OpenAI from "openai";
import "dotenv/config";
import { db, pool } from "../db/index.js";
import { ordenanzas, articulos, ordenanzaCategorias, categorias } from "../db/schema.js";
import { eq, inArray } from "drizzle-orm";
import { SYSTEM_PROMPT, buildUserPrompt } from "./prompts.js";
import { parseExtractionResponse, type ExtractionResult } from "./parser.js";

// ─── Clients ───────────────────────────────────────────────────

const glmClient = new OpenAI({
  apiKey: process.env.GLM_API_KEY,
  baseURL: "https://open.bigmodel.cn/api/paas/v4/",
});

const groqClient = new OpenAI({
  apiKey: process.env.GROQ_API_KEY,
  baseURL: "https://api.groq.com/openai/v1",
});

// ─── Types ────────────────────────────────────────────────────

interface GLMData {
  resumen: string | null;
  categorias: string[];
  articulos: number;
  fechaProcesado: Date | null;
}

interface ComparisonResult {
  numero: number;
  anio: number;
  titulo: string;
  glm: GLMData;
  groq: {
    resumen: string;
    categorias: string[];
    articulos: number;
    tiempo: number;
    error?: string;
  };
}

// ─── Helpers ──────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function callGroqAPI(
  numero: number,
  anio: number,
  textoCompleto: string,
): Promise<{ result: ExtractionResult; time: number }> {
  const userPrompt = buildUserPrompt(numero, anio, textoCompleto);
  const startTime = Date.now();

  const response = await groqClient.chat.completions.create({
    model: "llama-3.1-8b-instant",
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: userPrompt },
    ],
    temperature: 0.2,
    max_tokens: 8192,
  });

  const elapsed = Date.now() - startTime;
  const text = response.choices[0]?.message?.content;

  if (!text) {
    throw new Error("Groq no devolvió texto en la respuesta");
  }

  return { result: parseExtractionResponse(text), time: elapsed };
}

// ─── Main ─────────────────────────────────────────────────────

async function main() {
  console.log("=== Test Comparativo: GLM-4.7-Flash vs Llama-3.1-8B-Instant ===\n");

  // 1. Obtener 3 ordenanzas ya procesadas con GLM
  const procesadasGLM = await db
    .select({
      id: ordenanzas.id,
      numero: ordenanzas.numero,
      anio: ordenanzas.anio,
      titulo: ordenanzas.titulo,
      resumen: ordenanzas.resumen,
      fechaProcesadoIa: ordenanzas.fechaProcesadoIa,
      textoCompleto: ordenanzas.textoCompleto,
    })
    .from(ordenanzas)
    .where(eq(ordenanzas.procesadoIa, true))
    .orderBy(ordenanzas.anio, ordenanzas.numero)
    .limit(3);

  if (procesadasGLM.length === 0) {
    console.log("No hay ordenanzas procesadas con GLM para comparar.");
    await pool.end();
    return;
  }

  console.log(`Comparando ${procesadasGLM.length} ordenanzas procesadas con GLM:\n`);

  // 2. Cargar categorías para lookup
  const catRows = await db.select({ id: categorias.id, slug: categorias.slug }).from(categorias);
  const catLookup: Record<number, string> = {};
  for (const row of catRows) {
    catLookup[row.id] = row.slug;
  }

  const results: ComparisonResult[] = [];

  // 3. Procesar cada ordenanza con Groq
  for (const ord of procesadasGLM) {
    console.log(`\nProcesando Ordenanza N° ${ord.numero}/${ord.anio} con Groq...`);

    // Obtener datos de GLM desde la DB
    const glmCategorias = await db
      .select({ categoriaId: ordenanzaCategorias.categoriaId })
      .from(ordenanzaCategorias)
      .where(eq(ordenanzaCategorias.ordenanzaId, ord.id));

    const glmArticulos = await db
      .select({ id: articulos.id })
      .from(articulos)
      .where(eq(articulos.ordenanzaId, ord.id));

    const glmData: GLMData = {
      resumen: ord.resumen,
      categorias: glmCategorias.map((c) => catLookup[c.categoriaId] || `ID:${c.categoriaId}`),
      articulos: glmArticulos.length,
      fechaProcesado: ord.fechaProcesadoIa,
    };

    // Procesar con Groq
    let groqData: ComparisonResult["groq"];
    try {
      const { result, time } = await callGroqAPI(ord.numero, ord.anio, ord.textoCompleto);
      groqData = {
        resumen: result.resumen,
        categorias: result.categorias.map((c) => c.slug),
        articulos: result.articulos.length,
        tiempo: time,
      };
      console.log(`  OK en ${time}ms`);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      groqData = {
        resumen: "",
        categorias: [],
        articulos: 0,
        tiempo: 0,
        error: msg.slice(0, 200),
      };
      console.log(`  ERROR: ${msg.slice(0, 100)}`);
    }

    results.push({
      numero: ord.numero,
      anio: ord.anio,
      titulo: ord.titulo,
      glm: glmData,
      groq: groqData,
    });

    // Rate limit: 30 RPM = 2000ms
    await sleep(2000);
  }

  // 4. Mostrar comparación
  console.log("\n" + "=".repeat(80));
  console.log("COMPARACIÓN DE RESULTADOS");
  console.log("=".repeat(80) + "\n");

  for (const result of results) {
    console.log(`\n### Ordenanza N° ${result.numero}/${result.anio}`);
    console.log(`Título: ${result.titulo}\n`);

    console.log("--- GLM-4.7-Flash ---");
    console.log(`Resumen: ${result.glm.resumen?.slice(0, 150) || "N/A"}...`);
    console.log(`Categorías (${result.glm.categorias.length}): ${result.glm.categorias.join(", ")}`);
    console.log(`Artículos: ${result.glm.articulos}`);
    console.log(`Fecha procesado: ${result.glm.fechaProcesado?.toISOString() || "N/A"}`);

    console.log("\n--- Llama-3.1-8B-Instant (Groq) ---");
    if (result.groq.error) {
      console.log(`ERROR: ${result.groq.error}`);
    } else {
      console.log(`Resumen: ${result.groq.resumen?.slice(0, 150) || "N/A"}...`);
      console.log(`Categorías (${result.groq.categorias.length}): ${result.groq.categorias.join(", ")}`);
      console.log(`Artículos: ${result.groq.articulos}`);
      console.log(`Tiempo de respuesta: ${result.groq.tiempo}ms`);
    }

    console.log("\n--- Métricas Comparativas ---");
    if (!result.groq.error) {
      const catDiff = result.groq.categorias.length - result.glm.categorias.length;
      const artDiff = result.groq.articulos - result.glm.articulos;
      console.log(`Diferencia categorías: ${catDiff > 0 ? "+" : ""}${catDiff}`);
      console.log(`Diferencia artículos: ${artDiff > 0 ? "+" : ""}${artDiff}`);
    }

    console.log("-".repeat(80));
  }

  // 5. Resumen final
  console.log("\n" + "=".repeat(80));
  console.log("RESUMEN FINAL");
  console.log("=".repeat(80));

  const successResults = results.filter((r) => !r.groq.error);
  const avgTime = successResults.length > 0
    ? Math.round(successResults.reduce((sum, r) => sum + r.groq.tiempo, 0) / successResults.length)
    : 0;

  console.log(`\nOrdenanzas procesadas: ${results.length}`);
  console.log(`Éxitos Groq: ${successResults.length}`);
  console.log(`Errores Groq: ${results.length - successResults.length}`);
  console.log(`Tiempo promedio Groq: ${avgTime}ms`);

  // Categorías coincidentes
  let catMatches = 0;
  let catTotal = 0;
  for (const r of successResults) {
    for (const cat of r.glm.categorias) {
      catTotal++;
      if (r.groq.categorias.includes(cat)) catMatches++;
    }
  }
  const catMatchRate = catTotal > 0 ? Math.round((catMatches / catTotal) * 100) : 0;
  console.log(`Coincidencia categorías: ${catMatchRate}% (${catMatches}/${catTotal})`);

  console.log("\nNOTA: Los datos de Groq NO se guardaron en la base de datos.");
  console.log("Los resultados de GLM permanecen intactos.\n");

  await pool.end();
}

main().catch((error) => {
  console.error("\nError fatal:", error);
  process.exit(1);
});
