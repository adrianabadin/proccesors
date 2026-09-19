"""Gestión de conexiones seguras y solo lectura a SQLite para SIBOM."""
import sqlite3
import threading
from pathlib import Path
from typing import Any, Sequence
from .config import settings

_local = threading.local()


def get_readonly_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Abre y devuelve una conexión SQLite en modo estricto de solo lectura.
    
    Usa URI 'file:...mode=ro' y activa PRAGMA query_only = ON.
    """
    path = Path(db_path or settings.sibom_db_path).resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"La base de datos SQLite no existe en la ruta: {path}. "
            "Verifique la variable de entorno SIBOM_DB_PATH."
        )

    # Convertir ruta a formato URI para Windows y Unix
    uri_path = path.as_uri() + "?mode=ro"
    
    conn = sqlite3.connect(
        uri_path,
        uri=True,
        timeout=settings.sqlite_timeout,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON;")
    return conn


def get_index_connection(db_path: str | Path | None = None, readonly: bool = True) -> sqlite3.Connection:
    """Abre la base de datos del índice derivado (data/sibom-index.db)."""
    path = Path(db_path or settings.index_db_path).resolve()
    
    if readonly:
        if not path.exists():
            # Si no existe aún el índice y se pide lectura, inicializar schema vacío
            init_index_db(path)
        uri_path = path.as_uri() + "?mode=ro"
        conn = sqlite3.connect(
            uri_path,
            uri=True,
            timeout=settings.sqlite_timeout,
            check_same_thread=False
        )
        conn.execute("PRAGMA query_only = ON;")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(path),
            timeout=settings.sqlite_timeout,
            check_same_thread=False
        )
        conn.execute("PRAGMA journal_mode = WAL;")

    conn.row_factory = sqlite3.Row
    return conn


def init_index_db(db_path: Path | str) -> None:
    """Inicializa el esquema del índice derivado si no existe."""
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.executescript("""
        PRAGMA journal_mode = WAL;

        -- Manifiestos de generación de índices
        CREATE TABLE IF NOT EXISTS manifests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation_id TEXT UNIQUE NOT NULL,
            model_name TEXT NOT NULL,
            embedding_dim INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            total_items INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        );

        -- Taxonomía de categorías
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            descripcion TEXT,
            parent_id INTEGER REFERENCES categorias(id)
        );

        -- Asignación de categorías a normas
        CREATE TABLE IF NOT EXISTS norma_categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            norma_id INTEGER NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id),
            relevancia REAL DEFAULT 1.0,
            origen TEXT DEFAULT 'clasificador',
            UNIQUE(norma_id, categoria_id)
        );

        -- Entidades tipadas
        CREATE TABLE IF NOT EXISTS entidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            slug TEXT NOT NULL,
            tipo TEXT NOT NULL, -- persona, empresa, organismo, otro
            alias TEXT, -- JSON array de aliases
            UNIQUE(slug, tipo)
        );

        -- Menciones de entidades en normas
        CREATE TABLE IF NOT EXISTS norma_entidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            norma_id INTEGER NOT NULL,
            entidad_id INTEGER NOT NULL REFERENCES entidades(id),
            rol TEXT,
            contexto TEXT,
            UNIQUE(norma_id, entidad_id)
        );

        -- Embeddings de artículos individuales
        CREATE TABLE IF NOT EXISTS articulo_embeddings (
            articulo_id INTEGER PRIMARY KEY,
            norma_id INTEGER NOT NULL,
            codigo_localidad INTEGER NOT NULL,
            embedding BLOB NOT NULL, -- Vector float32
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        -- Caché de resúmenes generados con LLM
        CREATE TABLE IF NOT EXISTS summary_cache (
            hash_key TEXT PRIMARY KEY,
            prompt_hash TEXT,
            texto_hash TEXT NOT NULL,
            estilo TEXT NOT NULL,
            longitud INTEGER NOT NULL,
            modelo TEXT NOT NULL,
            resumen TEXT NOT NULL,
            tokens_usados INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()
    conn.close()


class Database:
    """Clase envolvente para ejecutar consultas seguras en sibom.db y el índice."""

    def __init__(self, db_path: str | Path | None = None, index_path: str | Path | None = None):
        self.db_path = Path(db_path or settings.sibom_db_path)
        self.index_path = Path(index_path or settings.index_db_path)

    def get_source_conn(self) -> sqlite3.Connection:
        return get_readonly_connection(self.db_path)

    def get_index_conn(self, readonly: bool = True) -> sqlite3.Connection:
        return get_index_connection(self.index_path, readonly=readonly)

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Ejecuta una consulta SELECT en la base principal y retorna diccionarios."""
        conn = self.get_source_conn()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def query_index(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        """Ejecuta una consulta SELECT en el índice derivado."""
        conn = self.get_index_conn(readonly=True)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
