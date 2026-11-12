"""
Script de preprocesamiento, normalización y partición estratificada de imágenes
para el proyecto Mr. Rose MCP.
"""

import os
import sys
import shutil
import random
import argparse
import json
from pathlib import Path
from PIL import Image

# Clases canónicas del proyecto
CANONICAL_CLASSES = ["sano", "botrytis", "oidio", "vello", "roya", "mancha_negra"]

# Mapeo de sinónimos habituales en Mendeley/Kaggle a nombres canónicos
CLASS_SYNONYMS = {
    # Sano
    "healthy": "sano",
    "fresh": "sano",
    "healthy_leaf": "sano",
    "healthy_leaves": "sano",
    "fresh_leaf": "sano",
    "sano": "sano",
    "saludable": "sano",

    # Botrytis
    "botrytis": "botrytis",
    "botrytis_blight": "botrytis",
    "botrytis_cinerea": "botrytis",
    "gray_mold": "botrytis",
    "grey_mold": "botrytis",
    "gray_mould": "botrytis",
    "moho_gris": "botrytis",

    # Oídio
    "powdery_mildew": "oidio",
    "powderymildew": "oidio",
    "oidio": "oidio",
    "mildeo_polvoriento": "oidio",

    # Vello / Mildiu velloso
    "downy_mildew": "vello",
    "downymildew": "vello",
    "vello": "vello",
    "mildiu_velloso": "vello",
    "peronospora": "vello",

    # Roya
    "rust": "roya",
    "rose_rust": "roya",
    "roya": "roya",
    "phragmidium": "roya",

    # Mancha negra
    "black_spot": "mancha_negra",
    "blackspot": "mancha_negra",
    "mancha_negra": "mancha_negra",
    "diplocarpon": "mancha_negra"
}

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def normalize_class_name(name: str) -> str:
    cleaned = name.strip().lower().replace(" ", "_").replace("-", "_")
    for key, canonical in CLASS_SYNONYMS.items():
        if key in cleaned:
            return canonical
    return "desconocido"


def validate_image(filepath: Path) -> bool:
    try:
        with Image.open(filepath) as img:
            img.verify()
        with Image.open(filepath) as img:
            img.load()
            if img.size[0] < 32 or img.size[1] < 32:
                return False
        return True
    except Exception:
        return False


def process_dataset(raw_dir: Path, output_dir: Path, split_ratios=(0.70, 0.15, 0.15), seed=42):
    random.seed(seed)
    train_ratio, val_ratio, test_ratio = split_ratios
    assert round(train_ratio + val_ratio + test_ratio, 2) == 1.0, "Los ratios deben sumar 1.0"

    print(f"[*] Analizando origen: {raw_dir}")
    print(f"[*] Destino: {output_dir}")

    # Estructura de salida
    for split in ["train", "val", "test"]:
        for cls in CANONICAL_CLASSES:
            (output_dir / split / cls).mkdir(parents=True, exist_ok=True)

    # Escanear carpetas
    collected_images = {cls: [] for cls in CANONICAL_CLASSES}
    ignored_images = []

    for root, dirs, files in os.walk(raw_dir):
        root_path = Path(root)
        # Ignorar exclusivamente subcarpetas de marigold (caléndula)
        if any(part.lower() == "marigold" for part in root_path.parts):
            continue

        current_class = normalize_class_name(root_path.name)
        if current_class == "desconocido" and root_path.parent != raw_dir:
            current_class = normalize_class_name(root_path.parent.name)

        for file in files:
            file_path = root_path / file
            if file_path.suffix.lower() not in VALID_EXTENSIONS:
                continue

            if current_class in CANONICAL_CLASSES:
                if validate_image(file_path):
                    collected_images[current_class].append(file_path)
                else:
                    ignored_images.append((str(file_path), "imagen corrupta o demasiado pequeña"))
            else:
                ignored_images.append((str(file_path), f"clase no reconocida: {root_path.name}"))

    # Partición y copia
    summary = {
        "total_valid": sum(len(v) for v in collected_images.values()),
        "total_ignored": len(ignored_images),
        "by_class": {},
        "splits": {"train": 0, "val": 0, "test": 0}
    }

    print("\n[+] Resumen de recolección:")
    for cls in CANONICAL_CLASSES:
        images = collected_images[cls]
        random.shuffle(images)
        total = len(images)
        n_train = int(total * train_ratio)
        n_val = int(total * val_ratio)

        train_imgs = images[:n_train]
        val_imgs = images[n_train:n_train + n_val]
        test_imgs = images[n_train + n_val:]

        splits_map = {"train": train_imgs, "val": val_imgs, "test": test_imgs}
        for split_name, img_list in splits_map.items():
            for idx, src_img in enumerate(img_list):
                ext = src_img.suffix.lower()
                dest_name = f"{cls}_{split_name}_{idx:05d}{ext}"
                dest_path = output_dir / split_name / cls / dest_name
                shutil.copy2(src_img, dest_path)
                summary["splits"][split_name] += 1

        summary["by_class"][cls] = {
            "total": total,
            "train": len(train_imgs),
            "val": len(val_imgs),
            "test": len(test_imgs)
        }
        print(f"  - {cls.ljust(15)}: Total={total:>4} | Train={len(train_imgs):>4} | Val={len(val_imgs):>4} | Test={len(test_imgs):>4}")

    summary_file = output_dir / "dataset_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Proceso completado. Resumen guardado en: {summary_file}")
    if ignored_images:
        print(f"[!] Advertencia: {len(ignored_images)} archivos ignorados (revisa dataset_summary.json)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocesar y particionar datasets de rosas")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Ruta de carpetas crudas")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Ruta de destino")
    args = parser.parse_args()

    process_dataset(Path(args.raw_dir), Path(args.output_dir))
