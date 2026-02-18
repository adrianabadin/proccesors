import * as z from "zod/v4";
import {
  HealthCheckInputSchema,
  HealthCheckOutputSchema,
} from "../types.js";
import { toolLogger } from "../utils.js";
import { healthCheck, closePool } from "../db.js";

// =============================================================================
// TOOL 1: health_check
// =============================================================================

export const healthCheckTool = {
  name: "health_check",
  title: "Health Check del Servidor",
  description:
    "Verifica el estado del servidor MCP, incluyendo conectividad con la base de datos. Útil para monitoreo y debugging.",
  inputSchema: HealthCheckInputSchema,
};

export async function healthCheckHandler(
  args: z.infer<typeof HealthCheckInputSchema>,
  ctx: any
): Promise<any> {
  const log = toolLogger("health_check");

  try {
    log.info("Running health check...");

    const startTime = Date.now();

    // Verificar conexión a DB
    const dbConnected = await healthCheck();
    const uptime = Date.now() - startTime;

    const result: z.infer<typeof HealthCheckOutputSchema> = {
      status: dbConnected ? "ok" : "error",
      db: dbConnected ? "connected" : "disconnected",
      timestamp: new Date().toISOString(),
      uptime_ms: uptime,
    };

    if (dbConnected) {
      log.info("Health check passed", {
        db_status: "connected",
        uptime_ms: uptime,
      });
    } else {
      log.error("Health check failed", {
        db_status: "disconnected",
      });
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result),
        },
      ],
    };
  } catch (error) {
    log.error("Health check failed", {
      error: error instanceof Error ? error.message : String(error)
    });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: `Error en health check: ${
              error instanceof Error ? error.message : String(error)
            }`,
          }),
        },
      ],
      isError: true,
    };
  }
}
