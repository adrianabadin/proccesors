import { Server, StdioServerTransport } from "@modelcontextprotocol/sdk/server";
import "dotenv/config";
import { closePool } from "./db.js";
import { logger } from "./logger.js";
import { ALL_TOOLS } from "./tools/index.js";

// =============================================================================
// SERVIDOR MCP PRINCIPAL
// =============================================================================

/**
 * Servidor MCP para el sistema de ordenanzas municipales de Saladillo.
 * 
 * Proporciona acceso a:
 * - 11 herramientas de consulta y análisis
 * - Búsqueda full-text con ranking
 * - Búsqueda semántica con embeddings
 * - Generación de resúmenes con IA
 * - Estadísticas de procesamiento
 * 
 * Características:
 * - Logging verboso configurable
 * - Error handling con mensajes amigables
 * - Cache de embeddings y resúmenes para reducir costos de API
 * - Conexión a PostgreSQL con pool optimizado
 */

const server = new Server(
  {
    name: "ordenanzas-saladillo",
    version: "1.0.0",
  },
  {
    capabilities: {},
  }
);

// =============================================================================
// REGISTRO DE HERRAMIENTAS
// =============================================================================

logger.info("Iniciando servidor MCP de Ordenanzas...", {
  tools_count: ALL_TOOLS.length,
});

for (const tool of ALL_TOOLS) {
  logger.debug(`Registrando herramienta: ${tool.name}...`);
  server.setRequestHandler(tool.name, tool);
}

// =============================================================================
// HANDLERS DE NOTIFICACIONES
// =============================================================================

server.oninitialized(() => {
  logger.info("Servidor MCP inicializado");
});

server.onclose(async () => {
  logger.info("Cerrando conexión pool de base de datos...");
  await closePool();
  logger.info("Servidor MCP detenido");
});

// =============================================================================
// INICIO DEL SERVIDOR
// =============================================================================

async function main() {
  logger.info("Conectando servidor MCP via stdio...");

  const transport = new StdioServerTransport();

  await server.connect(transport);

  logger.info("Servidor MCP listo y escuchando...");
}

// Ejecutar servidor
main().catch((error) => {
  logger.error("Error fatal al iniciar servidor MCP", {
    error: error instanceof Error ? error.message : String(error),
  });
  process.exit(1);
});
