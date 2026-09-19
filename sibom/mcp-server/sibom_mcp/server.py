"""Servidor FastMCP SIBOM con las 17 herramientas normativas registradas."""
import json
import logging
import sys
import time
from typing import Any, Literal
from fastmcp import FastMCP
from .config import settings
from .db import Database
from .tools.search import search_normas, search_by_category, search_by_year_range
from .tools.detail import get_norma, get_anexo
from .tools.references import get_references
from .tools.stats import get_stats
from .tools.similar import similar_normas
from .tools.summarize import summarize_texto
from .tools.categories import list_categories
from .tools.entities import search_by_entity
from .tools.semantic import semantic_search, semantic_search_articulos, full_semantic_search
from .tools.compilar import compilar_tematica
from .tools.comparar import comparar_intermunicipal

# Asegurar que logs vayan a stderr para no romper el protocolo stdio en stdout
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sibom_mcp.server")

SERVER_START_TIME = time.time()


def create_mcp_server(db: Database | None = None) -> FastMCP:
    """Crea e inicializa la instancia FastMCP con las 17 herramientas registradas."""
    _db = db or Database()
    mcp = FastMCP(
        "sibom-mcp",
        instructions=(
            "Servidor MCP para consulta normativa multi-municipio de la Provincia de Buenos Aires (SIBOM). "
            "Proporciona búsqueda textual FTS5, búsqueda semántica vectorial, compilación temática y "
            "comparación de antecedentes intermunicipales."
        )
    )

    # 1. sibom_search_normas
    @mcp.tool(
        name="sibom_search_normas",
        description="Búsqueda full-text de normas usando SQLite FTS5 y ranking BM25 con filtros opcionales."
    )
    def tool_search_normas(
        query: str,
        municipio: str | int | None = None,
        tipo: Literal["ordenanza", "decreto", "todos"] = "ordenanza",
        solo_vigentes: bool = False,
        limit: int = 20
    ) -> dict[str, Any]:
        return search_normas(
            db=_db,
            query=query,
            municipio=municipio,
            tipo=tipo,
            solo_vigentes=solo_vigentes,
            limit=limit
        )

    # 2. sibom_search_by_category
    @mcp.tool(
        name="sibom_search_by_category",
        description="Filtra normas por slug de categoría taxonómica y opcionalmente por año y municipio."
    )
    def tool_search_by_category(
        slug: str,
        municipio: str | int | None = None,
        anio: int | None = None,
        limit: int = 20
    ) -> dict[str, Any]:
        return search_by_category(
            db=_db,
            slug=slug,
            municipio=municipio,
            anio=anio,
            limit=limit
        )

    # 3. sibom_search_by_year_range
    @mcp.tool(
        name="sibom_search_by_year_range",
        description="Busca normas en un rango de años inclusivo (desde..hasta)."
    )
    def tool_search_by_year_range(
        desde: int,
        hasta: int,
        municipio: str | int | None = None,
        tipo: Literal["ordenanza", "decreto", "todos"] = "ordenanza",
        limit: int = 20
    ) -> dict[str, Any]:
        if desde > hasta:
            raise ValueError(f"'desde' ({desde}) no puede ser mayor que 'hasta' ({hasta})")
        return search_by_year_range(
            db=_db,
            desde=desde,
            hasta=hasta,
            municipio=municipio,
            tipo=tipo,
            limit=limit
        )

    # 4. sibom_get_norma
    @mcp.tool(
        name="sibom_get_norma",
        description="Obtiene el detalle completo de una norma por ID, incluyendo texto, artículos, referencias, anexos y categorías."
    )
    def tool_get_norma(id: int) -> dict[str, Any]:
        if id <= 0:
            raise ValueError("El ID debe ser un entero positivo mayor que cero")
        return get_norma(db=_db, norma_id=id)

    # 5. sibom_get_anexo
    @mcp.tool(
        name="sibom_get_anexo",
        description="Obtiene información y texto extraído de un anexo PDF por ID o por norma_id y número de anexo."
    )
    def tool_get_anexo(
        id: int | None = None,
        norma_id: int | None = None,
        anexo_numero: str | None = None
    ) -> dict[str, Any]:
        return get_anexo(
            db=_db,
            anexo_id=id,
            norma_id=norma_id,
            anexo_numero=anexo_numero
        )

    # 6. sibom_search_by_entity
    @mcp.tool(
        name="sibom_search_by_entity",
        description="Busca normas que mencionen una entidad específica (persona, empresa u organismo) con evidencia de rol y contexto."
    )
    def tool_search_by_entity(
        nombre: str,
        tipo: str | None = None,
        municipio: str | int | None = None,
        limit: int = 20
    ) -> dict[str, Any]:
        return search_by_entity(
            db=_db,
            nombre=nombre,
            tipo=tipo,
            municipio=municipio,
            limit=limit
        )

    # 7. sibom_get_references
    @mcp.tool(
        name="sibom_get_references",
        description="Obtiene el árbol de vigencia y referencias normativas (modificaciones, derogaciones, citas) con control de ciclos."
    )
    def tool_get_references(
        norma_id: int,
        direccion: Literal["ambas", "afecta_a", "afectada_por"] = "ambas",
        profundidad: int = 1,
        limit: int = 50
    ) -> dict[str, Any]:
        if profundidad < 1 or profundidad > 5:
            raise ValueError("La profundidad debe estar entre 1 y 5")
        return get_references(
            db=_db,
            norma_id=norma_id,
            direccion=direccion,
            profundidad=profundidad,
            limit=limit
        )

    # 8. sibom_list_categories
    @mcp.tool(
        name="sibom_list_categories",
        description="Lista la taxonomía jerárquica de categorías y la cantidad de normas asignadas a cada una."
    )
    def tool_list_categories(incluir_vacias: bool = False) -> dict[str, Any]:
        return list_categories(db=_db, incluir_vacias=incluir_vacias)

    # 9. sibom_get_stats
    @mcp.tool(
        name="sibom_get_stats",
        description="Obtiene estadísticas generales del corpus SIBOM o filtradas por municipio (totales, años, embeddings)."
    )
    def tool_get_stats(municipio: str | int | None = None) -> dict[str, Any]:
        return get_stats(db=_db, municipio=municipio)

    # 10. sibom_similar_normas
    @mcp.tool(
        name="sibom_similar_normas",
        description="Busca normas semánticamente similares a una norma de referencia usando embeddings vectoriales (excluye la norma de entrada)."
    )
    def tool_similar_normas(
        norma_id: int,
        municipio: str | int | None = None,
        limit: int = 10,
        umbral: float = 0.5
    ) -> dict[str, Any]:
        return similar_normas(
            db=_db,
            norma_id=norma_id,
            municipio=municipio,
            limit=limit,
            umbral=umbral
        )

    # 11. sibom_summarize_texto
    @mcp.tool(
        name="sibom_summarize_texto",
        description="Genera un resumen de texto legal mediante LLM configurado (Groq/Llama), con caché persistente."
    )
    def tool_summarize_texto(
        texto: str,
        longitud: int = 50,
        estilo: Literal["formal", "simple", "bullet-points"] = "formal"
    ) -> dict[str, Any]:
        return summarize_texto(
            db=_db,
            texto=texto,
            longitud=longitud,
            estilo=estilo
        )

    # 12. sibom_health_check
    @mcp.tool(
        name="sibom_health_check",
        description="Verifica el estado del servidor MCP, conectividad de SQLite (solo lectura), FTS5, modelo de embeddings e índices derivados."
    )
    def tool_health_check() -> dict[str, Any]:
        start = time.time()
        db_status = "error"
        fts_status = "error"
        total_normas = 0

        try:
            rows = _db.query("SELECT count(*) as cnt FROM normas")
            total_normas = rows[0]["cnt"]
            db_status = "connected"

            # Verificar FTS5
            fts_rows = _db.query("SELECT count(*) as cnt FROM normas_fts")
            fts_status = "ok"
        except Exception as e:
            logger.error(f"Health check error en base de datos: {e}")

        index_status = "ok"
        try:
            _db.query_index("SELECT count(*) FROM manifests")
        except Exception:
            index_status = "not_initialized"

        uptime = round(time.time() - SERVER_START_TIME, 2)
        status = "ok" if (db_status == "connected" and fts_status == "ok") else "degraded"

        return {
            "status": status,
            "database": {
                "status": db_status,
                "path": str(settings.sibom_db_path),
                "total_normas": total_normas,
                "fts5": fts_status
            },
            "index_db": {
                "status": index_status,
                "path": str(settings.index_db_path)
            },
            "embedding_model": {
                "model_name": settings.embedding_model,
                "dimension": settings.embedding_dimension
            },
            "uptime_seconds": uptime,
            "latency_ms": round((time.time() - start) * 1000, 2)
        }

    # 13. sibom_semantic_search
    @mcp.tool(
        name="sibom_semantic_search",
        description="Búsqueda semántica en lenguaje natural sobre normas completas usando embeddings vectoriales y matrices NumPy."
    )
    def tool_semantic_search(
        query: str,
        municipio: str | int | None = None,
        tipo: Literal["ordenanza", "decreto", "todos"] = "ordenanza",
        solo_vigentes: bool = False,
        limit: int = 10,
        umbral: float = 0.4
    ) -> dict[str, Any]:
        return semantic_search(
            db=_db,
            query=query,
            municipio=municipio,
            tipo=tipo,
            solo_vigentes=solo_vigentes,
            limit=limit,
            umbral=umbral
        )

    # 14. sibom_semantic_search_articulos
    @mcp.tool(
        name="sibom_semantic_search_articulos",
        description="Búsqueda semántica en lenguaje natural a nivel de artículos individuales en el índice derivado."
    )
    def tool_semantic_search_articulos(
        query: str,
        municipio: str | int | None = None,
        solo_vigentes: bool = False,
        limit: int = 10,
        umbral: float = 0.4
    ) -> dict[str, Any]:
        return semantic_search_articulos(
            db=_db,
            query=query,
            municipio=municipio,
            solo_vigentes=solo_vigentes,
            limit=limit,
            umbral=umbral
        )

    # 15. sibom_full_semantic_search
    @mcp.tool(
        name="sibom_full_semantic_search",
        description="Búsqueda semántica combinada de normas completas y artículos individuales con identidad diferenciada por resultado."
    )
    def tool_full_semantic_search(
        query: str,
        municipio: str | int | None = None,
        solo_vigentes: bool = False,
        limit: int = 10,
        umbral: float = 0.4
    ) -> dict[str, Any]:
        return full_semantic_search(
            db=_db,
            query=query,
            municipio=municipio,
            solo_vigentes=solo_vigentes,
            limit=limit,
            umbral=umbral
        )

    # 16. sibom_compilar_tematica
    @mcp.tool(
        name="sibom_compilar_tematica",
        description="Genera un dossier normativo estructurado y en Markdown sobre un tema, con inventario, articulado, relaciones y anexos."
    )
    def tool_compilar_tematica(
        tema: str,
        municipios: list[str | int] | None = None,
        desde: int | None = None,
        hasta: int | None = None,
        tipo: Literal["ordenanza", "decreto", "todos"] = "ordenanza",
        solo_vigentes: bool = False,
        cursor: int = 0,
        limit: int = 20
    ) -> dict[str, Any]:
        return compilar_tematica(
            db=_db,
            tema=tema,
            municipios=municipios,
            desde=desde,
            hasta=hasta,
            tipo=tipo,
            solo_vigentes=solo_vigentes,
            cursor=cursor,
            limit=limit
        )

    # 17. sibom_comparar_intermunicipal
    @mcp.tool(
        name="sibom_comparar_intermunicipal",
        description="Compara antecedentes normativos de municipios de referencia contra un municipio destino (Saladillo por defecto) para detectar equivalentes y posibles brechas."
    )
    def tool_comparar_intermunicipal(
        tema: str,
        municipio_destino: str | int = 108,
        municipios_referencia: list[str | int] | None = None,
        periodo_desde: int | None = None,
        limit_candidatos: int = 20
    ) -> dict[str, Any]:
        return comparar_intermunicipal(
            db=_db,
            tema=tema,
            municipio_destino=municipio_destino,
            municipios_referencia=municipios_referencia,
            periodo_desde=periodo_desde,
            limit_candidatos=limit_candidatos
        )

    return mcp


# Instancia por defecto para arranque
mcp_server = create_mcp_server()
