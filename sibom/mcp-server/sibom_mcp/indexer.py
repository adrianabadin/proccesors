"""CLI y lógica para construcción y actualización del índice derivado de SIBOM."""
import argparse
import logging
import sqlite3
import sys
import uuid
from pathlib import Path
from typing import Any
import numpy as np
from .config import settings
from .db import init_index_db
from .embeddings import get_embedding_model

logger = logging.getLogger(__name__)


def build_index(
    db_path: str | Path,
    output_path: str | Path,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    batch_size: int = 64,
    resume: bool = True,
    mock: bool = False,
    max_items: int | None = None
) -> dict[str, Any]:
    """Construye o actualiza incrementalmente el índice derivado."""
    source_path = Path(db_path).resolve()
    target_path = Path(output_path).resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Base de datos de origen no encontrada: {source_path}")

    # Inicializar schema si es necesario
    init_index_db(target_path)

    # Cargar modelo
    model = get_embedding_model(model_name, mock=mock)

    # Conectar a origen y destino
    src_conn = sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True)
    src_conn.row_factory = sqlite3.Row
    src_cur = src_conn.cursor()

    tgt_conn = sqlite3.connect(str(target_path))
    tgt_cur = tgt_conn.cursor()

    # 1. Obtener artículos a indexar
    indexed_articulo_ids: set[int] = set()
    if resume:
        tgt_cur.execute("SELECT articulo_id FROM articulo_embeddings")
        indexed_articulo_ids = {r[0] for r in tgt_cur.fetchall()}

    src_cur.execute("""
        SELECT a.id, a.norma_id, a.texto, n.codigo_localidad
        FROM articulos a
        JOIN normas n ON a.norma_id = n.id
        WHERE a.texto IS NOT NULL AND length(trim(a.texto)) > 5
    """)
    all_articulos = src_cur.fetchall()
    pending = [a for a in all_articulos if a["id"] not in indexed_articulo_ids]

    if max_items:
        pending = pending[:max_items]

    total_pending = len(pending)
    indexed_count = 0

    # 2. Procesar en lotes
    for i in range(0, total_pending, batch_size):
        batch = pending[i : i + batch_size]
        texts = [b["texto"] for b in batch]

        vectors = model.encode(texts, normalize_embeddings=True)
        if len(batch) == 1 and vectors.ndim == 1:
            vectors = np.expand_dims(vectors, axis=0)

        rows_to_insert = []
        for b, vec in zip(batch, vectors):
            blob = vec.astype(np.float32).tobytes()
            rows_to_insert.append((b["id"], b["norma_id"], b["codigo_localidad"], blob))

        tgt_cur.executemany("""
            INSERT OR REPLACE INTO articulo_embeddings (articulo_id, norma_id, codigo_localidad, embedding)
            VALUES (?, ?, ?, ?)
        """, rows_to_insert)
        tgt_conn.commit()
        indexed_count += len(batch)

    # 3. Registrar manifiesto de generación
    generation_id = str(uuid.uuid4())
    tgt_cur.execute("UPDATE manifests SET active = 0 WHERE active = 1")
    tgt_cur.execute("""
        INSERT INTO manifests (generation_id, model_name, embedding_dim, total_items, active)
        VALUES (?, ?, ?, ?, 1)
    """, (generation_id, model_name, settings.embedding_dimension, indexed_count + len(indexed_articulo_ids)))
    tgt_conn.commit()

    src_conn.close()
    tgt_conn.close()

    return {
        "generation_id": generation_id,
        "model_name": model_name,
        "new_indexed": indexed_count,
        "total_articles": indexed_count + len(indexed_articulo_ids)
    }


def main():
    """Punto de entrada CLI para indexación."""
    parser = argparse.ArgumentParser(description="Construcción del índice vectorial derivado para SIBOM MCP")
    parser.add_argument("--db", default=settings.sibom_db_path, help="Ruta a sibom.db de origen")
    parser.add_argument("--output", default=settings.index_db_path, help="Ruta a sibom-index.db de destino")
    parser.add_argument("--model", default=settings.embedding_model, help="Nombre del modelo de sentence-transformers")
    parser.add_argument("--batch-size", type=int, default=64, help="Tamaño de lote para vectorización")
    parser.add_argument("--resume", action="store_true", default=True, help="Reanudar omitiendo artículos ya indexados")
    parser.add_argument("--mock", action="store_true", default=False, help="Usar modelo simulado determinista")
    parser.add_argument("--max-items", type=int, default=None, help="Límite de artículos a procesar (para pruebas)")

    args = parser.parse_args()
    print(f"Iniciando indexador SIBOM con modelo '{args.model}'...")
    res = build_index(
        db_path=args.db,
        output_path=args.output,
        model_name=args.model,
        batch_size=args.batch_size,
        resume=args.resume,
        mock=args.mock,
        max_items=args.max_items
    )
    print(f"Indexación completada: {res}")


if __name__ == "__main__":
    main()
