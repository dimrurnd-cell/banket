# -*- coding: utf-8 -*-
"""Сжатие фотографий сайта под веб.

Скачивает каждый оригинал, на который ссылается сайт, и раскладывает его в
лесенку ширин в трёх форматах: AVIF (самый лёгкий), WebP и JPEG (запасной для
старых браузеров). Результат — папка assets/img/opt/ и манифест
_src/images.json, из которого сборщик берёт srcset, sizes и размеры кадра.

    python3 _src/optimize_images.py                # скачать и сжать всё
    python3 _src/optimize_images.py --force        # пересжать заново
    python3 _src/optimize_images.py --no-avif      # если Pillow без AVIF
    python3 _src/optimize_images.py --src-dir DIR  # брать оригиналы из папки

Нужен Pillow:  pip install pillow

Оригиналы кэшируются в _src/.cache/originals/, поэтому повторный запуск
ничего не качает заново. Кэш в git не попадает.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "assets", "img", "opt")
OUT_URL = "/assets/img/opt/"
CACHE = os.path.join(HERE, ".cache", "originals")
MANIFEST = os.path.join(HERE, "images.json")

# Адрес, откуда качать файлы, которых нет в репозитории (галерея, newyear.jpg).
ASSET_BASE = os.environ.get(
    "ASSET_BASE", "https://donexpocentre.ru/static/banket/assets/").rstrip("/") + "/"

# Лесенка ширин. Браузер выберет по sizes нужную и не скачает остальные.
LADDER = [400, 640, 900, 1280, 1680, 2000]
# Логотипы в бегущей строке — высотой до 62 px, огромные версии им не нужны.
LADDER_SMALL = [200, 400]
# Оригиналы шире этого уменьшаем: 2000 px хватает на full-bleed на 2x-экране.
MAX_WIDTH = 2000

QUALITY = {"avif": 52, "webp": 76, "jpg": 80}

UA = {"User-Agent": "Mozilla/5.0 (compatible; banket-image-optimizer)"}


# --------------------------------------------------------------------------- сбор
def collect():
    """Все картинки, которые показывает сайт: (url, роль)."""
    sys.path.insert(0, HERE)
    import data as D

    seen, out = set(), []

    def add(url, role="photo"):
        if url and url not in seen:
            seen.add(url)
            out.append((url, role))

    for group in D.PHOTOS.values():
        for u in group:
            add(u)
    for u in D.COVERS.values():
        add(u)
    for u in D.GALLERY:
        add(u)
    for u in D.LOGOS:
        add(u, "logo")
    # Кадры, зашитые в вёрстку, а не в data.py.
    add("/assets/img/banquet-table.jpg")
    add("/assets/img/hero-banquet-1668.jpg")
    return out


# --------------------------------------------------------------------------- загрузка
def source_bytes(url):
    """Оригинал: из репозитория, из кэша или с хостинга."""
    if url.startswith("/assets/"):
        local = os.path.join(ROOT, url.lstrip("/"))
        if os.path.exists(local):
            with open(local, "rb") as fh:
                return fh.read()
        url = ASSET_BASE + url[len("/assets/"):]

    key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    cached = os.path.join(CACHE, key)
    if os.path.exists(cached):
        with open(cached, "rb") as fh:
            return fh.read()

    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as resp:
        blob = resp.read()
    os.makedirs(CACHE, exist_ok=True)
    with open(cached, "wb") as fh:
        fh.write(blob)
    return blob


# --------------------------------------------------------------------------- имена
TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "c",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e",
    "ю": "yu", "я": "ya",
}


def slugify(url):
    """Короткое латинское имя файла плюс хвост от адреса — против совпадений."""
    name = urllib.parse.unquote(url.split("/")[-1])
    name = os.path.splitext(name)[0].lower()
    name = "".join(TRANSLIT.get(ch, ch) for ch in name)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "img"
    tail = hashlib.sha1(url.encode("utf-8")).hexdigest()[:6]
    return "%s-%s" % (name[:40], tail)


# --------------------------------------------------------------------------- сжатие
def has_alpha(im):
    """Прозрачность есть только если альфа-канал реально не сплошной."""
    if im.mode not in ("RGBA", "LA", "P"):
        return False
    im = im.convert("RGBA")
    alpha = im.getchannel("A")
    return alpha.getextrema()[0] < 255


def encode(im, fmt, path, alpha):
    from PIL import Image  # noqa: F401  (нужен для регистрации плагинов)

    if fmt == "jpg":
        if alpha:
            bg = Image.new("RGB", im.size, (20, 40, 47))
            bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").getchannel("A"))
            im = bg
        im.convert("RGB").save(path, "JPEG", quality=QUALITY["jpg"],
                               optimize=True, progressive=True)
    elif fmt == "webp":
        im.save(path, "WEBP", quality=QUALITY["webp"], method=6)
    elif fmt == "avif":
        im.save(path, "AVIF", quality=QUALITY["avif"], speed=5)
    return os.path.getsize(path)


def process(url, role, formats, force):
    from PIL import Image, ImageOps

    blob = source_bytes(url)
    im = Image.open(io.BytesIO(blob))
    im = ImageOps.exif_transpose(im)          # развернуть по метаданным камеры
    alpha = has_alpha(im)
    im = im.convert("RGBA" if alpha else "RGB")

    ow, oh = im.size
    slug = slugify(url)
    ladder = LADDER_SMALL if role == "logo" else LADDER
    widths = sorted({w for w in ladder if w < ow} | {min(ow, MAX_WIDTH)})

    os.makedirs(OUT_DIR, exist_ok=True)
    entry = {"slug": slug, "w": ow, "h": oh, "alpha": alpha, "src": url, "files": {}}
    written = 0
    for fmt in formats:
        ext = "png" if (fmt == "jpg" and alpha) else fmt
        rows = []
        for w in widths:
            path = os.path.join(OUT_DIR, "%s-%d.%s" % (slug, w, ext))
            if force or not os.path.exists(path):
                resized = im if w == ow else im.resize(
                    (w, max(1, round(oh * w / ow))), Image.LANCZOS)
                if ext == "png":
                    resized.save(path, "PNG", optimize=True)
                    size = os.path.getsize(path)
                else:
                    size = encode(resized, fmt, path, alpha)
                written += 1
            else:
                size = os.path.getsize(path)
            rows.append([w, size])
        entry["files"][fmt] = {"ext": ext, "widths": rows}
    return entry, len(blob), written


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Сжать фотографии сайта под веб")
    ap.add_argument("--force", action="store_true", help="пересжать уже готовые файлы")
    ap.add_argument("--no-avif", action="store_true", help="не делать AVIF")
    ap.add_argument("--src-dir", help="папка с оригиналами вместо скачивания "
                                      "(имена файлов как в адресах)")
    args = ap.parse_args()

    try:
        from PIL import Image, features
    except ImportError:
        sys.exit("Нужен Pillow:  pip install pillow")

    formats = ["webp", "jpg"]
    if not args.no_avif:
        if features.check("avif"):
            formats.insert(0, "avif")
        else:
            print("! Pillow собран без AVIF — делаю только WebP и JPEG "
                  "(обновить:  pip install -U pillow)")
    if not features.check("webp"):
        sys.exit("Pillow собран без WebP — обновите его:  pip install -U pillow")

    if args.src_dir:
        global source_bytes
        original = source_bytes

        def from_dir(url):
            name = urllib.parse.unquote(url.split("/")[-1])
            path = os.path.join(args.src_dir, name)
            if os.path.exists(path):
                with open(path, "rb") as fh:
                    return fh.read()
            return original(url)
        source_bytes = from_dir

    items = collect()
    print("картинок к обработке: %d, форматы: %s" % (len(items), ", ".join(formats)))

    manifest = {"version": 1, "dir": OUT_URL, "formats": formats, "images": {}}
    before = after = 0
    failed = []
    for i, (url, role) in enumerate(items, 1):
        short = urllib.parse.unquote(url.split("/")[-1])
        try:
            entry, orig_size, written = process(url, role, formats, args.force)
        except Exception as exc:                       # noqa: BLE001
            failed.append((url, "%s: %s" % (type(exc).__name__, exc)))
            print("  [%2d/%d] ✗ %s — %s" % (i, len(items), short, exc))
            continue
        manifest["images"][url] = entry
        # «После» — вес того, что реально уедет к типичному гостю: самый
        # большой AVIF (или WebP), а не сумма всех вариантов.
        best = entry["files"][formats[0]]["widths"][-1][1]
        before += orig_size
        after += best
        print("  [%2d/%d] %s  %d×%d  %s → %s%s" % (
            i, len(items), short, entry["w"], entry["h"],
            human(orig_size), human(best), "" if written else "  (уже было)"))

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)

    print("\nготово: %d из %d" % (len(manifest["images"]), len(items)))
    if before:
        print("самый крупный кадр: %s → %s  (−%.0f%%)"
              % (human(before), human(after), 100 * (1 - after / before)))
    print("файлы: assets/img/opt/,  манифест: _src/images.json")
    if failed:
        print("\nне получилось скачать или открыть:")
        for url, why in failed:
            print("  %s\n    %s" % (url, why))
        sys.exit(1)


def human(n):
    for unit in ("Б", "КБ", "МБ"):
        if n < 1024 or unit == "МБ":
            return "%.0f %s" % (n, unit) if unit == "Б" else "%.1f %s" % (n, unit)
        n /= 1024.0


if __name__ == "__main__":
    main()
