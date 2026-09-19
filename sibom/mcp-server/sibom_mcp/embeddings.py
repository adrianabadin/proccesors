"""Gestión de modelos y cálculo de embeddings vectoriales."""
import logging
from typing import Any
import numpy as np
from .config import settings

logger = logging.getLogger(__name__)

_MODEL_INSTANCE: Any = None
_MODEL_NAME_LOADED: str | None = None


def get_embedding_model(model_name: str | None = None, mock: bool = False) -> Any:
    """Carga y cachea en memoria el modelo de embeddings SentenceTransformer."""
    global _MODEL_INSTANCE, _MODEL_NAME_LOADED

    target_model = model_name or settings.embedding_model

    if mock or target_model == "mock":
        return MockEmbeddingModel(dim=settings.embedding_dimension)

    if _MODEL_INSTANCE is not None and _MODEL_NAME_LOADED == target_model:
        return _MODEL_INSTANCE

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Cargando modelo sentence-transformers: {target_model}")
        model = SentenceTransformer(target_model)
        _MODEL_INSTANCE = model
        _MODEL_NAME_LOADED = target_model
        return model
    except Exception as exc:
        logger.error(f"Error cargando {target_model}: {exc}")
        raise RuntimeError(
            f"No se pudo cargar el modelo de embeddings '{target_model}'. "
            "Asegúrese de tener conexión o use un modelo local disponible."
        ) from exc


class MockEmbeddingModel:
    """Modelo determinista para pruebas unitarias sin dependencias externas."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode(self, texts: str | list[str], normalize_embeddings: bool = True, **kwargs: Any) -> np.ndarray:
        single = isinstance(texts, str)
        text_list = [texts] if single else texts

        vectors = []
        for t in text_list:
            # Hash determinista pero reproducible
            seed = sum(ord(c) for c in t) % 1000
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(self.dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0 and normalize_embeddings:
                vec = vec / norm
            vectors.append(vec)

        arr = np.array(vectors, dtype=np.float32)
        return arr[0] if single else arr


def normalize_vector(vec: np.ndarray) -> np.ndarray:
    """Normaliza un vector a norma unitaria (L2)."""
    norm = np.linalg.norm(vec)
    if norm == 0 or np.isnan(norm) or np.isinf(norm):
        raise ValueError("El vector tiene norma cero, NaN o infinito.")
    return vec / norm


def parse_blob_to_vector(blob: bytes | None, expected_dim: int = 384) -> np.ndarray | None:
    """Convierte un BLOB float32 de SQLite a un array NumPy validado."""
    if not blob:
        return None
    
    expected_bytes = expected_dim * 4
    if len(blob) != expected_bytes:
        # Longitud inconsistente con la dimensión esperada
        return None

    vec = np.frombuffer(blob, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm == 0 or np.isnan(norm) or np.isinf(norm):
        return None
    return vec / norm
