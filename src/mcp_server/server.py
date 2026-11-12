"""
Servidor MCP Oficial para Mr. Rose (Model Context Protocol).
Expone herramientas especializadas en fitopatología de rosas para clientes MCP y agentes.
"""

import os
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

from src.services.diagnostic_engine import DiagnosticEngine
from src.knowledge.disease_catalog import CATALOGO_ENFERMEDADES, MAPA_ID_A_NOMBRE

# Instanciar el servidor FastMCP
mcp = FastMCP(
    name="MrRose-Pathology-MCP",
    instructions="Servidor experto en diagnóstico fitopatológico y asistencia agronómica para rosas en Ecuador."
)

# Instanciar el motor orquestador
engine = DiagnosticEngine()


@mcp.tool(
    name="diagnosticar_enfermedad_rosa",
    description="Analiza una fotografía de una rosa (vía ruta de archivo local o string base64) para detectar Botrytis, Oídio, Vello, Roya o Mancha Negra, emitiendo diagnóstico diferencial, severidad, manejo agronómico y guía de segunda foto si se requiere."
)
def diagnosticar_enfermedad_rosa(
    imagen: str,
    notas_contexto: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parámetros:
    - imagen: Ruta absoluta o relativa al archivo de imagen, o string codificado en base64.
    - notas_contexto: Información complementaria (ej: 'invernadero en Lasso Cotopaxi, riego por aspersión').
    """
    return engine.diagnose(image_input=imagen, context_notes=notas_contexto)


@mcp.tool(
    name="consultar_ficha_enfermedad",
    description="Obtiene la ficha técnica agronómica completa de una enfermedad de rosa según la literatura de Ecuador (agente causal, síntomas, condiciones favorables y manejo integrado)."
)
def consultar_ficha_enfermedad(enfermedad_id: str) -> Dict[str, Any]:
    """
    Parámetros:
    - enfermedad_id: 'botrytis', 'oidio', 'vello', 'roya', 'mancha_negra' o 'sano'.
    """
    clean_id = enfermedad_id.strip().lower()
    if clean_id in CATALOGO_ENFERMEDADES:
        return CATALOGO_ENFERMEDADES[clean_id].model_dump()
    return {
        "error": f"Enfermedad '{enfermedad_id}' no reconocida.",
        "opciones_validas": list(CATALOGO_ENFERMEDADES.keys())
    }


@mcp.tool(
    name="obtener_guia_fotografica",
    description="Retorna las recomendaciones técnicas de captura fotográfica en campo/invernadero para maximizar la precisión diagnóstica (iluminación, ángulos y enfoque del envés)."
)
def obtener_guia_fotografica() -> Dict[str, Any]:
    return engine.get_photography_guide()


@mcp.tool(
    name="listar_enfermedades_soportadas",
    description="Lista el catálogo de patologías evaluadas por el sistema con sus nombres científicos."
)
def listar_enfermedades_soportadas() -> List[Dict[str, str]]:
    return [
        {
            "id": eid,
            "nombre_comun": info.nombre_comun,
            "nombre_cientifico": info.nombre_cientifico,
            "tipo_patogeno": info.tipo_patogeno
        }
        for eid, info in CATALOGO_ENFERMEDADES.items()
    ]


if __name__ == "__main__":
    # Ejecutar servidor MCP por stdio por defecto
    mcp.run()
