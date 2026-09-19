"""Operaciones vectoriales con matrices NumPy, similitud coseno y RRF."""
from typing import Any, Sequence
import numpy as np


def compute_top_k(
    query_vec: np.ndarray,
    matrix: np.ndarray,
    ids: Sequence[int],
    limit: int = 10,
    umbral: float = 0.0
) -> list[tuple[int, float]]:
    """Calcula similitud coseno entre vector de consulta y matriz normalizada.
    
    Args:
        query_vec: Vector 1D float32 de forma (D,), normalizado a norma 1.
        matrix: Matriz 2D float32 de forma (N, D), normalizada a norma 1.
        ids: Secuencia de IDs enteros correspondientes a las filas de matrix.
        limit: Cantidad de resultados top-k.
        umbral: Similitud mínima requerida (0.0 a 1.0).
        
    Returns:
        Lista de tuplas (id, score) ordenadas descendentemente por score.
    """
    if len(matrix) == 0 or len(ids) == 0:
        return []

    if query_vec.shape[0] != matrix.shape[1]:
        raise ValueError(
            f"Dimensión incompatible: consulta tiene {query_vec.shape[0]} dims, "
            f"matriz tiene {matrix.shape[1]} dims."
        )

    # Producto punto = Similitud coseno (al estar ambos normalizados)
    scores = np.dot(matrix, query_vec)

    # Filtrar por umbral
    mask = scores >= umbral
    valid_indices = np.where(mask)[0]

    if len(valid_indices) == 0:
        return []

    valid_scores = scores[valid_indices]
    valid_ids = [ids[idx] for idx in valid_indices]

    # Ordenar por score descendente con desempate por ID estable
    # Usamos argsort con signo negativo
    sorted_order = np.argsort(-valid_scores)[:limit]

    results = []
    for rank_idx in sorted_order:
        results.append((valid_ids[rank_idx], float(valid_scores[rank_idx])))

    return results


def reciprocal_rank_fusion(
    ranking_lists: list[list[dict[str, Any]]],
    id_key: str = "id",
    k: int = 60,
    limit: int = 20
) -> list[dict[str, Any]]:
    """Combina múltiples listas ordenadas de resultados mediante Reciprocal Rank Fusion (RRF).
    
    Fórmula: RRF_score(d) = sum(1.0 / (k + rank_i(d)))
    """
    rrf_scores: dict[Any, float] = {}
    item_map: dict[Any, dict[str, Any]] = {}
    channel_counts: dict[Any, int] = {}

    for ranking in ranking_lists:
        for rank, item in enumerate(ranking, start=1):
            doc_id = item.get(id_key)
            if doc_id is None:
                continue

            if doc_id not in item_map:
                item_map[doc_id] = item.copy()
                rrf_scores[doc_id] = 0.0
                channel_counts[doc_id] = 0

            rrf_scores[doc_id] += 1.0 / (k + rank)
            channel_counts[doc_id] += 1

    # Ordenar por RRF score descendente
    sorted_ids = sorted(
        rrf_scores.keys(),
        key=lambda x: (rrf_scores[x], channel_counts[x]),
        reverse=True
    )[:limit]

    fused_results = []
    for doc_id in sorted_ids:
        doc = item_map[doc_id]
        doc["rrf_score"] = round(rrf_scores[doc_id], 6)
        doc["channel_hits"] = channel_counts[doc_id]
        fused_results.append(doc)

    return fused_results
