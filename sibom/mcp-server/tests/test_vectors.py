"""Pruebas para operaciones vectoriales matriciales y RRF."""
import numpy as np
import pytest
from sibom_mcp.vectors import compute_top_k, reciprocal_rank_fusion
from sibom_mcp.embeddings import normalize_vector, parse_blob_to_vector


def test_normalize_vector():
    """Verifica normalización L2 y rechazo de vectores inválidos."""
    v = np.array([3.0, 4.0], dtype=np.float32)
    normed = normalize_vector(v)
    assert np.isclose(np.linalg.norm(normed), 1.0)

    # Vector cero arroja ValueError
    with pytest.raises(ValueError):
        normalize_vector(np.array([0.0, 0.0], dtype=np.float32))

    # Vector con NaN arroja ValueError
    with pytest.raises(ValueError):
        normalize_vector(np.array([np.nan, 1.0], dtype=np.float32))


def test_compute_top_k_exhaustivo():
    """Verifica top-k y ordenamiento correcto con producto punto."""
    dim = 4
    # 3 vectores ortonormales
    v1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.7071, 0.7071, 0.0, 0.0], dtype=np.float32)

    matrix = np.vstack([v1, v2, v3])
    ids = [101, 102, 103]

    # Query muy cercana a v1
    query = np.array([0.9, 0.1, 0.0, 0.0], dtype=np.float32)
    query = query / np.linalg.norm(query)

    results = compute_top_k(query, matrix, ids, limit=2, umbral=0.0)
    assert len(results) == 2
    # El más cercano debe ser 101, luego 103
    assert results[0][0] == 101
    assert results[1][0] == 103
    assert results[0][1] > results[1][1]


def test_compute_top_k_empty_matrix():
    """Verifica que una matriz vacía no lance excepciones y devuelva lista vacía."""
    query = np.array([1.0, 0.0], dtype=np.float32)
    matrix = np.empty((0, 2), dtype=np.float32)
    results = compute_top_k(query, matrix, [], limit=10)
    assert results == []


def test_reciprocal_rank_fusion():
    """Verifica fusión de rankings por RRF con desempate estable."""
    list1 = [
        {"id": 1, "titulo": "Norma A"},
        {"id": 2, "titulo": "Norma B"},
        {"id": 3, "titulo": "Norma C"},
    ]
    list2 = [
        {"id": 2, "titulo": "Norma B"},
        {"id": 1, "titulo": "Norma A"},
        {"id": 4, "titulo": "Norma D"},
    ]

    fused = reciprocal_rank_fusion([list1, list2], id_key="id", k=60, limit=3)
    assert len(fused) == 3
    # Norma 1 y Norma 2 aparecen en ambos rankings, deben tener los puntajes más altos
    top_ids = [item["id"] for item in fused]
    assert 1 in top_ids
    assert 2 in top_ids
    assert fused[0]["channel_hits"] == 2
