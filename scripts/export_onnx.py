"""
Script para exportar el mejor modelo entrenado (best_model.pth) a formato ONNX.
"""

import os
import json
from pathlib import Path
import torch
import torch.nn as nn
from torchvision import models
import onnxruntime as ort

CANONICAL_CLASSES = ["botrytis", "mancha_negra", "oidio", "roya", "sano", "vello"]


def export():
    models_dir = Path("models")
    weights_path = models_dir / "best_model.pth"
    onnx_path = models_dir / "rose_disease_model.onnx"
    classes_path = models_dir / "classes.json"

    print(f"[*] Cargando pesos desde: {weights_path}")
    model = models.mobilenet_v3_large(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, len(CANONICAL_CLASSES))

    model.load_state_dict(torch.load(weights_path, map_location="cpu", weights_only=True))
    model.eval()

    # Guardar classes.json si no existe
    with open(classes_path, "w", encoding="utf-8") as f:
        json.dump(CANONICAL_CLASSES, f, indent=2)
    print(f"[✓] classes.json generado en: {classes_path}")

    # Exportar a ONNX
    print(f"[*] Exportando a: {onnx_path}")
    dummy_input = torch.randn(1, 3, 224, 224)

    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
    )

    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"[✓] Modelo ONNX exportado exitosamente. Tamaño: {size_mb:.2f} MB")

    # Validar inferencia con onnxruntime
    session = ort.InferenceSession(str(onnx_path))
    outputs = session.run(None, {"input": dummy_input.numpy()})
    print(f"[✓] Inferencia ONNX verificada. Salida shape: {outputs[0].shape}")


if __name__ == "__main__":
    export()
