"""
Servicio de Inferencia Local con ONNX Runtime para Mr. Rose MCP.
Carga el modelo MobileNetV3 optimizado y entrega probabilidades cuantitativas por clase.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from PIL import Image

CLASSES_FILE = Path("models/classes.json")
MODEL_PATH = Path("models/rose_disease_model.onnx")

# Mapeo por defecto en orden canónico
DEFAULT_CLASSES = ["botrytis", "mancha_negra", "oidio", "roya", "sano", "vello"]

# Estadísticas de normalización de ImageNet
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class ClassifierService:
    def __init__(self, model_path: Path = MODEL_PATH, classes_path: Path = CLASSES_FILE):
        self.model_path = model_path
        self.classes = self._load_classes(classes_path)
        self.session = None
        self._init_session()

    def _load_classes(self, classes_path: Path) -> List[str]:
        if classes_path.exists():
            with open(classes_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_CLASSES

    def _init_session(self):
        if self.model_path.exists():
            import onnxruntime as ort
            # Usar proveedores optimizados disponibles (CPUExecutionProvider por defecto)
            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=["CPUExecutionProvider"]
            )
            print(f"[✓] ClassifierService: Modelo ONNX cargado desde {self.model_path}")
        else:
            print(f"[!] ClassifierService: Archivo {self.model_path} no encontrado aún (entrenamiento en curso).")

    def is_ready(self) -> bool:
        if self.session is None and self.model_path.exists():
            self._init_session()
        return self.session is not None

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Redimensiona a 224x224, convierte a RGB, normaliza y transpone a (1, 3, 224, 224).
        """
        img = image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
        # De (H, W, C) a (1, C, H, W)
        tensor = np.transpose(arr, (2, 0, 1))
        return np.expand_dims(tensor, axis=0)

    def softmax(self, logits: np.ndarray, temperature: float = 2.5) -> np.ndarray:
        """Softmax con Temperature Scaling para evitar sobreconfianza extrema fuera de dominio."""
        scaled = logits / temperature
        exp_logits = np.exp(scaled - np.max(scaled))
        return exp_logits / np.sum(exp_logits)

    def predict(self, image: Image.Image) -> Dict[str, float]:
        """
        Ejecuta la inferencia y devuelve un diccionario con las probabilidades de cada clase.
        """
        if not self.is_ready():
            # Si el modelo aún está entrenando, devuelve distribución uniforme de respaldo
            uniform_prob = 1.0 / len(self.classes)
            return {cls_name: round(uniform_prob, 4) for cls_name in self.classes}

        input_tensor = self.preprocess_image(image)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: input_tensor})
        logits = outputs[0][0]
        probs = self.softmax(logits)

        return {self.classes[i]: float(round(probs[i], 4)) for i in range(len(self.classes))}
