"""Adaptador para generación y caché de resúmenes con IA."""
import hashlib
import logging
from typing import Any
from .config import settings
from .db import Database

logger = logging.getLogger(__name__)


def compute_cache_key(texto: str, estilo: str, longitud: int, modelo: str) -> str:
    """Calcula la clave de hash sha256 para almacenamiento en caché."""
    content = f"{modelo}|{estilo}|{longitud}|{texto}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class SummaryProvider:
    """Manejador de resúmenes con caché y respaldo de proveedores."""

    def __init__(self, db: Database):
        self.db = db

    def is_configured(self) -> bool:
        """Verifica si al menos un proveedor LLM está configurado en el entorno."""
        return bool(settings.groq_api_key or settings.openai_api_key)

    def generate_summary(
        self,
        texto: str,
        longitud: int = 50,
        estilo: str = "formal",
        mock_response: str | None = None
    ) -> dict[str, Any]:
        """Genera un resumen o lo recupera de la base de datos de caché."""
        modelo = settings.llm_model if not mock_response else "mock-llm"
        hash_key = compute_cache_key(texto, estilo, longitud, modelo)

        # 1. Verificar si ya está en caché
        try:
            cached_rows = self.db.query_index(
                "SELECT resumen, tokens_usados, modelo FROM summary_cache WHERE hash_key = ?",
                (hash_key,)
            )
            if cached_rows:
                row = cached_rows[0]
                return {
                    "status": "ok",
                    "resumen": row["resumen"],
                    "tokens_usados": row["tokens_usados"],
                    "modelo": row["modelo"],
                    "cached": True
                }
        except Exception as e:
            logger.warning(f"Error consultando summary_cache: {e}")

        # 2. Si no está en caché y no hay proveedor ni mock, error explícito
        if not self.is_configured() and mock_response is None:
            return {
                "status": "provider_not_configured",
                "error": (
                    "Cliente LLM no configurado. Establezca la variable de entorno "
                    "GROQ_API_KEY o OPENAI_API_KEY para habilitar esta herramienta."
                ),
                "resumen": None,
                "cached": False
            }

        # 3. Generar nuevo resumen (usando mock o cliente real)
        if mock_response is not None:
            resumen = mock_response
            tokens_usados = len(texto.split()) // 2
        else:
            # Llamada a proveedor real (ej: Groq Llama 3.3 70B)
            resumen = self._call_real_provider(texto, longitud, estilo)
            tokens_usados = len(resumen.split()) * 2

        # 4. Guardar en caché del índice derivado
        try:
            conn = self.db.get_index_conn(readonly=False)
            cur = conn.cursor()
            texto_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()
            cur.execute("""
                INSERT OR REPLACE INTO summary_cache (
                    hash_key, texto_hash, estilo, longitud, modelo, resumen, tokens_usados
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (hash_key, texto_hash, estilo, longitud, modelo, resumen, tokens_usados))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Error guardando en summary_cache: {e}")

        return {
            "status": "ok",
            "resumen": resumen,
            "tokens_usados": tokens_usados,
            "modelo": modelo,
            "cached": False
        }

    def _call_real_provider(self, texto: str, longitud: int, estilo: str) -> str:
        """Llama a la API configurada (Groq u OpenAI)."""
        prompt = (
            f"Resume el siguiente texto legal municipal en aproximadamente {longitud} palabras. "
            f"Estilo requerido: {estilo}.\n\nTexto:\n{texto}"
        )

        if settings.groq_api_key:
            import httpx
            headers = {
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        raise RuntimeError("No se encontró configuración activa para el proveedor LLM.")
