"""
Script de importación y descompresión de datasets para el proyecto Mr. Rose.
Permite importar archivos .zip descargados de Kaggle, Mendeley u otras fuentes.
"""

import sys
import zipfile
import tarfile
import shutil
from pathlib import Path
import argparse


def extract_archive(archive_path: Path, target_dir: Path):
    print(f"[*] Descomprimiendo: {archive_path.name} -> {target_dir}")
    if archive_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
    elif archive_path.suffix.lower() in [".tar", ".gz", ".tgz"]:
        with tarfile.open(archive_path, 'r:*') as tar_ref:
            tar_ref.extractall(target_dir)
    else:
        print(f"[!] Formato no soportado: {archive_path.suffix}")
        return False
    print(f"[✓] Descompresión exitosa de {archive_path.name}")
    return True


def scan_and_extract_raw(raw_dir: Path):
    archives = list(raw_dir.glob("*.zip")) + list(raw_dir.glob("*.tar.gz")) + list(raw_dir.glob("*.tgz"))
    if not archives:
        print(f"[-] No se encontraron archivos comprimidos (.zip, .tar.gz) en: {raw_dir}")
        print("    Coloca tus archivos descargados de Kaggle/Mendeley dentro de 'data/raw/' y vuelve a ejecutar.")
        return 0

    extracted_count = 0
    for archive in archives:
        extract_folder = raw_dir / archive.stem
        extract_folder.mkdir(exist_ok=True)
        if extract_archive(archive, extract_folder):
            extracted_count += 1

    return extracted_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descomprimir datasets en data/raw/")
    parser.add_argument("--file", type=str, default=None, help="Ruta específica a un archivo .zip")
    parser.add_argument("--dest", type=str, default="data/raw", help="Carpeta destino")
    args = parser.parse_args()

    dest_path = Path(args.dest)
    dest_path.mkdir(parents=True, exist_ok=True)

    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            extract_archive(file_path, dest_path / file_path.stem)
        else:
            print(f"[!] Error: El archivo {file_path} no existe.")
    else:
        scan_and_extract_raw(dest_path)
