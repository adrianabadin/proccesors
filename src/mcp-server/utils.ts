import { logger } from "./logger.js";

/**
 * Wrapper para logging de herramientas MCP
 * Agrega contexto automático de tool name
 */
export function toolLogger(toolName: string) {
  return {
    info: (msg: string, data?: any) =>
      logger.info({ tool: toolName, ...data }, msg),
    debug: (msg: string, data?: any) =>
      logger.debug({ tool: toolName, ...data }, msg),
    error: (msg: string, data?: any) =>
      logger.error({ tool: toolName, ...data }, msg),
    warn: (msg: string, data?: any) =>
      logger.warn({ tool: toolName, ...data }, msg),
  };
}

// Simplified ToolResult type for internal use
type ToolResult = {
  content: Array<{
    type: "text" | "image" | "audio" | "resource";
    text?: string;
    uri?: string;
    data?: string;
    mimeType?: string;
  }>;
  isError?: boolean;
  _meta?: {
    progressToken?: string | number;
    [key: string]: any;
  };
};

/**
 * Generador de mensajes de error amigables para el usuario
 */
export function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Error desconocido al procesar la solicitud";
}

/**
 * Crea un resultado de error MCP estandarizado
 */
export function toolError(
  toolName: string,
  error: unknown,
): ToolResult {
  const msg = errorMessage(error);

  logger.error(
    { tool: toolName, error: msg },
    "Tool execution failed"
  );

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          error: msg,
          tool: toolName,
        }),
      },
    ],
    isError: true,
  };
}

/**
 * Timeout handler para herramientas de larga duración
 */
const TOOL_TIMEOUT_MS = 30_000; // 30 segundos

export function withTimeout<T>(promise: Promise<T>, toolName: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(
        () =>
          reject(
            new Error(
              `Timeout: ${toolName} excedió el tiempo límite de 30s`
            )
          ),
        TOOL_TIMEOUT_MS
      )
    ),
  ]);
}

/**
 * Calcula cosine similarity entre dos vectores
 * Utilizado para búsqueda semántica cuando pgvector no está disponible
 */
export function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error("Vectors must have the same length");
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  const denom = Math.sqrt(normA) * Math.sqrt(normB);
  if (denom === 0) return 0;
  const similarity = dotProduct / denom;
  return similarity;
}

/**
 * Parsea un vector almacenado como JSON string a array de números
 */
export function parseVector(vectorStr: string): number[] {
  try {
    const parsed = JSON.parse(vectorStr);
    if (!Array.isArray(parsed)) {
      throw new Error("Vector is not an array");
    }
    return parsed;
  } catch (error) {
    logger.error(
      { vectorStr, error },
      "Failed to parse vector from string"
    );
    throw new Error(`Invalid vector format: ${vectorStr}`);
  }
}

/**
 * Formatea un array de números a JSON string
 */
export function formatVector(vector: number[]): string {
  return JSON.stringify(vector);
}

/**
 * Hash simple para identificar strings (usado para cache keys)
 */
export function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash.toString(36);
}

/**
 * Trunca texto con indicador de truncamiento
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.slice(0, maxLength - 3) + "...";
}
