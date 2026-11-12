# Mr. Rose MCP 🌹🍃

Sistema de diagnóstico inteligente y asistencia fitopatológica para el cultivo de rosas en Ecuador (Pichincha y Cotopaxi), basado en visión artificial y el **Model Context Protocol (MCP)**.

---

## 🎯 Objetivo
Proporcionar un diagnóstico temprano, interactivo y agronómicamente riguroso para las 5 principales enfermedades de la rosa:
1. **Botrytis** (*Botrytis cinerea*)
2. **Oídio** (*Podosphaera pannosa*)
3. **Vello o Mildiu Velloso** (*Peronospora sparsa*)
4. **Roya del Rosal** (*Phragmidium mucronatum*)
5. **Mancha Negra** (*Diplocarpon rosae*)
6. **Tejido Sano** (*Healthy*)

---

## 🏗️ Arquitectura Híbrida (Enfoque C)

```
[Foto de la Rosa] 
        │
        ├──> [Clasificador Ligero ONNX (MobileNetV3)]
        │            └── Vector de probabilidades cuantitativas
        │
        └──> [Motor Fitopatológico MCP + Google AI Studio (Gemini)]
                     ├── Inyección de matriz agronómica de Ecuador
                     ├── Evaluación de ambigüedad diferencial
                     └── Solicitud guiada de segunda foto (ej: envés) si confianza < 80%
```

---

## 📁 Estructura del Proyecto

```text
MCP_MrRose/
├── data/
│   ├── raw/                 # Datasets originales (.zip o carpetas crudas)
│   └── processed/           # Imágenes normalizadas y particionadas
│       ├── train/           # 70%
│       ├── val/             # 15%
│       └── test/            # 15%
├── models/                  # Pesos del modelo exportado (.onnx)
├── src/
│   ├── knowledge/           # Matriz agronómica de Pichincha y Cotopaxi
│   ├── services/            # Inferencia y conexión con Gemini
│   └── mcp_server/          # Herramientas MCP y endpoints HTTP/SSE
├── scripts/
│   ├── import_dataset.py    # Descompresión y carga de zips
│   ├── prepare_data.py      # Normalización y partición estratificada
│   └── train.py             # Pipeline de entrenamiento y exportación
├── requirements.txt         # Dependencias
└── .env.example             # Plantilla de variables de entorno
```

---

## 🚀 Cómo Ejecutar el Sistema

### 1. Iniciar el Servidor MCP (Model Context Protocol)
Para clientes MCP como Antigravity, Claude Desktop o agentes:
```powershell
.\.venv\Scripts\python.exe -m src.mcp_server.server
```

### 2. Iniciar la API REST / Gateway para App Móvil
Para conectar tu aplicación móvil o probar desde Swagger UI:
```powershell
.\.venv\Scripts\python.exe -m uvicorn src.mcp_server.api:app --reload --host 0.0.0.0 --port 8000
```
* **Documentación interactiva (Swagger):** Abre tu navegador en [http://localhost:8000/docs](http://localhost:8000/docs)
* **Endpoint para fotos de la cámara:** `POST /api/v1/diagnose/file`
* **Endpoint para base64:** `POST /api/v1/diagnose/base64`

---

## 📊 Resultados de la Evaluación del Modelo en TEST (2,092 imágenes)
* **Accuracy Global:** **96.41%**
* **F1-Score Ponderado:** **0.97**
* **Oídio:** Precision 100% | Recall 100%
* **Roya:** Precision 100% | Recall 100%
* **Mancha Negra:** Precision 100% | Recall 99%
* **Vello:** Precision 98% | Recall 100%
* **Sano:** Precision 99% | Recall 93%
* **Botrytis:** Precision 57% | Recall 93%
