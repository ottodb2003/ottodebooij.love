#!/usr/bin/env python3
"""
convert_to_png.py
Rekursiv alle Bilder in PNGs umwandeln, Ordnerstruktur wird gespiegelt.

Beispiel:
    python convert_to_png.py /pfad/zu/EXPO
    python convert_to_png.py /pfad/zu/EXPO --out /pfad/zu/EXPO_png --delete-originals
"""

import argparse
import os
import shutil
from pathlib import Path

from PIL import Image, ImageOps

# Häufige Bild-Endungen (bei Bedarf erweitern)
SUPPORTED_EXTS = {
    ".jpg", ".jpeg", ".jpe", ".jfif",
    ".png",
    ".tif", ".tiff",
    ".bmp",
    ".webp",
    ".heic", ".heif",   # benötigt ggf. zusätzliche Pillow-Plugins
    ".gif",
    ".ppm", ".pgm", ".pbm",
    ".ico"
}

def has_alpha(img: Image.Image) -> bool:
    """Erkennen, ob ein Bild Transparenz besitzt."""
    if img.mode in ("RGBA", "LA"):
        return True
    if img.mode == "P":
        return "transparency" in img.info
    return False

def convert_image_to_png(src_path: Path, dst_path: Path) -> bool:
    """
    Konvertiert ein einzelnes Bild nach PNG.
    Gibt True zurück, wenn erzeugt/überschrieben wurde, sonst False.
    """
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(src_path) as im:
            # EXIF-Ausrichtung berücksichtigen
            im = ImageOps.exif_transpose(im)

            # Modus passend wählen
            if has_alpha(im):
                if im.mode not in ("RGBA", "LA"):
                    # Palette/andere Modi mit Alpha auf RGBA konvertieren
                    im = im.convert("RGBA")
            else:
                # Ohne Alpha auf sRGB-ähnliches RGB konvertieren
                if im.mode not in ("RGB",):
                    im = im.convert("RGB")

            # Farbprofil/ICC, falls vorhanden, mitgeben
            icc_profile = im.info.get("icc_profile")

            # Als PNG speichern (verlustfrei, optimiert)
            im.save(
                dst_path,
                format="PNG",
                optimize=True,
                icc_profile=icc_profile
            )

        return True

    except Exception as e:
        print(f"[FEHLER] {src_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Alle Bilder in PNG umwandeln (rekursiv).")
    parser.add_argument("src", type=Path, help="Quellordner (z. B. /pfad/zu/EXPO)")
    parser.add_argument("--out", type=Path, default=None,
                        help="Zielordner (Standard: <src>_png parallel zum Quellordner)")
    parser.add_argument("--delete-originals", action="store_true",
                        help="Originaldateien nach erfolgreicher Konvertierung löschen (Vorsicht!)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="PNG überspringen, wenn die Zieldatei bereits existiert.")
    parser.add_argument("--copy-png", action="store_true",
                        help="Vorhandene PNGs (Quelle) unverändert ins Ziel kopieren (statt neu zu speichern).")
    args = parser.parse_args()

    src_root = args.src.resolve()
    if not src_root.is_dir():
        raise SystemExit(f"Quellordner existiert nicht: {src_root}")

    # Standard-Zielordner festlegen
    if args.out is None:
        dst_root = src_root.parent / f"{src_root.name}_png"
    else:
        dst_root = args.out.resolve()

    print(f"Quelle: {src_root}")
    print(f"Ziel:   {dst_root}")

    converted = 0
    copied = 0
    skipped = 0
    failed = 0

    for root, _, files in os.walk(src_root):
        root_path = Path(root)
        rel = root_path.relative_to(src_root)

        for fname in files:
            src_file = root_path / fname
            ext = src_file.suffix.lower()

            if ext not in SUPPORTED_EXTS:
                # Nicht unterstützte Datei
                continue

            # Zielpfad: gleiche Struktur, aber PNG-Endung
            dst_dir = dst_root / rel
            dst_file = dst_dir / (src_file.stem + ".png")

            # Bereits vorhandene Zieldatei?
            if args.skip_existing and dst_file.exists():
                skipped += 1
                continue

            # Wenn Quellbild bereits PNG ist:
            if ext == ".png":
                if args.copy_png:
                    dst_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                        if args.delete_originals:
                            try:
                                src_file.unlink(missing_ok=True)
                            except Exception as e:
                                print(f"[WARN] Original nicht gelöscht: {src_file} -> {e}")
                    except Exception as e:
                        print(f"[FEHLER] PNG-Kopie fehlgeschlagen: {src_file} -> {e}")
                        failed += 1
                else:
                    # PNG neu speichern (z. B. um zu normalisieren/optimieren)
                    ok = convert_image_to_png(src_file, dst_file)
                    if ok:
                        converted += 1
                        if args.delete_originals:
                            try:
                                src_file.unlink(missing_ok=True)
                            except Exception as e:
                                print(f"[WARN] Original nicht gelöscht: {src_file} -> {e}")
                    else:
                        failed += 1
                continue

            # Andere Formate -> nach PNG konvertieren
            ok = convert_image_to_png(src_file, dst_file)
            if ok:
                converted += 1
                if args.delete_originals:
                    try:
                        src_file.unlink(missing_ok=True)
                    except Exception as e:
                        print(f"[WARN] Original nicht gelöscht: {src_file} -> {e}")
            else:
                failed += 1

    print("\nZusammenfassung:")
    print(f"  Konvertiert: {converted}")
    print(f"  Kopiert (PNG): {copied}")
    print(f"  Übersprungen: {skipped}")
    print(f"  Fehlgeschlagen: {failed}")
    print(f"\nFertig. Dateien liegen unter: {dst_root}")

if __name__ == "__main__":
    # Verhindert DecompressionBomb-Warnungen bei extrem großen Bildern nicht, zeigt sie aber an.
    Image.MAX_IMAGE_PIXELS = None
    main()
