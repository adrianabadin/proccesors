/**
 * Procesador CONCURRENTE de ordenanzas con DeepSeek API (DeepSeek-V3).
 * 
 * Arquitectura optimizada para VPS 2 núcleos / 4GB RAM:
 * - Worker Pool para llamadas concurrentes a API
 * - Batch processing para persistencia en BD
 * - Circuit Breaker para resiliencia
 * - Retry con exponential backoff
 * - Lógica de resumibilidad compatible con processor original
 * 
 * Configuración por entorno:
 * - DEEPSEEK_WORKERS=6 (óptimo para 2 núcleos)
 * - DB_BATCH_SIZE=5 (para limitar RAM)
 * - MAX_QUEUE_SIZE=50 (backpressure control)
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

// ─── Configuración Concurrente ────────────────────────────────────────

// Configuración optimizada para 2 núcleos / 4GB RAM
const CONFIG = {
  // Workers concurrentes para API (6 = 3 por núcleo, dejando margen)
  API_WORKERS: parseInt(process.env.DEEPSEEK_WORKERS ?? "6", 10),
  
  // Batch size para persistencia en BD (5 para limitar uso de RAM)
  DB_BATCH_SIZE: parseInt(process.env.DB_BATCH_SIZE ?? "5", 10),
  
  // Límite de cola para backpressure (50 para evitar saturación)
  MAX_QUEUE_SIZE: parseInt(process.env.MAX_QUEUE_SIZE ?? "50", 10),
  
  // Retry y Circuit Breaker
  MAX_RETRIES: 3,
  CIRCUIT_BREAKER_THRESHOLD: 5,
  RETRY_BASE_DELAY: 2000, // 2s base
  
  // Timeouts
  API_TIMEOUT: 300_000, // 5 minutos por petición
  WORKER_IDLE_TIMEOUT: 30_000, // 30s idle
  
  // Configuración compatible con processor original
  BATCH_SIZE: parseInt(process.env.BATCH_SIZE ?? "50", 10),
  PROCESS_ALL: process.argv.includes("--all"),
  MODEL: process.env.MODEL ?? "deepseek-chat",
  
  // Verbose logging
  VERBOSE: process.env.VERBOSE === "true",
};

// ─── Client y Types ───────────────────────────────────────────────────

const client = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: "https://api.deepseek.com",
});

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

interface ProcessingResult {
  ordenanzaId: string;
  ordenanza: OrdenanzaRow;
  extraction?: ExtractionResult;
  error?: Error;
  retryCount: number;
  startTime: number;
}

interface PerformanceMetrics {
  startTime: number;
  totalProcessed: number;
  totalErrors: number;
  totalRetries: number;
  apiCallsPerSecond: number;
  averageLatency: number;
  circuitBreakerTrips: number;
}

// ─── Utilidades ──────────────────────────────────────────────────────────

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function logVerbose(message: string, data?: any) {
  if (CONFIG.VERBOSE) {
    console.log(`[VERBOSE] ${message}`, data || "");
  }
}

// ─── Circuit Breaker ────────────────────────────────────────────────────

class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private isOpen = false;
  private tripCount = 0;

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.isOpen) {
      const timeSinceLastFailure = Date.now() - this.lastFailureTime;
      if (timeSinceLastFailure < 60000) { // 1 minuto de cooldown
        throw new Error('Circuit breaker OPEN - esperando cooldown');
      } else {
        this.isOpen = false;
        this.failures = 0;
        logVerbose('Circuit breaker RESET');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    if (this.isOpen) {
      this.isOpen = false;
      logVerbose('Circuit breaker CLOSED');
    }
  }

  private onFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    
    if (this.failures >= CONFIG.CIRCUIT_BREAKER_THRESHOLD) {
      this.isOpen = true;
      this.tripCount++;
      console.warn(`⚡ Circuit breaker TRIPPED (${this.tripCount} veces)`);
    }
  }

  getTrips(): number {
    return this.tripCount;
  }
}

// ─── Task Queue ────────────────────────────────────────────────────────

class TaskQueue {
  private queue: OrdenanzaRow[] = [];
  private processing = false;
  private finished = false;

  constructor(private maxSize: number = CONFIG.MAX_QUEUE_SIZE) {}

  enqueue(item: OrdenanzaRow): boolean {
    if (this.queue.length >= this.maxSize) {
      return false; // Rechazado por backpressure
    }
    this.queue.push(item);
    return true;
  }

  dequeue(): OrdenanzaRow | undefined {
    return this.queue.shift();
  }

  size(): number {
    return this.queue.length;
  }

  isEmpty(): boolean {
    return this.queue.length === 0 && !this.processing;
  }

  markProcessing(isProcessing: boolean) {
    this.processing = isProcessing;
  }

  markFinished() {
    this.finished = true;
  }

  isFinished(): boolean {
    return this.finished && this.isEmpty();
  }
}

// ─── Database Batcher ────────────────────────────────────────────────────

class DatabaseBatcher {
  private queue: ProcessingResult[] = [];
  private categoryLookup: CategoryLookup;
  private flushPromise: Promise<void> | null = null;

  constructor(categoryLookup: CategoryLookup) {
    this.categoryLookup = categoryLookup;
  }

  async addResult(result: ProcessingResult): Promise<void> {
    this.queue.push(result);
    
    // Trigger flush si llegamos al batch size
    if (this.queue.length >= CONFIG.DB_BATCH_SIZE) {
      if (!this.flushPromise) {
        this.flushPromise = this.flushBatch();
        await this.flushPromise;
        this.flushPromise = null;
      }
    }
  }

  async flushRemaining(): Promise<void> {
    if (this.queue.length > 0) {
      await this.flushBatch();
    }
  }

  private async flushBatch(): Promise<void> {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, CONFIG.DB_BATCH_SIZE);
    logVerbose(`Flushing batch de ${batch.length} resultados a BD`);

    // Procesar batch completo en una transacción por resultado
    for (const result of batch) {
      if (result.error) {
        // Manejar errores marcando como ERROR_v1 como en el original
        await this.markAsError(result);
      } else if (result.extraction) {
        // Persistir resultado exitoso
        await this.persistResult(result.ordenanzaId, result.extraction);
      }
    }
  }

  private async persistResult(ordenanzaId: string, extraction: ExtractionResult): Promise<void> {
    // Usar la misma lógica de persistencia que el processor original
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

      // 2. INSERT artículos (con deduplicación)
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

      // 3. UPSERT entidades + INSERT relaciones
      for (const ent of extraction.entidades) {
        const entidadId = await this.upsertEntidad(tx, ent);

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

      // 4. INSERT categorías
      const catValues = extraction.categorias
        .filter((cat) => this.categoryLookup[cat.slug] !== undefined)
        .map((cat) => ({
          ordenanzaId,
          categoriaId: this.categoryLookup[cat.slug],
          relevancia: cat.relevancia,
        }));

      if (catValues.length > 0) {
        try {
          await tx.insert(ordenanzaCategorias).values(catValues).onConflictDoNothing();
        } catch (catError) {
          // Log error but don't fail the whole transaction
          logVerbose(`Error inserting categorías para ${ordenanzaId}: ${catError}`);
        }
      }

      // 5. INSERT referencias_normativas
      for (const ref of extraction.referencias) {
        let ordenanzaDestinoId: string | null = null;

        if (ref.destino_numero && ref.destino_anio) {
          ordenanzaDestinoId = await this.resolveOrdenanzaId(
            tx,
            ref.destino_numero,
            ref.destino_anio,
          );
        }

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

  private async markAsError(result: ProcessingResult): Promise<void> {
    const msg = result.error!.message.slice(0, 500);
    try {
      await db
        .update(ordenanzas)
        .set({
          procesadoIa: true,
          versionPrompt: "ERROR_v1",
          resumen: `__ERROR__: ${msg}`,
          fechaProcesadoIa: new Date(),
        })
        .where(eq(ordenanzas.id, result.ordenanzaId));
    } catch (dbErr) {
      console.error(`No se pudo marcar ERROR_v1 para ${result.ordenanza.numero}/${result.ordenanza.anio}: ${dbErr}`);
    }
  }

  private async upsertEntidad(
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

  private async resolveOrdenanzaId(
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
}

// ─── API Worker ───────────────────────────────────────────────────────────

class DeepSeekWorker {
  private id: number;
  private circuitBreaker: CircuitBreaker;
  private dbBatcher: DatabaseBatcher;

  constructor(id: number, dbBatcher: DatabaseBatcher) {
    this.id = id;
    this.circuitBreaker = new CircuitBreaker();
    this.dbBatcher = dbBatcher;
  }

  async start(taskQueue: TaskQueue): Promise<void> {
    logVerbose(`Worker ${this.id} iniciado`);

    while (!taskQueue.isFinished()) {
      const task = taskQueue.dequeue();
      if (!task) {
        await sleep(100); // Pequeña espera si no hay tareas
        continue;
      }

      taskQueue.markProcessing(true);
      await this.processOrdenanza(task);
      taskQueue.markProcessing(false);
    }

    logVerbose(`Worker ${this.id} finalizado`);
  }

  private async processOrdenanza(ordenanza: OrdenanzaRow): Promise<void> {
    const result: ProcessingResult = {
      ordenanzaId: ordenanza.id,
      ordenanza,
      retryCount: 0,
      startTime: Date.now(),
    };

    const label = `Ordenanza N° ${ordenanza.numero}/${ordenanza.anio}`;
    process.stdout.write(`[Worker ${this.id}] ${label}... `);

    try {
      result.extraction = await this.callWithRetry(ordenanza);
      
      const cats = result.extraction.categorias.map((c) => c.slug).join(", ");
      const arts = result.extraction.articulos.length;
      const ents = result.extraction.entidades.length;
      const refs = result.extraction.referencias.length;
      
      console.log(`OK [${arts} arts, ${ents} ents, ${refs} refs] -> ${cats}`);
      
      // Enviar a batcher para persistencia
      await this.dbBatcher.addResult(result);
      
    } catch (error) {
      result.error = error instanceof Error ? error : new Error(String(error));
      console.log(`ERROR: ${result.error.message.slice(0, 200)}`);
      
      // Enviar error a batcher
      await this.dbBatcher.addResult(result);
    }
  }

  private async callWithRetry(ordenanza: OrdenanzaRow): Promise<ExtractionResult> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= CONFIG.MAX_RETRIES; attempt++) {
      try {
        return await this.circuitBreaker.execute(async () => {
          return await this.callDeepSeekAPI(ordenanza);
        });
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Determinar si reintentar
        if (attempt < CONFIG.MAX_RETRIES && this.shouldRetry(lastError)) {
          const delay = CONFIG.RETRY_BASE_DELAY * Math.pow(2, attempt - 1); // Exponential backoff
          console.log(`  -> Reintento ${attempt}/${CONFIG.MAX_RETRIES} en ${delay}ms`);
          await sleep(delay);
          continue;
        }
        
        break;
      }
    }

    throw lastError;
  }

  private async callDeepSeekAPI(ordenanza: OrdenanzaRow): Promise<ExtractionResult> {
    const userPrompt = buildUserPrompt(ordenanza.numero, ordenanza.anio, ordenanza.textoCompleto);

    const response = await client.chat.completions.create({
      model: CONFIG.MODEL,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.2,
      max_tokens: 8192,
    });

    const text = response.choices[0]?.message?.content;
    if (!text) {
      throw new Error("DeepSeek no devolvió texto en la respuesta");
    }

    return parseExtractionResponse(text);
  }

  private shouldRetry(error: Error): boolean {
    // API errors son reintentables
    if (error instanceof APIError) {
      return true;
    }

    // Rate limit y balance son reintentables
    const msg = error.message.toLowerCase();
    if (msg.includes("429") || msg.includes("insufficient balance")) {
      return true;
    }

    // Errores de parseo NO son reintentables
    if (msg.includes("parse") || msg.includes("json") || msg.includes("schema")) {
      return false;
    }

    // Por defecto reintentar errores de red/API
    return true;
  }

  getCircuitBreakerTrips(): number {
    return this.circuitBreaker.getTrips();
  }
}

// ─── Main Concurrent ───────────────────────────────────────────────────────

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

async function main() {
  console.log("=== Procesador CONCURRENTE de Ordenanzas con DeepSeek-V3 ===\n");
  console.log(`Configuración:`);
  console.log(`  - Workers concurrentes: ${CONFIG.API_WORKERS}`);
  console.log(`  - DB batch size: ${CONFIG.DB_BATCH_SIZE}`);
  console.log(`  - Max queue size: ${CONFIG.MAX_QUEUE_SIZE}`);
  console.log(`  - Modelo: ${CONFIG.MODEL}`);
  console.log(`  - Batch size: ${CONFIG.PROCESS_ALL ? "TODAS" : CONFIG.BATCH_SIZE}`);
  console.log(`  - Max retries: ${CONFIG.MAX_RETRIES}`);
  console.log(`  - Prompt version: ${PROMPT_VERSION}\n`);

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

  // Query ordenanzas sin procesar (misma lógica que original)
  const limit = CONFIG.PROCESS_ALL ? 10000 : CONFIG.BATCH_SIZE;
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

  // Inicializar componentes concurrentes
  const taskQueue = new TaskQueue(CONFIG.MAX_QUEUE_SIZE);
  const dbBatcher = new DatabaseBatcher(categoryLookup);
  const workers = Array(CONFIG.API_WORKERS).fill(null).map((_, id) => 
    new DeepSeekWorker(id, dbBatcher)
  );

  // Métricas de performance
  const metrics: PerformanceMetrics = {
    startTime: Date.now(),
    totalProcessed: 0,
    totalErrors: 0,
    totalRetries: 0,
    apiCallsPerSecond: 0,
    averageLatency: 0,
    circuitBreakerTrips: 0,
  };

  // Producer: Enqueue todas las tareas
  console.log("Encolando tareas para procesamiento concurrente...");
  for (const ord of pendientes) {
    if (!taskQueue.enqueue(ord)) {
      console.warn(`⚠️  Queue llena, rechazando ordenanza ${ord.numero}/${ord.anio}`);
      break;
    }
  }
  taskQueue.markFinished();
  console.log(`Tareas encoladas: ${taskQueue.size()}`);

  // Consumers: Iniciar workers concurrentes
  console.log(`Iniciando ${CONFIG.API_WORKERS} workers concurrentes...`);
  const startTime = Date.now();

  await Promise.all(workers.map(worker => worker.start(taskQueue)));

  // Flush final de batch
  console.log("\nFinalizando persistencia en BD...");
  await dbBatcher.flushRemaining();

  // Calcular métricas finales
  const elapsed = ((Date.now() - startTime) / 1000);
  const processingRate = (pendientes.length / elapsed).toFixed(2);
  
  // Contar errores y circuit breaker trips
  for (const worker of workers) {
    metrics.circuitBreakerTrips += worker.getCircuitBreakerTrips();
  }

  // Resumen final
  console.log("\n=== Procesamiento concurrente completado ===");
  console.log(`Procesadas: ${pendientes.length}`);
  console.log(`Tiempo total: ${elapsed.toFixed(1)}s`);
  console.log(`Velocidad: ${processingRate} ord/segundo (${(parseFloat(processingRate) * 60).toFixed(1)} ord/min)`);
  console.log(`Circuit breaker trips: ${metrics.circuitBreakerTrips}`);
  console.log(`Configuración: ${CONFIG.API_WORKERS} workers, batch ${CONFIG.DB_BATCH_SIZE}`);

  await pool.end();
}

// Ejecutar
main().catch((error) => {
  console.error("\nError fatal:", error);
  process.exit(1);
});