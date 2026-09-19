"""Esquemas Pydantic para herramientas y respuestas del servidor MCP SIBOM."""
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# ENUMS Y TIPOS BASE
# =============================================================================

TipoNorma = Literal["ordenanza", "decreto", "todos"]
EstadoVigencia = Literal["vigente", "modificada", "derogada_total", "derogada_parcial", "sin_determinar"]
EstiloResumen = Literal["formal", "simple", "bullet-points"]


# =============================================================================
# SCHEMAS DE ENTRADA (17 TOOLS)
# =============================================================================

class SearchNormasInput(BaseModel):
    """Entrada para búsqueda textual FTS5 de normas."""
    query: str = Field(..., min_length=1, description="Texto o palabras clave a buscar")
    municipio: str | int | None = Field(None, description="Código, slug o nombre del municipio (ej: 108 o 'saladillo')")
    tipo: TipoNorma = Field("ordenanza", description="Tipo de norma: ordenanza, decreto o todos")
    solo_vigentes: bool = Field(False, description="Filtrar solo normas vigentes o modificadas")
    limit: int = Field(20, ge=1, le=100, description="Cantidad máxima de resultados (1-100)")


class SearchByCategoryInput(BaseModel):
    """Entrada para búsqueda por categoría taxonómica."""
    slug: str = Field(..., min_length=1, description="Slug de la categoría (ej: 'salud-publica')")
    municipio: str | int | None = Field(None, description="Filtro opcional de municipio")
    anio: int | None = Field(None, ge=1900, le=2100, description="Año específico opcional")
    limit: int = Field(20, ge=1, le=100, description="Límite de resultados")


class SearchByYearRangeInput(BaseModel):
    """Entrada para búsqueda por rango de años."""
    desde: int = Field(..., ge=1900, le=2100, description="Año inicial inclusivo")
    hasta: int = Field(..., ge=1900, le=2100, description="Año final inclusivo")
    municipio: str | int | None = Field(None, description="Filtro opcional de municipio")
    tipo: TipoNorma = Field("ordenanza", description="Tipo de norma: ordenanza, decreto o todos")
    limit: int = Field(20, ge=1, le=100, description="Límite de resultados")

    @model_validator(mode="after")
    def validate_range(self) -> "SearchByYearRangeInput":
        if self.desde > self.hasta:
            raise ValueError(f"'desde' ({self.desde}) no puede ser mayor que 'hasta' ({self.hasta})")
        return self


class GetNormaInput(BaseModel):
    """Entrada para obtener el detalle de una norma por ID."""
    id: int = Field(..., gt=0, description="ID entero de la norma")


class GetAnexoInput(BaseModel):
    """Entrada para obtener un anexo por ID o por norma y número."""
    id: int | None = Field(None, gt=0, description="ID entero del anexo")
    norma_id: int | None = Field(None, gt=0, description="ID de la norma si no se usa ID de anexo")
    anexo_numero: str | None = Field(None, description="Número o nombre del anexo")

    @model_validator(mode="after")
    def validate_selector(self) -> "GetAnexoInput":
        if self.id is None and self.norma_id is None:
            raise ValueError("Debe especificarse 'id' del anexo o 'norma_id'")
        return self


class SearchByEntityInput(BaseModel):
    """Entrada para buscar normas que mencionen una entidad."""
    nombre: str = Field(..., min_length=1, description="Nombre de persona, empresa u organismo")
    tipo: str | None = Field(None, description="Tipo de entidad opcional (ej: persona, empresa, organismo)")
    municipio: str | int | None = Field(None, description="Filtro opcional de municipio")
    limit: int = Field(20, ge=1, le=100, description="Límite de resultados")


class GetReferencesInput(BaseModel):
    """Entrada para consultar el árbol de vigencia y referencias normativas."""
    norma_id: int = Field(..., gt=0, description="ID entero de la norma")
    direccion: Literal["ambas", "afecta_a", "afectada_por"] = Field(
        "ambas", description="Dirección de las referencias"
    )
    profundidad: int = Field(1, ge=1, le=5, description="Profundidad de relaciones (1 a 5)")
    limit: int = Field(50, ge=1, le=100, description="Límite de referencias a retornar")


class ListCategoriesInput(BaseModel):
    """Entrada para listar la taxonomía de categorías."""
    incluir_vacias: bool = Field(False, description="Incluir categorías sin normas asignadas")


class GetStatsInput(BaseModel):
    """Entrada para estadísticas generales del corpus."""
    municipio: str | int | None = Field(None, description="Municipio opcional para filtrar estadísticas")


class SimilarNormasInput(BaseModel):
    """Entrada para buscar normas semánticamente similares a una norma de referencia."""
    norma_id: int = Field(..., gt=0, description="ID de la norma de referencia")
    municipio: str | int | None = Field(None, description="Municipio opcional para acotar candidatos")
    limit: int = Field(10, ge=1, le=50, description="Cantidad de resultados similares")
    umbral: float = Field(0.5, ge=0.0, le=1.0, description="Umbral mínimo de similitud coseno (0.0 a 1.0)")


class SummarizeTextoInput(BaseModel):
    """Entrada para resumir texto con LLM."""
    texto: str = Field(..., min_length=1, max_length=100000, description="Texto a resumir")
    longitud: int = Field(50, ge=10, le=500, description="Longitud aproximada en palabras")
    estilo: EstiloResumen = Field("formal", description="Estilo: formal, simple o bullet-points")


class HealthCheckInput(BaseModel):
    """Entrada para health check."""
    pass


