"""
Motor Orquestador de Diagnóstico Agronómico para Mr. Rose MCP.
Coordina el preprocesamiento de imágenes, el clasificador de visión artificial
y el agente agronómico multimodal de Google AI Studio.
"""

import io
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image

from src.services.classifier_service import ClassifierService
from src.services.gemini_service import GeminiService
from src.knowledge.disease_catalog import CATALOGO_ENFERMEDADES, MAPA_ID_A_NOMBRE


class DiagnosticEngine:
    def __init__(self):
        self.classifier = ClassifierService()
        self.gemini = GeminiService()

    def _load_image(self, image_input: Union[str, Path, bytes, Image.Image]) -> Image.Image:
        """
        Carga una imagen desde una ruta en disco, un string en base64, bytes crudos o un objeto PIL.
        """
        if isinstance(image_input, Image.Image):
            return image_input

        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if path.exists():
                return Image.open(path)
            # Si no existe como ruta de archivo, intentar decodificar como base64
            if isinstance(image_input, str):
                cleaned = image_input
                if "base64," in cleaned:
                    cleaned = cleaned.split("base64,")[1]
                img_bytes = base64.b64decode(cleaned)
                return Image.open(io.BytesIO(img_bytes))

        if isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input))

        raise ValueError("Formato de imagen no soportado o archivo no encontrado.")

    def diagnose(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        context_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Flujo completo de diagnóstico:
        1. Carga y valida imagen.
        2. Inferencia cuantitativa local (ONNX).
        3. Enriquecimiento fitopatológico y razonamiento (Gemini / Reglas Ecuador).
        """
        image = self._load_image(image_input)

        # 1. Probabilidades del modelo entrenado
        classifier_probs = self.classifier.predict(image)

        # 2. Análisis multimodal agronómico
        diagnostic_result = self.gemini.analyze_image(
            image=image,
            classifier_probs=classifier_probs,
            context_notes=context_notes
        )

        # 3. Adjuntar metadatos de las probabilidades cuantitativas locales para trazabilidad
        diagnostic_result["probabilidades_modelo_local"] = classifier_probs

        return diagnostic_result

    def get_disease_catalog(self) -> Dict[str, Any]:
        """
        Retorna la base de conocimiento fitopatológica completa de Ecuador.
        """
        return {eid: info.model_dump() for eid, info in CATALOGO_ENFERMEDADES.items()}

    def get_photography_guide(self) -> Dict[str, Any]:
        """
        Retorna la guía técnica para la captura de fotos en invernadero/campo.
        """
        return {
            "recomendaciones_generales": [
                "Luz natural difusa (evitar sol directo de mediodía que quema la imagen o sombras oscuras)",
                "Enfocar la cámara perpendicularmente a la lesión",
                "Evitar fotos con movimiento o desenfocadas",
                "Capturar una foto del haz (frente) y una foto del envés (dorso) si hay sospecha de manchas foliares",
                "En botones y flores, enfocar en primer plano la unión del cáliz y los pétalos exteriores"
            ],
            "puntos_criticos_por_enfermedad": {
                "botrytis": "Fotografiar pétalos senescentes, botones cerrados que no abren o base de la flor.",
                "vello_vs_oidio": "EL ENVÉS ES DECISIVO. El vello muestra esporas violáceas solo abajo; el oídio muestra polvo blanco arriba y abajo.",
                "roya": "Enfocar el envés de las hojas inferiores (basales) donde brotan las pústulas naranjas.",
                "mancha_negra": "Enfocar las hojas medias e inferiores buscando el margen plumoso y halo amarillo."
            }
        }
