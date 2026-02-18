import { db, pool } from "../db/index.js";
import { ordenanzas } from "../db/schema.js";
import { sql } from "drizzle-orm";
import { readFileSync, readdirSync, statSync } from "fs";
import { join, basename } from "path";

/**
 * Script de ingesta raw de archivos .txt a la base de datos.
 * Lee archivos de carpetas por año (1986/-2025/) y los inserta en la tabla ordenanzas.
 */

const BATCH_SIZE = 100;

interface OrdenanzaData {
  numero: number;
  anio: number;
  titulo: string;
  extracto: string | null;
  textoCompleto: string;
}

/**
 * Parsea el número de ordenanza del nombre del archivo.
 * Formato esperado: "Ordenanza N° {numero}.txt" o "Ordenanza Nº {numero}.txt"
 */
function parseNumeroFromFilename(filename: string): number | null {
  // Buscar patrones como "N° 123", "Nº 123", etc.
  const match = filename.match(/[N°Nº]\s*(\d+)/);
  if (match) {
    return parseInt(match[1], 10);
  }
  return null;
}

/**
 * Extrae el extracto si la segunda línea termina con [...] o […]
 */
function extraerExtracto(lineas: string[]): string | null {
  // Encontrar la segunda línea no vacía
  let lineasNoVacias = 0;
  for (const linea of lineas) {
    const trimmed = linea.trim();
    if (trimmed === "") continue;
    
    lineasNoVacias++;
    if (lineasNoVacias === 2) {
      // Verificar si termina con [...] o […]
      if (trimmed.endsWith("[...]") || trimmed.endsWith("[…]")) {
        return trimmed;
      }
      return null;
    }
  }
  return null;
}

/**
 * Procesa un archivo .txt y extrae los datos de la ordenanza.
 */
function procesarArchivo(filepath: string, anio: string): OrdenanzaData | null {
  const filename = basename(filepath);
  const numero = parseNumeroFromFilename(filename);
  
  if (numero === null) {
    console.warn(`  ⚠️  No se pudo parsear número de: ${filename}`);
    return null;
  }

  const contenido = readFileSync(filepath, "utf-8");
  const lineas = contenido.split("\n");
  
  // Título: primera línea no vacía
  let titulo = "";
  for (const linea of lineas) {
    const trimmed = linea.trim();
    if (trimmed !== "") {
      titulo = trimmed;
      break;
    }
  }
  
  if (!titulo) {
    titulo = `Ordenanza N° ${numero}/${anio}`;
  }

  // Extracto: segunda línea no vacía si termina con [...] o […]
  const extracto = extraerExtracto(lineas);

  return {
    numero,
    anio: parseInt(anio, 10),
    titulo,
    extracto,
    textoCompleto: contenido,
  };
}

/**
 * Escanea los directorios de años y retorna lista de archivos .txt
 */
function escanearDirectorios(): { anio: string; filepath: string }[] {
  const archivos: { anio: string; filepath: string }[] = [];
  const rootDir = process.cwd();
  
  const entries = readdirSync(rootDir);
  
  for (const entry of entries) {
    // Verificar si es un directorio de 4 dígitos (año)
    if (!/^\d{4}$/.test(entry)) continue;
    
    const dirPath = join(rootDir, entry);
    const stats = statSync(dirPath);
    
    if (!stats.isDirectory()) continue;
    
    // Escanear archivos .txt en este directorio
    const files = readdirSync(dirPath);
    for (const file of files) {
      if (file.endsWith(".txt")) {
        archivos.push({
          anio: entry,
          filepath: join(dirPath, file),
        });
      }
    }
  }
  
  return archivos;
}

/**
 * Inserta un batch de ordenanzas en la base de datos usando batch insert.
 */
