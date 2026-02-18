/**
 * Menú interactivo para seleccionar el procesador de ordenanzas.
 *
 * Uso:
 *   npx tsx src/processor/run.ts
 *   npx tsx src/processor/run.ts --all       # pasa --all al procesador elegido
 *   BATCH_SIZE=10 npx tsx src/processor/run.ts
 */

import { createInterface } from "readline";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const extraArgs = process.argv.slice(2); // ej: ["--all"]

// ─── Config de procesadores disponibles ───────────────────────

const PROCESSORS = [
  {
    name: "Gemini 2.0 Flash",
    desc: "Google - JSON nativo, buena calidad, free tier generoso",
    file: "index-gemini.ts",
    envKey: "GEMINI_API_KEY",
    rateMs: 1000,
  },
  {
    name: "DeepSeek-V3 (deepseek-chat)",
    desc: "DeepSeek - alta calidad, muy bajo costo",
    file: "index-deepseek.ts",
    envKey: "DEEPSEEK_API_KEY",
    rateMs: 1000,
  },
  {
    name: "GLM 4.7 Flash (Zhipu AI)",
    desc: "GLM - rápido, bajo costo, compatible OpenAI",
    file: "index-glm.ts",
    envKey: "GLM_API_KEY",
    rateMs: 1000,
  },
  {
    name: "Groq Llama 3.3 70B",
    desc: "Groq - velocidad extrema, límite 30 RPM (~3500ms entre llamadas)",
    file: "index-groq.ts",
    envKey: "GROQ_API_KEY",
    rateMs: 3500,
  },
] as const;

// ─── Helpers ──────────────────────────────────────────────────

function printMenu() {
  console.log("\n╔══════════════════════════════════════════════════════╗");
  console.log("║       Procesador de Ordenanzas - Selector de IA       ║");
  console.log("╚══════════════════════════════════════════════════════╝\n");

  PROCESSORS.forEach((p, i) => {
    const keyOk = !!process.env[p.envKey];
    const status = keyOk ? "✓" : "✗";
    console.log(`  [${i + 1}] ${status} ${p.name}`);
    console.log(`      ${p.desc}`);
    if (!keyOk) {
      console.log(`      ⚠ ${p.envKey} no configurada en .env`);
    }
    console.log();
  });

  console.log("  [0] Salir\n");

  if (extraArgs.length > 0) {
    console.log(`  Args adicionales: ${extraArgs.join(" ")}\n`);
  }
}

function ask(prompt: string): Promise<string> {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(prompt, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function runProcessor(file: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const scriptPath = join(__dirname, file);
    const args = ["tsx", scriptPath, ...extraArgs];

    console.log(`\nEjecutando: npx ${args.join(" ")}\n`);
    console.log("─".repeat(60));

    const child = spawn("npx", args, {
      stdio: "inherit",
      shell: true,
      env: process.env,
    });

    child.on("close", (code) => {
      console.log("\n" + "─".repeat(60));
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Proceso terminó con código ${code}`));
      }
    });

    child.on("error", reject);
  });
}

// ─── Main ─────────────────────────────────────────────────────

async function main() {
  // Cargar .env antes de mostrar el menú (para detectar keys configuradas)
  const { config } = await import("dotenv");
  config();

  printMenu();

  const answer = await ask("Seleccioná un procesador [1-4] o 0 para salir: ");
  const choice = parseInt(answer, 10);

  if (choice === 0 || isNaN(choice)) {
    console.log("Saliendo.");
    process.exit(0);
  }

  const processor = PROCESSORS[choice - 1];
  if (!processor) {
    console.error(`Opción inválida: ${answer}`);
    process.exit(1);
  }

  if (!process.env[processor.envKey]) {
    console.error(`\n⚠ ${processor.envKey} no está configurada en .env.`);
    console.error("Agregá la clave API y volvé a intentar.\n");
    process.exit(1);
  }

  try {
    await runProcessor(processor.file);
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    console.error(`\nError al ejecutar procesador: ${msg}`);
    process.exit(1);
  }
}

main();
