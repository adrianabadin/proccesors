import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";
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

const server = new McpServer({
  name: "ordenanzas-saladillo",
  version: "1.0.0",
});

// =============================================================================
// REGISTRO DE HERRAMIENTAS
// =============================================================================

logger.info({ tools_count: ALL_TOOLS.length }, "Iniciando servidor MCP de Ordenanzas...");

for (const { tool, handler } of ALL_TOOLS) {
  logger.debug(`Registrando herramienta: ${tool.name}...`);
  server.registerTool(
    tool.name,
    {
      title: tool.title,
      description: tool.description,
      inputSchema: tool.inputSchema,
    },
    handler as any
  );
}

// =============================================================================
// HANDLERS DE NOTIFICACIONES
// =============================================================================

server.server.oninitialized = () => {
  logger.info("Servidor MCP inicializado");
};

server.server.onclose = async () => {
  logger.info("Cerrando conexión pool de base de datos...");
  await closePool();
  logger.info("Servidor MCP detenido");
};

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
  logger.error({ error: error instanceof Error ? error.message : String(error) }, "Error fatal al iniciar servidor MCP");
  process.exit(1);
});