async function insertarBatch(batch: OrdenanzaData[]): Promise<number> {
  if (batch.length === 0) return 0;

  try {
    // Usar batch insert de Drizzle - mucho más rápido que insert uno por uno
    const result = await db
      .insert(ordenanzas)
      .values(
        batch.map((o) => ({
          numero: o.numero,
          anio: o.anio,
          titulo: o.titulo,
          extracto: o.extracto,
          textoCompleto: o.textoCompleto,
        }))
      )
      .onConflictDoNothing({
        target: [ordenanzas.numero, ordenanzas.anio],
      });

    // Drizzle no retorna count directamente en conflict, así que devolvemos el batch size
    // Las filas que ya existen simplemente se ignoran
    return batch.length;
  } catch (error) {
    console.error(`  ❌ Error en batch insert:`, error);
    return 0;
  }
}

/**
 * Función principal de ingesta.
 */
async function main() {
  console.log("📁 Iniciando ingesta de archivos .txt...\n");
  
  // Escanear directorios
  const archivos = escanearDirectorios();
  console.log(`📊 Total de archivos encontrados: ${archivos.length}\n`);
  
  if (archivos.length === 0) {
    console.log("⚠️  No se encontraron archivos .txt en los directorios de años.");
    process.exit(0);
  }
  
  // Agrupar por año para loggear progreso
  const porAnio: Record<string, number> = {};
  archivos.forEach((a) => {
    porAnio[a.anio] = (porAnio[a.anio] || 0) + 1;
  });
  
  console.log("📂 Archivos por año:");
  Object.entries(porAnio)
    .sort(([a], [b]) => parseInt(a) - parseInt(b))
    .forEach(([anio, count]) => {
      console.log(`   ${anio}: ${count} archivos`);
    });
  console.log("");
  
  // Procesar en batches
  let procesados = 0;
  let insertados = 0;
  let fallidos = 0;
  let batch: OrdenanzaData[] = [];
  let anioActual = "";
  let insertadosPorAnio: Record<string, number> = {};
  
  for (const { anio, filepath } of archivos) {
    // Log de progreso por año
    if (anio !== anioActual) {
      if (anioActual && batch.length > 0) {
        const insertadosBatch = await insertarBatch(batch);
        insertados += insertadosBatch;
        insertadosPorAnio[anioActual] = (insertadosPorAnio[anioActual] || 0) + insertadosBatch;
        batch = [];
      }
      anioActual = anio;
      console.log(`\n📅 Procesando año ${anio}...`);
    }
    
    const datos = procesarArchivo(filepath, anio);
    
    if (datos) {
      batch.push(datos);
      procesados++;
    } else {
      fallidos++;
    }
    
    // Insertar batch cuando llega al tamaño
    if (batch.length >= BATCH_SIZE) {
      const insertadosBatch = await insertarBatch(batch);
      insertados += insertadosBatch;
      insertadosPorAnio[anio] = (insertadosPorAnio[anio] || 0) + insertadosBatch;
      batch = [];
      
      // Log de progreso
      process.stdout.write(`   Progreso: ${insertados} insertados...\r`);
    }
  }
  
  // Insertar último batch
  if (batch.length > 0) {
    const insertadosBatch = await insertarBatch(batch);
    insertados += insertadosBatch;
    insertadosPorAnio[anioActual] = (insertadosPorAnio[anioActual] || 0) + insertadosBatch;
  }
  
  console.log("\n\n✅ Ingesta completada!");
  console.log(`\n📊 Resumen:`);
  console.log(`   - Archivos procesados: ${procesados}`);
  console.log(`   - Insertados en DB: ${insertados}`);
  console.log(`   - Fallidos: ${fallidos}`);
  
  console.log(`\n📈 Insertados por año:`);
  Object.entries(insertadosPorAnio)
    .sort(([a], [b]) => parseInt(a) - parseInt(b))
    .forEach(([anio, count]) => {
      console.log(`   ${anio}: ${count}`);
    });
  
  // Cerrar conexión
  await pool.end();
}

// Ejecutar
main().catch((error) => {
  console.error("\n❌ Error fatal:", error);
  process.exit(1);
});
