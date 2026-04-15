import os
from pathlib import Path
from PIL import Image, ImageOps
import shutil

# --- Einstellungen ---
SRC_DIR = Path("IMAGE")
OUT_AVIF = SRC_DIR / "mobile" / "avif"
OUT_WEBP = SRC_DIR / "mobile" / "webp"
SIZES = [480, 960, 1200]  # Zielbreiten für Mobile
JPEG_BG = (255, 255, 255)  # Hintergrund für PNG mit Alpha (weiß)

# Qualität/Kompression
AVIF_QUALITY = 45   # 30-50 ist oft sweet spot
AVIF_SPEED = 6      # 0 = langsam/besser, 10 = schnell
WEBP_QUALITY = 75   # visuell i.d.R. gut

# --- Helper ---
def ensure_dirs():
    OUT_AVIF.mkdir(parents=True, exist_ok=True)
    OUT_WEBP.mkdir(parents=True, exist_ok=True)

def iter_source_images():
    # Alle Bilder in IMAGE/, aber mobile/ und thumbs/ auslassen
    for root, dirs, files in os.walk(SRC_DIR):
        # Verzeichnisse überspringen, die nicht als Quelle dienen sollen
        if "mobile" in root.split(os.sep): 
            continue
        if "thumbs" in root.split(os.sep):
            continue

        for f in files:
            fn = Path(root) / f
            ext = fn.suffix.lower()
            if ext in (".png", ".jpg", ".jpeg"):
                yield fn

def load_flat_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)  # korrekte Orientierung
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, JPEG_BG)
        bg.paste(im, mask=im.split()[-1])
        return bg
    elif im.mode != "RGB":
        return im.convert("RGB")
    return im

def resize_to_width(img: Image.Image, target_w: int) -> Image.Image:
    w, h = img.size
    if w <= target_w:
        return img.copy()
    target_h = int(h * (target_w / w))
    return img.resize((target_w, target_h), Image.LANCZOS)

def base_name(path: Path) -> str:
    # z.B. IMAGE/COMPRESSED/DISCO.JPG -> DISCO
    return path.stem

def save_avif(img: Image.Image, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="AVIF", quality=AVIF_QUALITY, effort=AVIF_SPEED)

def save_webp(img: Image.Image, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="WEBP", quality=WEBP_QUALITY, method=6)

def already_done(name: str) -> bool:
    # Wenn alle Zielgrößen als AVIF existieren, betrachten wir es als fertig
    return all((OUT_AVIF / f"{name}-{w}.avif").exists() for w in SIZES)

def main():
    ensure_dirs()
    count = 0
    for src in iter_source_images():
        name = base_name(src)

        # Wenn die Datei nur Varianten eines bestehenden Namens ist (SMALL/COMPRESSED),
        # trotzdem nur EIN Mal pro Name erzeugen.
        if already_done(name):
            continue

        try:
            img = load_flat_rgb(src)

            for w in SIZES:
                resized = resize_to_width(img, w)
                avif_path = OUT_AVIF / f"{name}-{w}.avif"
                webp_path = OUT_WEBP / f"{name}-{w}.webp"

                save_avif(resized, avif_path)
                save_webp(resized, webp_path)

            count += 1
            print(f"OK: {name} -> AVIF/WebP @ {SIZES}")
        except Exception as e:
            print(f"FEHLER bei {src}: {e}")

    print(f"Fertig. Neu erzeugte Basismotive: {count}")

if __name__ == "__main__":
    main()
