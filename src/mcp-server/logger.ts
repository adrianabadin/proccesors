import pino from "pino";
import "dotenv/config";

/**
 * Configuración de logging para MCP Server
 * 
 * Modes:
 * - production: JSON format, no colors
 * - development: pretty format with colors
 */

const isVerbose = process.env.VERBOSE === "true" || process.env.NODE_ENV === "development";
const logLevel = process.env.LOG_LEVEL || "info";

export const logger = pino({
  level: logLevel,
  formatters: {
    level(label: string) {
      return { level: label };
    },
  },
  transport: isVerbose
    ? {
        target: "pino-pretty",
        options: {
          colorize: true,
          translateTime: "SYS:standard",
          singleLine: false,
        },
      }
    : undefined,
});

/**
 * Wrapper para logging de herramientas MCP
 * Agrega contexto automático de tool name
 * 
 * @param toolName - Nombre de la herramienta
 * @returns Objeto con métodos info, debug, error, warn que aceptan (mensaje, datos?)
 */
export function toolLogger(toolName: string) {
  return {
    info: (msgOrData: string | object, logData?: any) => {
      const msg = typeof msgOrData === "string" ? msgOrData : "";
      const data = typeof msgOrData === "object" ? msgOrData : logData;
      logger.info({ tool: toolName, ...data }, msg);
    },
    debug: (msgOrData: string | object, logData?: any) => {
      const msg = typeof msgOrData === "string" ? msgOrData : "";
      const data = typeof msgOrData === "object" ? msgOrData : logData;
      logger.debug({ tool: toolName, ...data }, msg);
    },
    error: (msgOrData: string | object, logData?: any) => {
      const msg = typeof msgOrData === "string" ? msgOrData : "";
      const data = typeof msgOrData === "object" ? msgOrData : logData;
      logger.error({ tool: toolName, ...data }, msg);
    },
    warn: (msgOrData: string | object, logData?: any) => {
      const msg = typeof msgOrData === "string" ? msgOrData : "";
      const data = typeof msgOrData === "object" ? msgOrData : logData;
      logger.warn({ tool: toolName, ...data }, msg);
    },
  };
}
