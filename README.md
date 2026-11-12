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

## 🚀 Inicio Rápido (Fase 1: Preparación de Datos)

### 1. Activar el Entorno Virtual
En Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias base
```powershell
pip install -r requirements.txt
```

### 3. Cargar los Datasets
Coloca los archivos `.zip` descargados de Kaggle o Mendeley en `data/raw/` y ejecuta:
```powershell
python scripts/import_dataset.py
```

### 4. Normalizar y Particionar
```powershell
python scripts/prepare_data.py
```
Esto creará la partición estratificada 70/15/15 en `data/processed/` y generará `dataset_summary.json`.
