"""Fixtures para la suite de pruebas de SIBOM MCP."""
import sqlite3
import struct
from pathlib import Path
import pytest
from sibom_mcp.db import init_index_db


def create_fake_vector(dim: int = 384, val: float = 0.05) -> bytes:
    """Crea un vector BLOB float32 para tests."""
    return struct.pack(f"{dim}f", *([val] * dim))


@pytest.fixture
def test_env(tmp_path: Path):
    """Crea un ambiente de pruebas con base SQLite fuente y base de índice derivado."""
    db_file = tmp_path / "test_sibom.db"
    index_file = tmp_path / "test_index.db"
    anexos_dir = tmp_path / "anexos"
    anexos_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()

    # 1. Esquema idéntico a sibom.db
    cur.executescript("""
    PRAGMA journal_mode = WAL;

    CREATE TABLE normas (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo                    TEXT NOT NULL CHECK(tipo IN ('ordenanza', 'decreto')),
        numero                  INTEGER,
        anio                    INTEGER,
        numero_sibom            TEXT,
        fecha                   TEXT,
        boletin                 INTEGER,
        boletin_id              INTEGER,
        contenido_id            INTEGER UNIQUE NOT NULL,
        version                 TEXT NOT NULL CHECK(version IN ('completa', 'extractada')),
        titulo                  TEXT NOT NULL,
        seccion_visto           TEXT,
        seccion_considerando    TEXT,
        texto_completo          TEXT NOT NULL,
        estado                  TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificada', 'derogada_total', 'derogada_parcial', 'sin_determinar')),
        notas_vigencia          TEXT,
        summary                 TEXT,
        summary_trata           TEXT,
        summary_resuelve        TEXT,
        summary_depende         TEXT,
        embedding_summary       BLOB,
        embedding_texto         BLOB,
        tambien_en              TEXT,
        url                     TEXT NOT NULL,
        archivo_md              TEXT NOT NULL,
        procesado_llm           INTEGER NOT NULL DEFAULT 0,
        fecha_procesado_llm     TEXT,
        created_at              TEXT DEFAULT (datetime('now', 'localtime')),
        codigo_localidad        INTEGER DEFAULT 108,
        localidad               TEXT DEFAULT 'Saladillo'
    );

    CREATE TABLE articulos (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        norma_id                INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
        numero_articulo         TEXT NOT NULL,
        orden                   INTEGER NOT NULL,
        texto                   TEXT NOT NULL,
        resumen                 TEXT,
        estado                  TEXT NOT NULL DEFAULT 'vigente' CHECK(estado IN ('vigente', 'modificado', 'derogado', 'sin_determinar')),
        modificado_por_norma_id INTEGER REFERENCES normas(id) ON DELETE SET NULL,
        created_at              TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(norma_id, numero_articulo)
    );

    CREATE TABLE referencias_normativas (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        norma_origen_id         INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
        norma_destino_id        INTEGER REFERENCES normas(id) ON DELETE SET NULL,
        destino_tipo            TEXT NOT NULL,
        destino_numero          INTEGER,
        destino_anio            INTEGER,
        destino_referencia      TEXT,
        tipo_relacion           TEXT NOT NULL,
        articulos_afectados     TEXT,
        texto_cita              TEXT,
        notas                   TEXT,
        created_at              TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE anexos (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        norma_id                INTEGER NOT NULL REFERENCES normas(id) ON DELETE CASCADE,
        nombre                  TEXT NOT NULL,
        archivo_pdf             TEXT,
        url                     TEXT NOT NULL,
        created_at              TEXT DEFAULT (datetime('now', 'localtime'))
    );

    CREATE VIRTUAL TABLE normas_fts USING fts5(
        titulo,
        summary,
        texto_completo,
        seccion_visto,
        seccion_considerando,
        content='normas',
        content_rowid='id'
    );

    CREATE TRIGGER normas_ai AFTER INSERT ON normas BEGIN
        INSERT INTO normas_fts(rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
        VALUES (new.id, new.titulo, new.summary, new.texto_completo, new.seccion_visto, new.seccion_considerando);
    END;

    CREATE TRIGGER normas_ad AFTER DELETE ON normas BEGIN
        INSERT INTO normas_fts(normas_fts, rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
        VALUES('delete', old.id, old.titulo, old.summary, old.texto_completo, old.seccion_visto, old.seccion_considerando);
    END;

    CREATE TRIGGER normas_au AFTER UPDATE ON normas BEGIN
        INSERT INTO normas_fts(normas_fts, rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
        VALUES('delete', old.id, old.titulo, old.summary, old.texto_completo, old.seccion_visto, old.seccion_considerando);
        INSERT INTO normas_fts(rowid, titulo, summary, texto_completo, seccion_visto, seccion_considerando)
        VALUES (new.id, new.titulo, new.summary, new.texto_completo, new.seccion_visto, new.seccion_considerando);
    END;

    CREATE VIEW v_arbol_vigencia AS
    SELECT 
        'afecta_a' AS direccion,
        r.id AS referencia_id,
        r.norma_origen_id,
        no.tipo AS origen_tipo,
        no.numero AS origen_numero,
        no.anio AS origen_anio,
        r.tipo_relacion,
        r.norma_destino_id,
        nd.tipo AS destino_tipo,
        COALESCE(nd.numero, r.destino_numero) AS destino_numero,
        COALESCE(nd.anio, r.destino_anio) AS destino_anio,
        r.destino_referencia,
        r.articulos_afectados,
        r.texto_cita,
        r.notas
    FROM referencias_normativas r
    JOIN normas no ON no.id = r.norma_origen_id
    LEFT JOIN normas nd ON nd.id = r.norma_destino_id
    UNION ALL
    SELECT 
        'afectada_por' AS direccion,
        r.id AS referencia_id,
        r.norma_destino_id AS norma_origen_id,
        nd.tipo AS origen_tipo,
        nd.numero AS origen_numero,
        nd.anio AS origen_anio,
        r.tipo_relacion,
        r.norma_origen_id AS norma_destino_id,
        no.tipo AS destino_tipo,
        no.numero AS destino_numero,
        no.anio AS destino_anio,
        NULL AS destino_referencia,
        r.articulos_afectados,
        r.texto_cita,
        r.notas
    FROM referencias_normativas r
    JOIN normas no ON no.id = r.norma_origen_id
    JOIN normas nd ON nd.id = r.norma_destino_id;
    """)

    vec_habitat = create_fake_vector(384, 0.1)
    vec_salud = create_fake_vector(384, 0.2)

    # 2. Datos de prueba con múltiples municipios, años nulos y referencias cruzadas
    # Norma 1: Saladillo (108), Ordenanza 10/2021 sobre Hábitat
    cur.execute("""
    INSERT INTO normas (
        id, tipo, numero, anio, contenido_id, version, titulo, texto_completo,
        summary, estado, codigo_localidad, localidad, url, archivo_md, embedding_summary, embedding_texto
    ) VALUES (
        1, 'ordenanza', 10, 2021, 1001, 'completa',
        'Programa Municipal de Hábitat y Vivienda Digna',
        'Art. 1: Créase el Programa Municipal de Hábitat y Vivienda Social. Art. 2: Creación del banco de tierras fiscales.',
        'Crea el programa de hábitat y banco de tierras.', 'vigente', 108, 'Saladillo',
        'https://sibom.pba.gov.ar/108/1', '108/ord_10_2021.md', ?, ?
    )
    """, (vec_habitat, vec_habitat))

    # Norma 2: Saladillo (108), Ordenanza 25/2022 que modifica Ordenanza 10/2021
    cur.execute("""
    INSERT INTO normas (
        id, tipo, numero, anio, contenido_id, version, titulo, texto_completo,
        summary, estado, codigo_localidad, localidad, url, archivo_md, embedding_summary, embedding_texto
    ) VALUES (
        2, 'ordenanza', 25, 2022, 1002, 'completa',
        'Modificación de la Ordenanza de Hábitat y Banco de Tierras',
        'Art. 1: Modifícase el artículo 2 de la Ordenanza 10/2021 sobre destino de las tierras fiscales.',
        'Modifica el banco de tierras de la ord 10/2021.', 'vigente', 108, 'Saladillo',
        'https://sibom.pba.gov.ar/108/2', '108/ord_25_2022.md', ?, ?
    )
    """, (vec_habitat, vec_habitat))

    # Norma 3: Veinticinco de Mayo (130), Ordenanza 40/2020 sobre Hábitat
    cur.execute("""
    INSERT INTO normas (
        id, tipo, numero, anio, contenido_id, version, titulo, texto_completo,
        summary, estado, codigo_localidad, localidad, url, archivo_md, embedding_summary, embedding_texto
    ) VALUES (
        3, 'ordenanza', 40, 2020, 1003, 'completa',
        'Régimen de Suelo Urbano y Acceso a la Vivienda en Veinticinco de Mayo',
        'Art. 1: Establécese el régimen general de acceso al suelo y regularización dominial de viviendas sociales.',
        'Regula el acceso al suelo y regularización dominial.', 'vigente', 130, 'Veinticinco de Mayo',
        'https://sibom.pba.gov.ar/130/3', '130/ord_40_2020.md', ?, ?
    )
    """, (vec_habitat, vec_habitat))

    # Norma 4: Adolfo Alsina (1), Decreto 150/2023 sobre Salud
    cur.execute("""
    INSERT INTO normas (
        id, tipo, numero, anio, contenido_id, version, titulo, texto_completo,
        summary, estado, codigo_localidad, localidad, url, archivo_md, embedding_summary, embedding_texto
    ) VALUES (
        4, 'decreto', 150, 2023, 1004, 'completa',
        'Adquisición de insumos para centros de atención primaria de la salud',
        'Art. 1: Apruébase el gasto para provisión sanitaria a los CAPS.',
        'Compra de insumos médicos para CAPS.', 'vigente', 1, 'Adolfo Alsina',
        'https://sibom.pba.gov.ar/1/4', '1/dec_150_2023.md', ?, ?
    )
    """, (vec_salud, vec_salud))

    # Norma 5: Saladillo (108), Ordenanza histórica sin año (año nulo)
    cur.execute("""
    INSERT INTO normas (
        id, tipo, numero, anio, contenido_id, version, titulo, texto_completo,
        summary, estado, codigo_localidad, localidad, url, archivo_md
    ) VALUES (
        5, 'ordenanza', 999, NULL, 1005, 'extractada',
        'Reglamento histórico de cementerio',
        'Art. 1: Disposiciones sobre nichos.',
        'Regula cementerio.', 'vigente', 108, 'Saladillo',
        'https://sibom.pba.gov.ar/108/5', '108/ord_999.md'
    )
    """)

    # Artículos para Norma 1 y 2
    cur.execute("INSERT INTO articulos (id, norma_id, numero_articulo, orden, texto) VALUES (1, 1, '1', 1, 'Créase el Programa Municipal de Hábitat y Vivienda Social.')")
    cur.execute("INSERT INTO articulos (id, norma_id, numero_articulo, orden, texto) VALUES (2, 1, '2', 2, 'Creación del banco de tierras fiscales destinadas a loteos sociales.')")
    cur.execute("INSERT INTO articulos (id, norma_id, numero_articulo, orden, texto) VALUES (3, 2, '1', 1, 'Modifícase el artículo 2 de la Ordenanza 10/2021 sobre destino de las tierras fiscales.')")
    cur.execute("INSERT INTO articulos (id, norma_id, numero_articulo, orden, texto) VALUES (4, 3, '1', 1, 'Establécese el régimen general de acceso al suelo y regularización dominial de viviendas sociales.')")

    # Referencias normativas (con ciclo: Norma 2 modifica Norma 1, y una cita externa)
    cur.execute("""
    INSERT INTO referencias_normativas (id, norma_origen_id, norma_destino_id, destino_tipo, destino_numero, destino_anio, tipo_relacion, texto_cita)
    VALUES (1, 2, 1, 'ordenanza', 10, 2021, 'modifica', 'Modifícase el artículo 2 de la Ordenanza 10/2021')
    """)
    cur.execute("""
    INSERT INTO referencias_normativas (id, norma_origen_id, norma_destino_id, destino_tipo, destino_referencia, tipo_relacion, texto_cita)
    VALUES (2, 1, NULL, 'ley_provincial', 'Ley 14.449', 'cita', 'En el marco de la Ley Provincial de Acceso Justo al Hábitat N° 14.449')
    """)

    # Anexo de prueba
    anexo_pdf = anexos_dir / "anexo_plano_1.pdf"
    anexo_pdf.write_text("PDF simulado plano loteo")
    cur.execute("""
    INSERT INTO anexos (id, norma_id, nombre, archivo_pdf, url)
    VALUES (1, 1, 'Anexo I - Plano de loteo social', 'anexo_plano_1.pdf', 'https://sibom.pba.gov.ar/anexo/1')
    """)

    conn.commit()
    conn.close()

    # 3. Inicializar base de índice derivado
    init_index_db(index_file)

    # Insertar categorías iniciales en index_db
    iconn = sqlite3.connect(str(index_file))
    icur = iconn.cursor()
    icur.execute("INSERT INTO categorias (id, nombre, slug, descripcion) VALUES (1, 'Urbanismo y Uso del Suelo', 'urbanismo-suelo', 'Tierras, loteos y habitat')")
    icur.execute("INSERT INTO categorias (id, nombre, slug, descripcion, parent_id) VALUES (2, 'Vivienda Social', 'vivienda-social', 'Planes de vivienda y lotes', 1)")
    icur.execute("INSERT INTO categorias (id, nombre, slug, descripcion) VALUES (3, 'Salud Publica', 'salud-publica', 'Salud y centros de atencion')")
    
    # Asignaciones
    icur.execute("INSERT INTO norma_categorias (norma_id, categoria_id, relevancia) VALUES (1, 1, 0.95)")
    icur.execute("INSERT INTO norma_categorias (norma_id, categoria_id, relevancia) VALUES (1, 2, 0.90)")
    icur.execute("INSERT INTO norma_categorias (norma_id, categoria_id, relevancia) VALUES (2, 2, 0.85)")
    icur.execute("INSERT INTO norma_categorias (norma_id, categoria_id, relevancia) VALUES (3, 2, 0.88)")
    icur.execute("INSERT INTO norma_categorias (norma_id, categoria_id, relevancia) VALUES (4, 3, 0.92)")

    # Entidades
    icur.execute("INSERT INTO entidades (id, nombre, slug, tipo) VALUES (1, 'Ministerio de Hábitat', 'ministerio-de-habitat', 'organismo')")
    icur.execute("INSERT INTO entidades (id, nombre, slug, tipo) VALUES (2, 'Juan Pérez', 'juan-perez', 'persona')")
    icur.execute("INSERT INTO norma_entidades (norma_id, entidad_id, rol, contexto) VALUES (1, 1, 'firmante', 'Convenio con Ministerio de Hábitat')")

    # Articulo embeddings
    icur.execute("INSERT INTO articulo_embeddings (articulo_id, norma_id, codigo_localidad, embedding) VALUES (1, 1, 108, ?)", (vec_habitat,))
    icur.execute("INSERT INTO articulo_embeddings (articulo_id, norma_id, codigo_localidad, embedding) VALUES (2, 1, 108, ?)", (vec_habitat,))
    icur.execute("INSERT INTO articulo_embeddings (articulo_id, norma_id, codigo_localidad, embedding) VALUES (4, 3, 130, ?)", (vec_habitat,))

    iconn.commit()
    iconn.close()

    return {
        "db_path": db_file,
        "index_path": index_file,
        "anexos_dir": anexos_dir
    }
