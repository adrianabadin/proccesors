import {
  pgTable,
  uuid,
  integer,
  varchar,
  text,
  boolean,
  real,
  numeric,
  serial,
  smallint,
  date,
  timestamp,
  pgEnum,
  index,
  uniqueIndex,
  primaryKey,
  check,
} from "drizzle-orm/pg-core";
import { relations, sql } from "drizzle-orm";

// =============================================================================
// ENUMS
// =============================================================================

export const estadoVigencia = pgEnum("estado_vigencia", [
  "vigente",
  "modificada",
  "derogada_total",
  "derogada_parcial",
  "sin_determinar",
]);

export const tipoEntidad = pgEnum("tipo_entidad", [
  "persona_fisica",
  "empresa",
  "organismo_municipal",
  "organismo_provincial",
  "organismo_nacional",
  "institucion_educativa",
  "club_asociacion",
  "otro",
]);

export const rolEntidad = pgEnum("rol_entidad", [
  "beneficiario",
  "contratista",
  "contraparte_contractual",
  "firmante",
  "solicitante",
  "mencionado",
  "sancionado",
  "otro",
]);

export const tipoReferencia = pgEnum("tipo_referencia", [
  "modifica",
  "deroga_total",
  "deroga_parcial",
  "complementa",
  "reglamenta",
  "adhiere",
  "prorroga",
  "convalida",
  "cita",
  "sustituye",
]);

// =============================================================================
// TABLA: categorias
// =============================================================================

export const categorias = pgTable(
  "categorias",
  {
    id: serial("id").primaryKey(),
    nombre: varchar("nombre", { length: 120 }).notNull(),
    slug: varchar("slug", { length: 120 }).notNull().unique(),
    descripcion: text("descripcion"),
    parentId: integer("parent_id").references((): any => categorias.id, {
      onDelete: "set null",
    }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_categorias_parent").on(table.parentId)],
);

// =============================================================================
// TABLA: ordenanzas
// =============================================================================

export const ordenanzas = pgTable(
  "ordenanzas",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    numero: integer("numero").notNull(),
    anio: integer("anio").notNull(),

    // Texto original y secciones
    titulo: varchar("titulo", { length: 500 }).notNull(),
    extracto: text("extracto"),
    seccionVisto: text("seccion_visto"),
    seccionConsiderando: text("seccion_considerando"),
    textoCompleto: text("texto_completo").notNull(),

    // Metadatos extraidos por Claude API
    resumen: text("resumen"),
    palabrasClave: text("palabras_clave")
      .array()
      .default(sql`'{}'`),
    expediente: varchar("expediente", { length: 100 }),
    fechaSancion: date("fecha_sancion"),
    estado: estadoVigencia("estado").notNull().default("sin_determinar"),
    notasVigencia: text("notas_vigencia"),

    // Montos economicos principales
    montoPrincipal: numeric("monto_principal", { precision: 18, scale: 2 }),
    moneda: varchar("moneda", { length: 10 }),

    // fts_documento: tsvector - managed by SQL trigger, skipped here

    // URL fuente
    urlFuente: varchar("url_fuente", { length: 500 }),

    // Pipeline tracking
    procesadoIa: boolean("procesado_ia").notNull().default(false),
    fechaProcesadoIa: timestamp("fecha_procesado_ia", { withTimezone: true }),
    versionPrompt: varchar("version_prompt", { length: 50 }),

    // Timestamps
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_ordenanza_numero_anio").on(table.numero, table.anio),
    index("idx_ordenanzas_anio").on(table.anio),
    index("idx_ordenanzas_estado").on(table.estado),
    index("idx_ordenanzas_fecha_sancion").on(table.fechaSancion),
    check(
      "ck_anio_valido",
      sql`${table.anio} >= 1983 AND ${table.anio} <= 2100`,
    ),
    check("ck_numero_positivo", sql`${table.numero} > 0`),
  ],
);

// =============================================================================
// TABLA: articulos
// =============================================================================

export const articulos = pgTable(
  "articulos",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    numeroArticulo: varchar("numero_articulo", { length: 20 }).notNull(),
    orden: smallint("orden").notNull(),
    texto: text("texto").notNull(),
    resumen: text("resumen"),
    estado: estadoVigencia("estado").notNull().default("sin_determinar"),

    // fts_articulo: tsvector - managed by SQL trigger, skipped here

    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("uq_articulo_ordenanza").on(
      table.ordenanzaId,
      table.numeroArticulo,
    ),
    index("idx_articulos_ordenanza").on(table.ordenanzaId),
    index("idx_articulos_estado").on(table.estado),
  ],
);

