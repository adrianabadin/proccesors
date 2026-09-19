"""Caché en memoria para embeddings de consultas y resultados frecuentes."""
import hashlib
from typing import Any
import numpy as np


class QueryVectorCache:
    """Caché LRU simple para vectores de consulta en memoria."""

    def __init__(self, maxsize: int = 256):
        self.maxsize = maxsize
        self._cache: dict[str, np.ndarray] = {}
        self._order: list[str] = []

    def _make_key(self, text: str, model_name: str) -> str:
        h = hashlib.sha256(f"{model_name}:{text}".encode("utf-8")).hexdigest()
        return h

    def get(self, text: str, model_name: str) -> np.ndarray | None:
        key = self._make_key(text, model_name)
        if key in self._cache:
            # Mover al final (más reciente)
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return None

    def set(self, text: str, model_name: str, vector: np.ndarray) -> None:
        key = self._make_key(text, model_name)
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self.maxsize:
            oldest = self._order.pop(0)
            del self._cache[oldest]

        self._cache[key] = vector
        self._order.append(key)

    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()


query_cache = QueryVectorCache()
