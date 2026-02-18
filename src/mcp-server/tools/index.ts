/**
 * Exportación de todas las herramientas del MCP server
 * 
 * Este archivo agrupa todas las tools para fácil registro en el servidor principal.
 */

// Tools de búsqueda
export { searchOrdenanzasTool, searchOrdenanzasHandler } from "./search.js";
export { searchByCategoryTool, searchByCategoryHandler } from "./search.js";
export { searchByYearRangeTool, searchByYearRangeHandler } from "./search.js";

// Tools de detalle por ID
export { getOrdenanzaTool, getOrdenanzaHandler } from "./by-id.js";
export { getAnexoTool, getAnexoHandler } from "./by-id.js";

// Tools por entidad
export { searchByEntityTool, searchByEntityHandler } from "./by-entity.js";

// Tools de referencias
export { getReferencesTool, getReferencesHandler } from "./references.js";

// Tools de categorías
export { listCategoriesTool, listCategoriesHandler } from "./categories.js";

// Tools de estadísticas
export { getStatsTool, getStatsHandler } from "./stats.js";

// Tools de similitud (AI)
export { similarOrdenanzasTool, similarOrdenanzasHandler } from "./similar.js";

// Tools de resumen (AI)
export { summarizeTextoTool, summarizeTextoHandler } from "./summarize.js";

// Tool de health check
export { healthCheckTool, healthCheckHandler } from "./health.js";

/**
 * Array con todas las herramientas disponibles
 * Útil para registro masivo en el servidor MCP
 */
export const ALL_TOOLS = [
  // Búsqueda (3)
  searchOrdenanzasTool,
  searchByCategoryTool,
  searchByYearRangeTool,

  // Detalle por ID (2)
  getOrdenanzaTool,
  getAnexoTool,

  // Por entidad (1)
  searchByEntityTool,

  // Referencias (1)
  getReferencesTool,

  // Categorías (1)
  listCategoriesTool,

  // Estadísticas (1)
  getStatsTool,

  // Similitud (1)
  similarOrdenanzasTool,

  // Resumen (1)
  summarizeTextoTool,

  // Health check (1)
  healthCheckTool,
];
