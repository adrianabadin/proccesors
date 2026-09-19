
import requests
import json
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# System prompt diseñado para extraction de normas legislativas PBA
SYSTEM_PROMPT = """# System Prompt - Extracción de Normas Legislativas (PBA - DeepSeek API)

**Role:** Experto en Análisis Normativo y Data Extraction con Expertise en Texto Legislativo.

**Task:** Procesar el HTML de una norma de la Provincia de Buenos Aires y devolver un JSON estrictamente estructurado con metadatos y articulado.

**INSTRUCCIONES:**

1. **Metadata Extraction**:
   - Identifica Tipo (LEY, DECRETO, RESOLUCION)
   - Extrae Número y Año (ej: "Ley 13413" -> numero: 13413, anio: 2006)
   - Identifica Fechas: fecha de promulgación y fecha de publicación
   - Detecta si la norma tiene algún indicador de estado
   - Extrae el título completo visible en el encabezado
   - Extrae el texto "Resumen" si está presente
   - Identifica el organismo emisor (Ministerio, Poder Ejecutivo, etc.)

2. **Article Structuring**:
   - Localiza todos los ARTICULO N. - o similar en el HTML
   - Extracción precisa: número del artículo (conserva formato: "1", "2 bis", "3", etc.)
   - Extracción del contenido: texto completo dentro de los paréntesis
   - Identifica elementos extra si existen (ANEXOS, considerando la estructura del HTML)

3. **Semantic Analysis**:
   - Detecta modificaciones explícitas: busca "Modifíquese el artículo X de la Ley Y" o similar
   - Identifica referencias cruzadas explícitas entre normas (ej: "esta norma reglamenta el artículo X de la Ley Y")
   - Determina el estado específico de cada artículo (Vigente, Derogado, Sustituido)

4. **Executive Summary**:
   - Genera un resumen ejecutivo de 3 párrafos centrado en:
     * Impacto jurídico principal
     * Contribución a la política pública de salud
     * Objetivo general de la norma

**OUTPUT FORMAT (strict JSON):**

```json
{
  "norma": {
    "tipo": "LEY|DECRETO|RESOLUCION",
    "numero": int,
    "anio": int,
    "fecha_sancion": "YYYY-MM-DD|null",
    "fecha_publicacion": "YYYY-MM-DD|null",
    "titulo": "string",
    "resumen": "string",
    "estado": "Vigente|Derogada|Modificada|null",
    "organismo_emisor": "string|null"
  },
  "articulos": [
    {
      "numero": "string (ej: \"1 bis\")",
      "contenido": "string (texto completo entre paréntesis)",
      "estado": "Vigente|Derogado|Sustituido|null"
    }
  ],
  "referencias_detectadas": [
    {
      "tipo": "Modifica|Deroga|Reglamenta|Cita",
      "destino_norma": "Ley 5116 (1947)|null",
      "articulo_afectado": "Artículo 2|null"
    }
  ],
  "resumen": "string (3 párrafos de impacto jurídico)"
}
```

**CONSTRAINTS:**
- No inventes datos. Si un dato no está en el HTML, devuelve null.
- Si no hay referencias explícitas, devuelve array vacío.
- El JSON debe ser válido y parseable (no comentarios).
- Asegúrate de capturar el número del artículo correctamente.
- No debes incluir referencias que no estén explícitas en el texto.
- El contenido del artículo debe ir en el orden cronológico.
"""

# Ejemplo de configuración
def extract_norma_from_html(html_content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae información estructurada de HTML usando DeepSeek API.

    Args:
        html_content: El HTML de la norma (texto actualizado)
        metadata: Metadatos básicos (url, tipo, número, etc.)

    Returns:
        JSON con metadatos completos y articulado
    """
    # En una implementación real, aquí conectarías con la API de DeepSeek
    # Ejemplo de implementación:

    prompt = f"""Analiza el siguiente HTML de una norma de PBA y extrae la información solicitada.

METADATOS:
{json.dumps(metadata, ensure_ascii=False, indent=2)}

HTML:
{html_content}

Genera un JSON con el siguiente formato:
{SYSTEM_PROMPT}
"""

    # Lógica para llamar a la API de DeepSeek...
    # Esta es solo una estructura de ejemplo
    return {
        "norma": {
            "tipo": metadata.get("tipo_norma"),
            "numero": metadata.get("numero_norma"),
            "anio": metadata.get("anio"),
            "titulo": "Ley 13413",
            "resumen": "Creación del Seguro Público de Salud de la Provincia de Buenos Aires (SPS)",
            "estado": "Vigente",
            "organismo_emisor": "Honorable Senado y Cámara de Diputados de la Provincia de Buenos Aires"
        },
        "articulos": [
            {"numero": "1", "contenido": "Créase el Seguro Público de Salud de la Provincia de Buenos Aires (SPS)...", "estado": "Vigente"},
            {"numero": "2", "contenido": "Serán objetivos del Seguro Público de Salud los siguientes: a) Ejecutar acciones de promoción...", "estado": "Vigente"},
            {"numero": "3", "contenido": "Las acciones generales que deberán cumplirse para el logro de los objetivos señalados en el artículo precedente...", "estado": "Vigente"},
            {"numero": "4", "contenido": "La Administración del Seguro creado por la presente Ley funcionará con la estructura orgánica necesaria...", "estado": "Vigente"}
        ],
        "referencias_detectadas": [],
        "resumen": "Esta norma crea el Seguro Público de Salud de la Provincia de Buenos Aires (SPS) como mecanismo de aseguramiento público de la atención de la salud de las personas con residencia en el territorio bonaerense que carezcan de cobertura. Establece los objetivos del seguro, incluyendo acciones de promoción, protección, recuperación y rehabilitación de la salud, así como mecanismos de financiamiento y gestión eficiente."
    }

def main():
    # Procesar el archivo de ejemplo
    input_file = "data/pba/salud_sample.json"

    if not os.path.exists(input_file):
        print(f"❌ Archivo no encontrado: {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        normas_sample = json.load(f)

    print(f"📊 Procesando {len(normas_sample)} normas de ejemplo...")

    for i, norma in enumerate(normas_sample, 1):
        print(f"📄 Procesando {i}/{len(normas_sample)}: {norma['titulo']}")

        # Extraer datos
        resultado = extract_norma_from_html(
            html_content="<HTML_DE_EXEMPLO>",
            metadata=norma
        )

        # Imprimir resultados
        print(f"  ✅ Tipo: {resultado['norma']['tipo']}")
        print(f"  ✅ Artículos: {len(resultado['articulos'])}")
        print(f"  ✅ Resumen: {resultado['norma']['resumen'][:100]}...")

    print(f"\n✅ Procesamiento completado exitosamente.")

if __name__ == "__main__":
    main()
