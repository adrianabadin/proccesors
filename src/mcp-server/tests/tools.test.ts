/**
 * Tests unitarios para las herramientas del servidor MCP
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { Server, StdioServerTransport } from "@modelcontextprotocol/sdk/server";
import { logger } from "../logger.js";
import {
  searchOrdenanzasTool,
  searchByCategoryTool,
  searchByYearRangeTool,
} from "../tools/search.js";
import {
  getOrdenanzaTool,
  getAnexoTool,
} from "../tools/by-id.js";
import { searchByEntityTool } from "../tools/by-entity.js";
import { getReferencesTool } from "../tools/references.js";
import { listCategoriesTool } from "../tools/categories.js";
import { getStatsTool } from "../tools/stats.js";
import { similarOrdenanzasTool } from "../tools/similar.js";
import { summarizeTextoTool } from "../tools/summarize.js";
import { healthCheckTool } from "../tools/health.js";

// Mock de base de datos
const mockDB = {
  query: vi.fn(),
};

describe("MCP Server Tools", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("search_ordenanzas", () => {
    it("debería buscar ordenanzas con query FTS", async () => {
      mockDB.query.mockResolvedValue([
        { id: "test-id-1", titulo: "Ordenanza Test 1" },
        { id: "test-id-2", titulo: "Ordenanza Test 2" },
      ]);

      const result = await searchOrdenanzasTool.handler({ query: "test" }, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.results).toHaveLength(2);
    });

    it("debería manejar errores de búsqueda", async () => {
      mockDB.query.mockRejectedValue(new Error("DB error"));

      const result = await searchOrdenanzasTool.handler({ query: "test" }, {});

      expect(result.isError).toBe(true);
      const data = JSON.parse(result.content[0].text);
      expect(data.error).toContain("Error al buscar ordenanzas");
    });
  });

  describe("search_by_category", () => {
    it("debería filtrar por categoría", async () => {
      mockDB.query.mockResolvedValue([
        { id: "test-id", titulo: "Test", slug: "test", nombre: "Test" },
      ]);

      const result = await searchByCategoryTool.handler({ slug: "test" }, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.results).toHaveLength(1);
      expect(data.category).toBe("test");
    });
  });

  describe("search_by_year_range", () => {
    it("debería validar rango de años", async () => {
      mockDB.query.mockResolvedValue([]);

      const result = await searchByYearRangeTool.handler(
        { desde: 2000, hasta: 2020 },
        {}
      );

      expect(result.isError).toBe(true);
      const data = JSON.parse(result.content[0].text);
      expect(data.error).toContain("menor o igual");
    });
  });

  describe("get_ordenanza", () => {
    it("debería obtener ordenanza completa", async () => {
      const ordenanzaRow = {
        id: "test-id",
        numero: 123,
        anio: 2024,
        titulo: "Ordenanza Test",
        texto_completo: "Texto completo",
      };

      mockDB.query.mockResolvedValueOnce([ordenanzaRow]);
      mockDB.query.mockResolvedValueOnce([
        { numero_articulo: "1", texto: "Artículo 1" },
        { nombre: "Entidad Test", tipo: "empresa", rol: "mencionado" },
        { nombre: "Categoria Test", slug: "test", relevancia: 0.8 },
        [],
        [],
        [],
        [{ nombre: "Test", slug: "test" }],
        [{ concepto: "Monto 1", valor: 100 }],
        [{ numero: "I", titulo: "Anexo I" }],
      ]);

      const result = await getOrdenanzaTool.handler({ id: "test-id" }, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.id).toBe("test-id");
      expect(data.articulos).toHaveLength(1);
      expect(data.entidades).toHaveLength(1);
      expect(data.categorias).toHaveLength(1);
    });

    it("debería retornar error si no existe", async () => {
      mockDB.query.mockResolvedValueOnce([]);

      const result = await getOrdenanzaTool.handler({ id: "test-id" }, {});

      expect(result.isError).toBe(true);
      const data = JSON.parse(result.content[0].text);
      expect(data.error).toContain("No se encontró ordenanza");
    });
  });

  describe("search_by_entity", () => {
    it("debería buscar por nombre de entidad", async () => {
      mockDB.query.mockResolvedValue([
        {
          id: "test-id",
          numero: 456,
          anio: 2024,
          titulo: "Ordenanza",
          entidad_nombre: "Municipio de Saladillo",
          entidad_tipo: "organismo_municipal",
          entidad_rol: "mencionado",
        },
      ]);

      const result = await searchByEntityTool.handler(
        { nombre: "Saladillo" },
        {}
      );

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.results).toHaveLength(1);
      expect(data.results[0].entidad_nombre).toBe("Municipio de Saladillo");
    });
  });

  describe("get_references", () => {
    it("debería obtener referencias normativas", async () => {
      mockDB.query.mockResolvedValue([
        {
          id: "ref-id-1",
          direccion: "afecta_a",
          tipo: "modifica",
          ordenanza_relacionada_id: "test-id-2",
          numero: 123,
          anio: 2023,
        },
      ]);

      const result = await getReferencesTool.handler({ ordenanza_id: "test-id-1" }, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.references).toHaveLength(1);
      expect(data.references[0].direccion).toBe("afecta_a");
    });
  });

  describe("list_categories", () => {
    it("debería listar todas las categorías", async () => {
      mockDB.query.mockResolvedValue([
        { id: 1, nombre: "Presupuesto", slug: "presupuesto-hacienda" },
        { id: 2, nombre: "Salud", slug: "salud-publica" },
      ]);

      const result = await listCategoriesTool.handler({}, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.categories).toHaveLength(2);
    });
  });

  describe("get_stats", () => {
    it("debería calcular estadísticas", async () => {
      mockDB.query
        .mockResolvedValueOnce([{ total: "100" }])
        .mockResolvedValueOnce([{ procesadas: "50" }])
        .mockResolvedValueOnce([]);

      const result = await getStatsTool.handler({}, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.total).toBe(100);
      expect(data.procesadas).toBe(50);
      expect(data.pendientes).toBe(50);
    });
  });

  describe("similar_ordenanzas (sin embeddings)", () => {
    it("debería fallar si no hay embeddings", async () => {
      mockDB.query.mockRejectedValueOnce(new Error("DB error"));

      const result = await similarOrdenanzasTool.handler(
        { ordenanza_id: "test-id" },
        {}
      );

      expect(result.isError).toBe(true);
      const data = JSON.parse(result.content[0].text);
      expect(data.error).toContain("Error al obtener embeddings");
    });
  });

  describe("summarize_texto (sin LLM)", () => {
    it("debería fallar si LLM no configurado", async () => {
      const result = await summarizeTextoTool.handler(
        { texto: "Texto de prueba" },
        {}
      );

      expect(result.isError).toBe(true);
      const data = JSON.parse(result.content[0].text);
      expect(data.error).toContain("Cliente LLM no configurado");
    });
  });

  describe("health_check", () => {
    it("debería verificar conectividad con DB", async () => {
      mockDB.query.mockResolvedValueOnce([{ status: "ok" }]);

      const result = await healthCheckTool.handler({}, {});

      expect(result.content).toBeDefined();
      const data = JSON.parse(result.content[0].text);
      expect(data.status).toBe("ok");
      expect(data.db).toBe("connected");
    });
  });
});
