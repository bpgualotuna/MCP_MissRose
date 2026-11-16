"""
API REST y Wrapper HTTP/SSE para conectar Mr. Rose MCP con Aplicaciones Móviles.
Permite subir imágenes directamente desde la cámara del smartphone (multipart o base64).
"""

import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.diagnostic_engine import DiagnosticEngine
from src.knowledge.disease_catalog import CATALOGO_ENFERMEDADES

app = FastAPI(
    title="Mr. Rose - Pathology API & Mobile Gateway",
    description="Servidor de diagnóstico fitopatológico de rosas para Ecuador conectado al protocolo MCP.",
    version="1.0.0"
)

# Habilitar CORS para permitir llamadas desde aplicaciones móviles y web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DiagnosticEngine()


class Base64DiagnosisRequest(BaseModel):
    image_base64: str
    context_notes: Optional[str] = None


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Mr. Rose Pathology Engine",
        "model_ready": engine.classifier.is_ready(),
        "gemini_ready": engine.gemini.is_available()
    }


@app.post("/api/v1/diagnose/file", summary="Diagnosticar subiendo archivo de imagen (Recomendado para App Móvil)")
async def diagnose_file(
    file: UploadFile = File(..., description="Fotografía tomada desde la cámara del móvil"),
    second_angle_file: Optional[UploadFile] = File(None, description="Segunda fotografía opcional (ej. envés de la hoja)"),
    context_notes: Optional[str] = Form(None, description="Notas de campo (lugar, humedad, etc.)")
):
    try:
        contents = await file.read()
        second_contents = await second_angle_file.read() if second_angle_file is not None else None
        if second_contents is not None and len(second_contents) == 0:
            second_contents = None
        result = engine.diagnose(
            image_input=contents,
            context_notes=context_notes,
            second_image_input=second_contents
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/diagnose/base64", summary="Diagnosticar enviando string en base64")
def diagnose_base64(request: Base64DiagnosisRequest):
    try:
        result = engine.diagnose(
            image_input=request.image_base64,
            context_notes=request.context_notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/diseases", summary="Listar catálogo fitopatológico completo")
def list_diseases():
    return engine.get_disease_catalog()


@app.get("/api/v1/diseases/{disease_id}", summary="Consultar ficha de una enfermedad específica")
def get_disease_detail(disease_id: str):
    clean_id = disease_id.strip().lower()
    if clean_id in CATALOGO_ENFERMEDADES:
        return CATALOGO_ENFERMEDADES[clean_id].model_dump()
    raise HTTPException(status_code=404, detail=f"Enfermedad '{disease_id}' no encontrada.")


@app.get("/api/v1/guide", summary="Obtener guía fotográfica y ángulos recomendados")
def get_guide():
    return engine.get_photography_guide()


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run("src.mcp_server.api:app", host=host, port=port, reload=True)