// =============================================================================
// TABLA: ordenanza_categorias (many-to-many)
// =============================================================================

export const ordenanzaCategorias = pgTable(
  "ordenanza_categorias",
  {
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    categoriaId: integer("categoria_id")
      .notNull()
      .references(() => categorias.id, { onDelete: "cascade" }),
    relevancia: real("relevancia").default(1.0),
  },
  (table) => [
    primaryKey({ columns: [table.ordenanzaId, table.categoriaId] }),
    index("idx_ord_cat_categoria").on(table.categoriaId),
  ],
);

// =============================================================================
// TABLA: entidades
// =============================================================================

export const entidades = pgTable(
  "entidades",
  {
    id: serial("id").primaryKey(),
    nombre: varchar("nombre", { length: 300 }).notNull(),
    tipo: tipoEntidad("tipo").notNull(),
    cuit: varchar("cuit", { length: 20 }).unique(),
    dni: varchar("dni", { length: 20 }),
    notas: text("notas"),

    // fts_nombre: tsvector - managed by SQL trigger, skipped here

    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_entidades_tipo").on(table.tipo)],
);

// =============================================================================
// TABLA: ordenanza_entidades (many-to-many with context)
// =============================================================================

export const ordenanzaEntidades = pgTable(
  "ordenanza_entidades",
  {
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    entidadId: integer("entidad_id")
      .notNull()
      .references(() => entidades.id, { onDelete: "cascade" }),
    rol: rolEntidad("rol").notNull().default("mencionado"),
    contexto: text("contexto"),
  },
  (table) => [
    primaryKey({
      columns: [table.ordenanzaId, table.entidadId, table.rol],
    }),
    index("idx_ord_ent_entidad").on(table.entidadId),
    index("idx_ord_ent_rol").on(table.rol),
  ],
);

// =============================================================================
// TABLA: referencias_normativas
// =============================================================================

export const referenciasNormativas = pgTable(
  "referencias_normativas",
  {
    id: serial("id").primaryKey(),
    ordenanzaOrigenId: uuid("ordenanza_origen_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    ordenanzaDestinoId: uuid("ordenanza_destino_id").references(
      () => ordenanzas.id,
      { onDelete: "set null" },
    ),
    normaExternaTipo: varchar("norma_externa_tipo", { length: 80 }),
    normaExternaReferencia: varchar("norma_externa_referencia", { length: 200 }),
    normaExternaDescripcion: text("norma_externa_descripcion"),
    tipo: tipoReferencia("tipo").notNull(),
    articulosAfectados: text("articulos_afectados"),
    notas: text("notas"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("idx_ref_origen").on(table.ordenanzaOrigenId),
    index("idx_ref_destino").on(table.ordenanzaDestinoId),
    index("idx_ref_tipo").on(table.tipo),
    index("idx_ref_norma_externa").on(
      table.normaExternaTipo,
      table.normaExternaReferencia,
    ),
    check(
      "ck_destino_presente",
      sql`${table.ordenanzaDestinoId} IS NOT NULL OR ${table.normaExternaReferencia} IS NOT NULL`,
    ),
  ],
);

// =============================================================================
// TABLA: montos
// =============================================================================

export const montos = pgTable(
  "montos",
  {
    id: serial("id").primaryKey(),
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    concepto: varchar("concepto", { length: 300 }).notNull(),
    valor: numeric("valor", { precision: 18, scale: 2 }).notNull(),
    moneda: varchar("moneda", { length: 10 }).notNull().default("ARS"),
    unidad: varchar("unidad", { length: 50 }),
    esPorcentaje: boolean("es_porcentaje").default(false),
    notas: text("notas"),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_montos_ordenanza").on(table.ordenanzaId)],
);

// =============================================================================
// TABLA: anexos
// =============================================================================

export const anexos = pgTable(
  "anexos",
  {
    id: uuid("id").primaryKey().defaultRandom(),
    ordenanzaId: uuid("ordenanza_id")
      .notNull()
      .references(() => ordenanzas.id, { onDelete: "cascade" }),
    numero: varchar("numero", { length: 20 }).notNull(),
    titulo: varchar("titulo", { length: 500 }),
    contenido: text("contenido"),
    tipo: varchar("tipo", { length: 100 }),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [index("idx_anexos_ordenanza").on(table.ordenanzaId)],
);

// =============================================================================
// RELATIONS
// =============================================================================

export const categoriasRelations = relations(categorias, ({ one, many }) => ({
  parent: one(categorias, {
    fields: [categorias.parentId],
    references: [categorias.id],
    relationName: "categoriasParent",
  }),
  children: many(categorias, { relationName: "categoriasParent" }),
  ordenanzaCategorias: many(ordenanzaCategorias),
}));

export const ordenanzasRelations = relations(ordenanzas, ({ many }) => ({
  articulos: many(articulos),
  ordenanzaCategorias: many(ordenanzaCategorias),
  ordenanzaEntidades: many(ordenanzaEntidades),
  referenciasOrigen: many(referenciasNormativas, {
    relationName: "refOrigen",
  }),
  referenciasDestino: many(referenciasNormativas, {
    relationName: "refDestino",
  }),
  montos: many(montos),
  anexos: many(anexos),
}));

export const articulosRelations = relations(articulos, ({ one }) => ({
  ordenanza: one(ordenanzas, {
    fields: [articulos.ordenanzaId],
    references: [ordenanzas.id],
  }),
}));

export const ordenanzaCategoriasRelations = relations(
  ordenanzaCategorias,
  ({ one }) => ({
    ordenanza: one(ordenanzas, {
      fields: [ordenanzaCategorias.ordenanzaId],
      references: [ordenanzas.id],
    }),
    categoria: one(categorias, {
      fields: [ordenanzaCategorias.categoriaId],
      references: [categorias.id],
    }),
  }),
);

export const entidadesRelations = relations(entidades, ({ many }) => ({
  ordenanzaEntidades: many(ordenanzaEntidades),
}));

export const ordenanzaEntidadesRelations = relations(
  ordenanzaEntidades,
  ({ one }) => ({
    ordenanza: one(ordenanzas, {
      fields: [ordenanzaEntidades.ordenanzaId],
      references: [ordenanzas.id],
    }),
    entidad: one(entidades, {
      fields: [ordenanzaEntidades.entidadId],
      references: [entidades.id],
    }),
  }),
);

export const referenciasNormativasRelations = relations(
  referenciasNormativas,
  ({ one }) => ({
    ordenanzaOrigen: one(ordenanzas, {
      fields: [referenciasNormativas.ordenanzaOrigenId],
      references: [ordenanzas.id],
      relationName: "refOrigen",
    }),
    ordenanzaDestino: one(ordenanzas, {
      fields: [referenciasNormativas.ordenanzaDestinoId],
      references: [ordenanzas.id],
      relationName: "refDestino",
    }),
  }),
);

export const montosRelations = relations(montos, ({ one }) => ({
  ordenanza: one(ordenanzas, {
    fields: [montos.ordenanzaId],
    references: [ordenanzas.id],
  }),
}));

export const anexosRelations = relations(anexos, ({ one }) => ({
  ordenanza: one(ordenanzas, {
    fields: [anexos.ordenanzaId],
    references: [ordenanzas.id],
  }),
}));
