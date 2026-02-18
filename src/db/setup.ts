import pg from "pg";
import "dotenv/config";

const pool = new pg.Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: false,
});

async function run(label: string, sql: string) {
  console.log(`  ${label}...`);
  await pool.query(sql);
}

async function main() {
  console.log("=== Database Setup ===\n");

  // ----- Extensions -----
  console.log("[1/8] Creating extensions...");
  await run("uuid-ossp", `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`);
  await run("unaccent", `CREATE EXTENSION IF NOT EXISTS "unaccent";`);
  await run("pg_trgm", `CREATE EXTENSION IF NOT EXISTS "pg_trgm";`);

  // ----- Text search configuration -----
  console.log("[2/8] Creating text search configuration...");
  await pool.query(`
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname = 'espanol'
      ) THEN
        CREATE TEXT SEARCH CONFIGURATION espanol (COPY = spanish);
        ALTER TEXT SEARCH CONFIGURATION espanol
          ALTER MAPPING FOR hword, hword_part, word
          WITH unaccent, spanish_stem;
      END IF;
    END $$;
  `);

  // ----- tsvector columns -----
  console.log("[3/8] Adding tsvector columns...");
  await pool.query(`
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ordenanzas' AND column_name = 'fts_documento'
      ) THEN
        ALTER TABLE ordenanzas ADD COLUMN fts_documento tsvector;
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'articulos' AND column_name = 'fts_articulo'
      ) THEN
        ALTER TABLE articulos ADD COLUMN fts_articulo tsvector;
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'entidades' AND column_name = 'fts_nombre'
      ) THEN
        ALTER TABLE entidades ADD COLUMN fts_nombre tsvector;
      END IF;
    END $$;
  `);

  // ----- GIN indexes for FTS and trigrams -----
  console.log("[4/8] Creating GIN indexes...");
  await pool.query(`
    CREATE INDEX IF NOT EXISTS idx_ordenanzas_fts ON ordenanzas USING GIN (fts_documento);
    CREATE INDEX IF NOT EXISTS idx_ordenanzas_palabras_clave ON ordenanzas USING GIN (palabras_clave);
    CREATE INDEX IF NOT EXISTS idx_ordenanzas_no_procesadas ON ordenanzas(procesado_ia) WHERE procesado_ia = FALSE;
    CREATE INDEX IF NOT EXISTS idx_ordenanzas_titulo_trgm ON ordenanzas USING GIN (titulo gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_articulos_fts ON articulos USING GIN (fts_articulo);
    CREATE INDEX IF NOT EXISTS idx_entidades_fts ON entidades USING GIN (fts_nombre);
    CREATE INDEX IF NOT EXISTS idx_entidades_nombre_trgm ON entidades USING GIN (nombre gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_montos_concepto_trgm ON montos USING GIN (concepto gin_trgm_ops);
  `);

  // ----- Triggers -----
  console.log("[5/8] Creating FTS triggers...");

  await pool.query(`
    CREATE OR REPLACE FUNCTION ordenanzas_fts_update() RETURNS trigger AS $$
    BEGIN
      NEW.fts_documento :=
        setweight(to_tsvector('espanol', COALESCE(NEW.titulo, '')), 'A') ||
        setweight(to_tsvector('espanol', COALESCE(NEW.resumen, '')), 'B') ||
        setweight(to_tsvector('espanol', COALESCE(NEW.seccion_visto, '') || ' ' || COALESCE(NEW.seccion_considerando, '')), 'C') ||
        setweight(to_tsvector('espanol', COALESCE(NEW.texto_completo, '')), 'D');
      NEW.updated_at := NOW();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
  `);

  await pool.query(`
    DROP TRIGGER IF EXISTS trg_ordenanzas_fts ON ordenanzas;
    CREATE TRIGGER trg_ordenanzas_fts
      BEFORE INSERT OR UPDATE OF titulo, resumen, seccion_visto, seccion_considerando, texto_completo
      ON ordenanzas
      FOR EACH ROW
      EXECUTE FUNCTION ordenanzas_fts_update();
  `);

  await pool.query(`
    CREATE OR REPLACE FUNCTION articulos_fts_update() RETURNS trigger AS $$
    BEGIN
      NEW.fts_articulo :=
        setweight(to_tsvector('espanol', COALESCE(NEW.numero_articulo, '')), 'A') ||
        setweight(to_tsvector('espanol', COALESCE(NEW.texto, '')), 'B');
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
  `);

  await pool.query(`
    DROP TRIGGER IF EXISTS trg_articulos_fts ON articulos;
    CREATE TRIGGER trg_articulos_fts
      BEFORE INSERT OR UPDATE OF numero_articulo, texto
      ON articulos
      FOR EACH ROW
      EXECUTE FUNCTION articulos_fts_update();
  `);

  await pool.query(`
    CREATE OR REPLACE FUNCTION entidades_fts_update() RETURNS trigger AS $$
    BEGIN
      NEW.fts_nombre := to_tsvector('espanol', COALESCE(NEW.nombre, ''));
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
  `);

  await pool.query(`
    DROP TRIGGER IF EXISTS trg_entidades_fts ON entidades;
    CREATE TRIGGER trg_entidades_fts
      BEFORE INSERT OR UPDATE OF nombre
      ON entidades
      FOR EACH ROW
      EXECUTE FUNCTION entidades_fts_update();
  `);

  // ----- SQL Functions -----
  console.log("[6/8] Creating SQL functions...");

  await pool.query(`
    CREATE OR REPLACE FUNCTION buscar_ordenanzas(
      p_query TEXT,
      p_limit INTEGER DEFAULT 20,
      p_solo_vigentes BOOLEAN DEFAULT FALSE
    )
    RETURNS TABLE (
      id UUID,
      numero INTEGER,
      anio INTEGER,
      titulo VARCHAR(500),
      resumen TEXT,
      estado estado_vigencia,
      rank REAL,
      headline TEXT
    ) AS $$
    DECLARE
      v_tsquery tsquery;
    BEGIN
      v_tsquery := websearch_to_tsquery('espanol', p_query);
      RETURN QUERY
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        o.resumen,
        o.estado,
        ts_rank_cd(o.fts_documento, v_tsquery, 32)::REAL AS rank,
        ts_headline('espanol', o.texto_completo, v_tsquery,
          'StartSel=<<, StopSel=>>, MaxWords=50, MinWords=20, MaxFragments=3'
        ) AS headline
      FROM ordenanzas o
      WHERE o.fts_documento @@ v_tsquery
        AND (NOT p_solo_vigentes OR o.estado IN ('vigente', 'modificada'))
      ORDER BY rank DESC
      LIMIT p_limit;
    END;
    $$ LANGUAGE plpgsql STABLE;
  `);

  await pool.query(`
    CREATE OR REPLACE FUNCTION buscar_por_entidad(
      p_nombre_entidad TEXT,
      p_tipo tipo_entidad DEFAULT NULL,
      p_limit INTEGER DEFAULT 20
    )
    RETURNS TABLE (
      ordenanza_id UUID,
      numero INTEGER,
      anio INTEGER,
      titulo VARCHAR(500),
      entidad_nombre VARCHAR(300),
      entidad_tipo tipo_entidad,
      rol rol_entidad
    ) AS $$
    BEGIN
      RETURN QUERY
      SELECT
        o.id,
        o.numero,
        o.anio,
        o.titulo,
        e.nombre,
        e.tipo,
        oe.rol
      FROM entidades e
      JOIN ordenanza_entidades oe ON oe.entidad_id = e.id
      JOIN ordenanzas o ON o.id = oe.ordenanza_id
      WHERE e.nombre ILIKE '%' || p_nombre_entidad || '%'
        AND (p_tipo IS NULL OR e.tipo = p_tipo)
      ORDER BY o.anio DESC, o.numero DESC
      LIMIT p_limit;
    END;
    $$ LANGUAGE plpgsql STABLE;
  `);

  await pool.query(`
    CREATE OR REPLACE FUNCTION arbol_vigencia(p_ordenanza_id UUID)
    RETURNS TABLE (
      direccion TEXT,
      tipo tipo_referencia,
      ordenanza_relacionada_id UUID,
      numero INTEGER,
      anio INTEGER,
      titulo VARCHAR(500),
      norma_externa TEXT,
      articulos_afectados TEXT,
      notas TEXT
    ) AS $$
    BEGIN
      RETURN QUERY
      SELECT
        'afecta_a'::TEXT,
        r.tipo,
        r.ordenanza_destino_id,
        od.numero,
        od.anio,
        od.titulo,
        CASE WHEN r.norma_externa_referencia IS NOT NULL
          THEN r.norma_externa_tipo || ' ' || r.norma_externa_referencia
          ELSE NULL
        END,
        r.articulos_afectados,
        r.notas
      FROM referencias_normativas r
      LEFT JOIN ordenanzas od ON od.id = r.ordenanza_destino_id
      WHERE r.ordenanza_origen_id = p_ordenanza_id;

      RETURN QUERY
      SELECT
        'afectada_por'::TEXT,
        r.tipo,
        r.ordenanza_origen_id,
        oo.numero,
        oo.anio,
        oo.titulo,
        NULL::TEXT,
        r.articulos_afectados,
        r.notas
      FROM referencias_normativas r
      JOIN ordenanzas oo ON oo.id = r.ordenanza_origen_id
      WHERE r.ordenanza_destino_id = p_ordenanza_id;
    END;
    $$ LANGUAGE plpgsql STABLE;
  `);

  // ----- Seed categories -----
  console.log("[7/8] Seeding categories...");

  // Check if categories already exist
  const { rows } = await pool.query("SELECT count(*)::int AS cnt FROM categorias");
  if (rows[0].cnt > 0) {
    console.log(`  Categories already seeded (${rows[0].cnt} rows), skipping.`);
  } else {
    // Parent categories
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion) VALUES
      ('Presupuesto y Hacienda', 'presupuesto-hacienda', 'Presupuesto general, calculo de recursos, ordenanza complementaria, modificaciones presupuestarias'),
      ('Tasas, Tarifas y Tributos', 'tasas-tarifas-tributos', 'Tasas municipales, tarifas de servicios, regimen impositivo, exenciones fiscales'),
      ('Personal Municipal', 'personal-municipal', 'Escalas salariales, bonificaciones, estatuto del empleado, concursos, designaciones'),
      ('Obras Publicas e Infraestructura', 'obras-publicas', 'Obras viales, pavimentacion, infraestructura urbana, licitaciones de obra'),
      ('Urbanismo y Uso del Suelo', 'urbanismo-suelo', 'Codigo de edificacion, zonificacion, loteos, subdivisiones, habilitaciones, vivienda'),
      ('Servicios Publicos', 'servicios-publicos', 'Alumbrado, saneamiento, recoleccion de residuos, agua, cloacas'),
      ('Salud Publica', 'salud-publica', 'Emergencias sanitarias, regulaciones bromatologicas, habilitaciones sanitarias'),
      ('Educacion, Ciencia y Tecnologia', 'educacion-ciencia', 'Subsidios educativos, tecnologia, modernizacion administrativa, gobierno digital'),
      ('Cultura y Patrimonio', 'cultura-patrimonio', 'Patrimonio cultural, declaraciones de interes, actos conmemorativos, eventos'),
      ('Contratos y Convenios', 'contratos-convenios', 'Licitaciones, permutas, locaciones, compras, contratacion de servicios'),
      ('Transito y Transporte', 'transito-transporte', 'Regulacion vial, estacionamiento, transporte publico, licencias'),
      ('Seguridad y Orden Publico', 'seguridad-orden-publico', 'Regulaciones de seguridad, defensa civil, emergencias'),
      ('Desarrollo Economico y Produccion', 'desarrollo-economico', 'Promocion industrial, fomento agropecuario, regimenes de incentivo, comercio'),
      ('Medio Ambiente', 'medio-ambiente', 'Gestion ambiental, espacios verdes, arbolado, sustentabilidad'),
      ('Accion Social y Derechos', 'accion-social-derechos', 'Politicas sociales, ninez, discapacidad, genero, adultos mayores, vivienda social'),
      ('Deportes y Recreacion', 'deportes-recreacion', 'Clubes, eventos deportivos, espacios recreativos, subsidios deportivos'),
      ('Empleo y Relaciones Laborales', 'empleo-laboral', 'Regulaciones laborales locales, cooperativas de trabajo, economia social'),
      ('Procedimientos y Administracion', 'procedimientos-admin', 'Adhesiones a leyes, convalidaciones de decretos, reglamentos internos, creacion de organismos');
    `);

    // Subcategories - Presupuesto y Hacienda
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'presupuesto-hacienda')
      FROM (VALUES
        ('Presupuesto General de Gastos y Recursos', 'presupuesto-general', 'Aprobacion del presupuesto anual'),
        ('Modificaciones Presupuestarias', 'modif-presupuestarias', 'Ampliaciones, transferencias de partidas'),
        ('Planes de Pago y Regularizacion', 'planes-pago', 'Moratorias, facilidades de pago, regularizacion de deudas'),
        ('Deuda Municipal', 'deuda-municipal', 'Reconocimiento de deudas, emprestitos')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Tasas, Tarifas y Tributos
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'tasas-tarifas-tributos')
      FROM (VALUES
        ('Tasas por Servicios Urbanos', 'tasas-serv-urbanos', 'Alumbrado, barrido, limpieza'),
        ('Tasas por Servicios Sanitarios', 'tasas-serv-sanitarios', 'Agua, cloacas'),
        ('Tasa de Seguridad e Higiene', 'tasa-seg-higiene', 'Inspeccion comercial'),
        ('Derecho de Cementerio', 'derecho-cementerio', 'Tasas cementeriales'),
        ('Tarifas Electricas', 'tarifas-electricas', 'Cuadros tarifarios de energia'),
        ('Exenciones y Beneficios Fiscales', 'exenciones-fiscales', 'Condonaciones, exenciones, descuentos tributarios'),
        ('Red Vial Municipal', 'red-vial-tasa', 'Tasa de conservacion y mejorado de caminos')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Personal Municipal
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'personal-municipal')
      FROM (VALUES
        ('Escalas Salariales', 'escalas-salariales', 'Sueldos basicos, bonificaciones, adicionales'),
        ('Estatuto del Personal', 'estatuto-personal', 'Regimen de empleo publico municipal'),
        ('Anticipos y Pagos Extraordinarios', 'anticipos-pagos', 'Anticipos salariales, bonos extraordinarios')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Obras Publicas
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'obras-publicas')
      FROM (VALUES
        ('Pavimentacion y Vialidad', 'pavimentacion-vialidad', 'Obras de pavimento, cordon cuneta, ciclovias'),
        ('Infraestructura Hidraulica', 'infra-hidraulica', 'Desagues pluviales, obras sanitarias'),
        ('Edificios Publicos', 'edificios-publicos', 'Construccion y remodelacion de edificios municipales')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Contratos y Convenios
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'contratos-convenios')
      FROM (VALUES
        ('Licitaciones y Compras', 'licitaciones-compras', 'Licitaciones publicas, privadas, contrataciones directas'),
        ('Permutas y Ventas de Inmuebles', 'permutas-ventas', 'Enajenacion de bienes municipales'),
        ('Locaciones y Alquileres', 'locaciones-alquileres', 'Contratos de alquiler de inmuebles'),
        ('Convenios Interinstitucionales', 'convenios-inter', 'Convenios con provincia, nacion u otros organismos')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Educacion, Ciencia y Tecnologia
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'educacion-ciencia')
      FROM (VALUES
        ('Educacion Formal y Cooperadoras', 'educacion-formal', 'Escuelas, cooperadoras escolares, subsidios educativos'),
        ('Ciencia y Tecnologia', 'ciencia-tecnologia', 'Investigacion, innovacion, parques tecnologicos'),
        ('Modernizacion y Gobierno Digital', 'gobierno-digital', 'Sistemas informaticos, RAFAM, expediente electronico')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Accion Social y Derechos
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'accion-social-derechos')
      FROM (VALUES
        ('Ninez y Adolescencia', 'ninez-adolescencia', 'Proteccion de derechos del nino, programas de infancia'),
        ('Discapacidad y Accesibilidad', 'discapacidad-accesibilidad', 'Inclusion, accesibilidad urbana, transporte adaptado'),
        ('Genero y Diversidad', 'genero-diversidad', 'Politicas de genero, violencia de genero, diversidad sexual'),
        ('Adultos Mayores', 'adultos-mayores', 'Programas para la tercera edad, geriatricos, jubilados'),
        ('Vivienda Social', 'vivienda-social', 'Planes de vivienda, lotes sociales, regularizacion dominial'),
        ('Programas y Subsidios Sociales', 'programas-subsidios', 'Asistencia directa, becas, comedores, emergencia social')
      ) AS sub(nombre, slug, descripcion);
    `);

    // Subcategories - Procedimientos y Administracion
    await pool.query(`
      INSERT INTO categorias (nombre, slug, descripcion, parent_id)
      SELECT nombre, slug, descripcion, (SELECT id FROM categorias WHERE slug = 'procedimientos-admin')
      FROM (VALUES
        ('Adhesiones a Leyes', 'adhesiones-leyes', 'Adhesion a leyes provinciales o nacionales'),
        ('Convalidacion de Decretos', 'convalidacion-decretos', 'Ratificacion de decretos del ejecutivo'),
        ('Creacion de Organismos', 'creacion-organismos', 'Creacion de direcciones, secretarias, comisiones'),
        ('Declaraciones de Interes', 'declaraciones-interes', 'Declaraciones de interes municipal, provincial')
      ) AS sub(nombre, slug, descripcion);
    `);

    const { rows: countRows } = await pool.query("SELECT count(*)::int AS cnt FROM categorias");
    console.log(`  Seeded ${countRows[0].cnt} categories.`);
  }

  // ----- Materialized view -----
  console.log("[8/8] Creating materialized view...");
  await pool.query(`
    DROP MATERIALIZED VIEW IF EXISTS mv_estadisticas_categorias;
    CREATE MATERIALIZED VIEW mv_estadisticas_categorias AS
    SELECT
      c.id AS categoria_id,
      c.nombre AS categoria,
      cp.nombre AS categoria_padre,
      o.anio,
      COUNT(*) AS cantidad,
      ARRAY_AGG(o.numero ORDER BY o.numero) AS numeros_ordenanza
    FROM ordenanza_categorias oc
    JOIN ordenanzas o ON o.id = oc.ordenanza_id
    JOIN categorias c ON c.id = oc.categoria_id
    LEFT JOIN categorias cp ON cp.id = c.parent_id
    GROUP BY c.id, c.nombre, cp.nombre, o.anio
    ORDER BY o.anio DESC, cantidad DESC;
  `);

  await pool.query(`
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_estadisticas
    ON mv_estadisticas_categorias(categoria_id, anio);
  `);

  console.log("\n=== Setup complete! ===");
  await pool.end();
}

main().catch((err) => {
  console.error("Setup failed:", err);
  pool.end();
  process.exit(1);
});
