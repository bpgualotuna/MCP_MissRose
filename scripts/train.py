"""
Pipeline de Entrenamiento y Exportación ONNX para Mr. Rose MCP.
Entrena MobileNetV3-Large con Transfer Learning para las 6 clases fitopatológicas.
"""

import os
import sys
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

# Clases canónicas en orden estricto de torchvision (alfabético)
CANONICAL_CLASSES = ["botrytis", "mancha_negra", "oidio", "roya", "sano", "vello"]


def get_data_loaders(data_dir: Path, batch_size=32, num_workers=2):
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(degrees=20),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = datasets.ImageFolder(data_dir / "train", transform=train_transform)
    val_dataset = datasets.ImageFolder(data_dir / "val", transform=val_test_transform)
    test_dataset = datasets.ImageFolder(data_dir / "test", transform=val_test_transform)

    # Validar coincidencia de clases
    print(f"[*] Clases detectadas en ImageFolder: {train_dataset.classes}")
    assert train_dataset.classes == CANONICAL_CLASSES, f"Discrepancia en clases: {train_dataset.classes} vs {CANONICAL_CLASSES}"

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, test_loader, train_dataset.targets


def calculate_class_weights(targets, num_classes=6):
    counts = np.bincount(targets, minlength=num_classes)
    total = len(targets)
    # Ponderación inversa suavizada
    weights = total / (num_classes * counts.astype(np.float32) + 1e-5)
    weights = weights / weights.sum() * num_classes
    print("\n[+] Pesos de clase balanceados:")
    for cls_name, count, w in zip(CANONICAL_CLASSES, counts, weights):
        print(f"    - {cls_name.ljust(15)}: {count:>5} muestras | Peso Loss: {w:.3f}")
    return torch.tensor(weights, dtype=torch.float32)


def build_model(num_classes=6):
    print("\n[*] Descargando e instanciando MobileNetV3-Large con pesos ImageNet...")
    model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.DEFAULT)
    
    # Reemplazar la capa clasificadora final
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(labels).sum().item()
        total += labels.size(0)

    return running_loss / total, correct / total


def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, preds = outputs.max(1)
            correct += preds.eq(labels).sum().item()
            total += labels.size(0)

            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())

    return running_loss / total, correct / total, np.array(all_preds), np.array(all_targets)


def export_to_onnx(model, onnx_path: Path):
    print(f"\n[*] Exportando modelo a ONNX en: {onnx_path}")
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224)
    
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
    )
    
    file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"[✓] Modelo exportado exitosamente. Tamaño: {file_size_mb:.2f} MB")

    # Verificación con onnxruntime
    import onnxruntime as ort
    session = ort.InferenceSession(str(onnx_path))
    test_out = session.run(None, {"input": dummy_input.numpy()})
    print(f"[✓] Verificación ONNX Runtime superada. Forma de salida: {test_out[0].shape}")


def run_training(epochs=12, batch_size=32, lr=1e-3):
    data_dir = Path("data/processed")
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"============================================================")
    print(f"   ENTRENAMIENTO MR. ROSE - MOBILENETV3 (6 CLASES)")
    print(f"   Dispositivo: {device} | Épocas: {epochs} | Batch: {batch_size}")
    print(f"============================================================")

    train_loader, val_loader, test_loader, targets = get_data_loaders(data_dir, batch_size=batch_size, num_workers=0)
    class_weights = calculate_class_weights(targets).to(device)

    model = build_model(num_classes=len(CANONICAL_CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_loss = float("inf")
    best_weights_path = models_dir / "best_model.pth"

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        ep_start = time.time()
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, _, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step()
        ep_time = time.time() - ep_start

        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_weights_path)

        flag = " [BEST]" if is_best else ""
        print(f"Época [{epoch:>2}/{epochs:>2}] ({ep_time:.1f}s) | "
              f"Train Loss: {train_loss:.4f} - Acc: {train_acc*100:.2f}% | "
              f"Val Loss: {val_loss:.4f} - Acc: {val_acc*100:.2f}%{flag}")

    total_time = (time.time() - start_time) / 60
    print(f"\n[✓] Entrenamiento finalizado en {total_time:.2f} minutos.")

    # Cargar mejores pesos para evaluación final
    print("\n[*] Evaluando mejor modelo sobre el conjunto TEST...")
    model.load_state_dict(torch.load(best_weights_path, weights_only=True))
    test_loss, test_acc, preds, truths = evaluate(model, test_loader, criterion, device)

    report_dict = classification_report(truths, preds, target_names=CANONICAL_CLASSES, output_dict=True)
    report_text = classification_report(truths, preds, target_names=CANONICAL_CLASSES)
    cm = confusion_matrix(truths, preds).tolist()

    print("\n--- REPORTE DE EVALUACIÓN FINAL (TEST) ---")
    print(report_text)
    print(f"Test Accuracy Global: {test_acc*100:.2f}%")

    metrics_file = models_dir / "evaluation_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_accuracy": test_acc,
            "test_loss": test_loss,
            "classification_report": report_dict,
            "confusion_matrix": cm,
            "canonical_classes": CANONICAL_CLASSES
        }, f, indent=2, ensure_ascii=False)
    print(f"[✓] Métricas guardadas en: {metrics_file}")

    with open(models_dir / "classes.json", "w", encoding="utf-8") as f:
        json.dump(CANONICAL_CLASSES, f, indent=2)

    # Exportar a ONNX
    onnx_path = models_dir / "rose_disease_model.onnx"
    export_to_onnx(model.to("cpu"), onnx_path)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=12, help="Número de épocas")
    parser.add_argument("--batch_size", type=int, default=32, help="Tamaño de batch")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    run_training(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
