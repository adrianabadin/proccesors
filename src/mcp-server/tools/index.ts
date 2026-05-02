/**
 * Exportación de todas las herramientas del MCP server
 *
 * Este archivo agrupa todas las tools para fácil registro en el servidor principal.
 */

// Imports de tools de búsqueda
import { searchOrdenanzasTool, searchOrdenanzasHandler } from "./search.js";
import { searchByCategoryTool, searchByCategoryHandler } from "./search.js";
import { searchByYearRangeTool, searchByYearRangeHandler } from "./search.js";

// Imports de tools de detalle por ID
import { getOrdenanzaTool, getOrdenanzaHandler } from "./by-id.js";
import { getAnexoTool, getAnexoHandler } from "./by-id.js";

// Imports de tools por entidad
import { searchByEntityTool, searchByEntityHandler } from "./by-entity.js";

// Imports de tools de referencias
import { getReferencesTool, getReferencesHandler } from "./references.js";

// Imports de tools de categorías
import { listCategoriesTool, listCategoriesHandler } from "./categories.js";

// Imports de tools de estadísticas
import { getStatsTool, getStatsHandler } from "./stats.js";

// Imports de tools de similitud (AI)
import { similarOrdenanzasTool, similarOrdenanzasHandler } from "./similar.js";

// Imports de tools de resumen (AI)
import { summarizeTextoTool, summarizeTextoHandler } from "./summarize.js";

// Imports de tool de health check
import { healthCheckTool, healthCheckHandler } from "./health.js";

// Imports de tools de búsqueda semántica (AI)
import { semanticSearchTool, semanticSearchHandler } from "./semantic-search.js";

// Re-exportar para uso directo si se necesita
export {
  searchOrdenanzasTool, searchOrdenanzasHandler,
  searchByCategoryTool, searchByCategoryHandler,
  searchByYearRangeTool, searchByYearRangeHandler,
  getOrdenanzaTool, getOrdenanzaHandler,
  getAnexoTool, getAnexoHandler,
  searchByEntityTool, searchByEntityHandler,
  getReferencesTool, getReferencesHandler,
  listCategoriesTool, listCategoriesHandler,
  getStatsTool, getStatsHandler,
  similarOrdenanzasTool, similarOrdenanzasHandler,
  summarizeTextoTool, summarizeTextoHandler,
  healthCheckTool, healthCheckHandler,
  semanticSearchTool, semanticSearchHandler,
};

/**
 * Array con todas las herramientas disponibles (tool + handler)
 * Útil para registro masivo en el servidor MCP
 */
export const ALL_TOOLS = [
  // Búsqueda (3)
  { tool: searchOrdenanzasTool, handler: searchOrdenanzasHandler },
  { tool: searchByCategoryTool, handler: searchByCategoryHandler },
  { tool: searchByYearRangeTool, handler: searchByYearRangeHandler },

  // Detalle por ID (2)
  { tool: getOrdenanzaTool, handler: getOrdenanzaHandler },
  { tool: getAnexoTool, handler: getAnexoHandler },

  // Por entidad (1)
  { tool: searchByEntityTool, handler: searchByEntityHandler },

  // Referencias (1)
  { tool: getReferencesTool, handler: getReferencesHandler },

  // Categorías (1)
  { tool: listCategoriesTool, handler: listCategoriesHandler },

  // Estadísticas (1)
  { tool: getStatsTool, handler: getStatsHandler },

  // Similitud (1)
  { tool: similarOrdenanzasTool, handler: similarOrdenanzasHandler },

  // Resumen (1)
  { tool: summarizeTextoTool, handler: summarizeTextoHandler },

  // Health check (1)
  { tool: healthCheckTool, handler: healthCheckHandler },

  // Búsqueda semántica (1)
  { tool: semanticSearchTool, handler: semanticSearchHandler },
];
