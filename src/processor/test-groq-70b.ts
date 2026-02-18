
import OpenAI from "openai";
import "dotenv/config";
import { db, pool } from "../db/index.js";
import { ordenanzas } from "../db/schema.js";
import { eq, and } from "drizzle-orm";
import { SYSTEM_PROMPT, buildUserPrompt } from "./prompts.js";
import { parseExtractionResponse } from "./parser.js";

async function main() {
  console.log("=== Probando Llama 3.3 70B Versatile (Groq) ===\n");

  // 1. Obtener texto de Ordenanza 19/1986
  const ord = await db
    .select({ textoCompleto: ordenanzas.textoCompleto })
    .from(ordenanzas)
    .where(and(eq(ordenanzas.numero, 19), eq(ordenanzas.anio, 1986)))
    .limit(1);

  if (ord.length === 0) {
    console.error("Ordenanza 19/1986 no encontrada.");
    process.exit(1);
  }

  const textoCompleto = ord[0].textoCompleto;
  const userPrompt = buildUserPrompt(19, 1986, textoCompleto);

  // 2. Configurar cliente Groq
  const client = new OpenAI({
    apiKey: process.env.GROQ_API_KEY,
    baseURL: "https://api.groq.com/openai/v1",
  });

  const startTime = Date.now();

  try {
    // 3. Llamar a la API
    const response = await client.chat.completions.create({
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.2,
      max_tokens: 8192,
    });

    const elapsed = Date.now() - startTime;
    const text = response.choices[0]?.message?.content;

    if (!text) throw new Error("Sin respuesta de texto");

    // 4. Parsear y mostrar resultados
    const result = parseExtractionResponse(text);

    console.log(`Tiempo de respuesta: ${elapsed}ms\n`);
    console.log(`--- Resumen ---\n${result.resumen}\n`);
    console.log(`--- Categorías (${result.categorias.length}) ---`);
    result.categorias.forEach((c) =>
      console.log(`- ${c.slug} (relevancia: ${c.relevancia})`)
    );
    console.log(`\n--- Artículos (${result.articulos.length}) ---`);
    console.log(`--- Entidades (${result.entidades.length}) ---`);
    result.entidades.forEach((e) => console.log(`- ${e.nombre} (${e.tipo})`));

  } catch (error) {
    console.error("\nError:", error instanceof Error ? error.message : String(error));
  } finally {
    await pool.end();
  }
}

main();