class SemanticSearchInput(BaseModel):
    """Entrada para búsqueda semántica libre en normas."""
    query: str = Field(..., min_length=1, description="Consulta en lenguaje natural")
    municipio: str | int | None = Field(None, description="Municipio opcional")
    tipo: TipoNorma = Field("ordenanza", description="Tipo de norma: ordenanza, decreto o todos")
    solo_vigentes: bool = Field(False, description="Filtrar solo normas vigentes")
    limit: int = Field(10, ge=1, le=50, description="Límite de resultados")
    umbral: float = Field(0.4, ge=0.0, le=1.0, description="Umbral de similitud")


class SemanticSearchArticulosInput(BaseModel):
    """Entrada para búsqueda semántica en artículos individuales."""
    query: str = Field(..., min_length=1, description="Consulta en lenguaje natural sobre disposiciones específicas")
    municipio: str | int | None = Field(None, description="Municipio opcional")
    solo_vigentes: bool = Field(False, description="Filtrar solo normas vigentes")
    limit: int = Field(10, ge=1, le=50, description="Límite de resultados")
    umbral: float = Field(0.4, ge=0.0, le=1.0, description="Umbral de similitud")


class FullSemanticSearchInput(BaseModel):
    """Entrada para búsqueda semántica combinada de normas y artículos."""
    query: str = Field(..., min_length=1, description="Consulta conceptual en lenguaje natural")
    municipio: str | int | None = Field(None, description="Municipio opcional")
    solo_vigentes: bool = Field(False, description="Filtrar solo normas vigentes")
    limit: int = Field(10, ge=1, le=50, description="Límite de resultados combinados")
    umbral: float = Field(0.4, ge=0.0, le=1.0, description="Umbral de similitud")


class CompilarTematicaInput(BaseModel):
    """Entrada para compilar un dossier temático normativo."""
    tema: str = Field(..., min_length=1, description="Tema central de compilación (ej: 'habitat', 'salud')")
    municipios: list[str | int] | None = Field(None, description="Lista opcional de municipios a incluir")
    desde: int | None = Field(None, ge=1900, le=2100, description="Año inicial opcional")
    hasta: int | None = Field(None, ge=1900, le=2100, description="Año final opcional")
    tipo: TipoNorma = Field("ordenanza", description="Tipo de norma a compilar (ordenanza por defecto)")
    solo_vigentes: bool = Field(False, description="Filtrar solo normas vigentes")
    cursor: int = Field(0, ge=0, description="Cursor de paginación (offset)")
    limit: int = Field(20, ge=1, le=100, description="Cantidad máxima de normas en este lote")

    @model_validator(mode="after")
    def validate_years(self) -> "CompilarTematicaInput":
        if self.desde is not None and self.hasta is not None and self.desde > self.hasta:
            raise ValueError(f"'desde' ({self.desde}) no puede ser mayor que 'hasta' ({self.hasta})")
        return self


class CompararIntermunicipalInput(BaseModel):
    """Entrada para comparación de antecedentes normativos intermunicipales."""
    tema: str = Field(..., min_length=1, description="Tema o materia a comparar (ej: 'banco de tierras')")
    municipio_destino: str | int = Field(108, description="Municipio destino evaluado (Saladillo por defecto: 108)")
    municipios_referencia: list[str | int] | None = Field(
        None, description="Municipios de referencia (ej: [130, 1]). Si es None, incluye todos los demás"
    )
    periodo_desde: int | None = Field(None, ge=1900, le=2100, description="Año mínimo de análisis")
    limit_candidatos: int = Field(20, ge=1, le=50, description="Máximo de candidatos de referencia a contrastar")


# =============================================================================
# SCHEMAS DE SALIDA Y ESTRUCTURAS DE DATOS
# =============================================================================

class CategoriaItem(BaseModel):
    id: int
    nombre: str
    slug: str
    descripcion: str | None = None
    parent_id: int | None = None
    parent_nombre: str | None = None
    normas_count: int = 0


class ArticuloDetail(BaseModel):
    id: int
    norma_id: int
    numero_articulo: str
    orden: int
    texto: str
    resumen: str | None = None
    estado: str = "vigente"


class ReferenciaDetail(BaseModel):
    id: int
    direccion: Literal["afecta_a", "afectada_por"]
    tipo_relacion: str
    norma_relacionada_id: int | None = None
    destino_tipo: str | None = None
    destino_numero: int | None = None
    destino_anio: int | None = None
    destino_referencia: str | None = None
    articulos_afectados: str | None = None
    texto_cita: str | None = None
    notas: str | None = None


class AnexoDetail(BaseModel):
    id: int
    norma_id: int
    nombre: str
    archivo_pdf: str | None = None
    url: str
    texto_extraido: str | None = None
    texto_disponible: bool = False


class NormaSummary(BaseModel):
    id: int
    tipo: str
    numero: int | None = None
    anio: int | None = None
    codigo_localidad: int
    localidad: str
    titulo: str
    resumen: str | None = None
    estado: str
    score: float | None = None
    headline: str | None = None
    categorias: list[str] = Field(default_factory=list)


class NormaDetail(BaseModel):
    id: int
    tipo: str
    numero: int | None = None
    anio: int | None = None
    numero_sibom: str | None = None
    fecha: str | None = None
    boletin: int | None = None
    version: str
    codigo_localidad: int
    localidad: str
    titulo: str
    seccion_visto: str | None = None
    seccion_considerando: str | None = None
    texto_completo: str
    estado: str
    notas_vigencia: str | None = None
    summary: str | None = None
    summary_trata: str | None = None
    summary_resuelve: str | None = None
    summary_depende: str | None = None
    url: str
    archivo_md: str
    articulos: list[ArticuloDetail] = Field(default_factory=list)
    referencias: list[ReferenciaDetail] = Field(default_factory=list)
    anexos: list[AnexoDetail] = Field(default_factory=list)
    categorias: list[str] = Field(default_factory=list)
