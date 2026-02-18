/**
 * Test de DeepSeek-V3 sobre las 3 ordenanzas de prueba.
 */

import OpenAI from "openai";
import "dotenv/config";
import { db, pool } from "../db/index.js";
import { ordenanzas } from "../db/schema.js";
import { eq, and, inArray } from "drizzle-orm";
import { SYSTEM_PROMPT, buildUserPrompt } from "./prompts.js";
import { parseExtractionResponse } from "./parser.js";

const client = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: "https://api.deepseek.com",
});

async function main() {
  console.log("=== Test DeepSeek-V3 (deepseek-chat) ===\n");

  // Buscar las 3 ordenanzas específicas (18, 19, 20 del año 1986)
  const targetOrdenanzas = await db
    .select({
      numero: ordenanzas.numero,
      anio: ordenanzas.anio,
      titulo: ordenanzas.titulo,
      textoCompleto: ordenanzas.textoCompleto,
    })
    .from(ordenanzas)
    .where(
      and(
        eq(ordenanzas.anio, 1986),
        inArray(ordenanzas.numero, [18, 19, 20])
      )
    )
    .orderBy(ordenanzas.numero);

  if (targetOrdenanzas.length === 0) {
    console.error("No se encontraron las ordenanzas 18, 19 y 20 de 1986.");
    process.exit(1);
  }

  for (const ord of targetOrdenanzas) {
    console.log(`\n--- Procesando Ordenanza N° ${ord.numero}/${ord.anio} ---`);
    console.log(`Título: ${ord.titulo}`);

    const userPrompt = buildUserPrompt(ord.numero, ord.anio, ord.textoCompleto);
    const start = Date.now();

    try {
      const response = await client.chat.completions.create({
        model: "deepseek-chat",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: userPrompt },
        ],
        temperature: 0.2,
        max_tokens: 8192,
      });

      const elapsed = Date.now() - start;
      const text = response.choices[0]?.message?.content;

      if (!text) throw new Error("Respuesta vacía");

      // Parsear
      const result = parseExtractionResponse(text);

      console.log(`Tiempo: ${elapsed}ms`);
      console.log(`Resumen: ${result.resumen.slice(0, 150)}...`);
      console.log(
        `Categorías (${result.categorias.length}): ${result.categorias
          .map((c) => `${c.slug} (${c.relevancia})`)
          .join(", ")}`
      );
      console.log(`Artículos extraídos: ${result.articulos.length}`);
      console.log(`Entidades detectadas: ${result.entidades.length}`);
      
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : String(error));
    }
  }

  await pool.end();
}

main();
