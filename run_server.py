"""
Punto de Entrada Principal para levantar el Servidor Mr. Rose MCP y API Móvil.
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def main():
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))

    print("=" * 65)
    print("   🌹 INICIANDO SERVIDOR MR. ROSE MCP & MOBILE BACKEND 🌹")
    print("=" * 65)
    print(f"[*] Escuchando en: http://{host}:{port}")
    print(f"[*] Documentación Interactiva (Swagger): http://localhost:{port}/docs")
    print(f"[*] Endpoint Móvil (Cámara/Archivo): POST http://localhost:{port}/api/v1/diagnose/file")
    print(f"[*] Endpoint Móvil (Base64): POST http://localhost:{port}/api/v1/diagnose/base64")
    print(f"[*] Catálogo de Enfermedades: GET http://localhost:{port}/api/v1/diseases")
    print("=" * 65)

    uvicorn.run("src.mcp_server.api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
