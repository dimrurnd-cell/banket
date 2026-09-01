# -*- coding: utf-8 -*-
"""Адаптивные картинки: <picture> с srcset по манифесту _src/images.json.

Манифест создаёт `python3 _src/optimize_images.py`. Пока его нет, всё
работает по-старому — одна большая картинка в <img>. Так сборка не ломается
до того, как фотографии сожмут, и чинится сама, как только манифест появится.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(HERE, "images.json")


def _load():
    if not os.path.exists(MANIFEST_PATH):
        return {"images": {}, "dir": "/assets/img/opt/", "formats": []}
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


M = _load()
IMAGES = M.get("images", {})
DIR = M.get("dir", "/assets/img/opt/")
# Порядок важен: первым идёт самый лёгкий формат, браузер берёт первый,
# который понимает.
FORMATS = [f for f in ("avif", "webp") if f in M.get("formats", [])]
MIME = {"avif": "image/avif", "webp": "image/webp"}

# Ширина слота на разных экранах. Без этого браузер считает картинку во всю
# ширину окна и качает версию вчетверо тяжелее нужной.
# Сетка: --wrap 1340px, --gutter до 48px, значит колонка из трёх — около 400px.
SLOTS = {
    "hero": "100vw",
    "band": "100vw",
    "split": "(max-width:860px) calc(100vw - 40px), 620px",
    "card": "(max-width:640px) calc(100vw - 40px), (max-width:1000px) 46vw, 400px",
    "gallery": "(max-width:560px) calc(100vw - 40px), (max-width:900px) 46vw, 400px",
    "logo": "160px",
}


def known(src):
    return src in IMAGES


def _srcset(entry, fmt):
    ext = entry["files"][fmt]["ext"]
    return ", ".join("%s%s-%d.%s %dw" % (DIR, entry["slug"], w, ext, w)
                     for w, _size in entry["files"][fmt]["widths"])


def _at(entry, fmt, target):
    """Один файл ближайшей сверху ширины — для og:image и лайтбокса."""
    ext = entry["files"][fmt]["ext"]
    widths = [w for w, _ in entry["files"][fmt]["widths"]]
    pick = next((w for w in widths if w >= target), widths[-1])
    return "%s%s-%d.%s" % (DIR, entry["slug"], pick, ext)


def at(src, fmt, target):
    """Ссылка на конкретный вариант или None, если картинки нет в манифесте."""
    entry = IMAGES.get(src)
    if not entry or fmt not in entry["files"]:
        return None
    return _at(entry, fmt, target)


def og(src, target=1200):
    """Картинка для соцсетей: только jpg/png — Telegram и VK не жуют avif."""
    return at(src, "jpg", target) or src


def markup(src, alt, cls="", lazy=True, slot="card", priority=False, esc=str):
    """<picture> с лесенкой ширин; без манифеста — обычный <img>, как раньше."""
    entry = IMAGES.get(src)
    attrs = ""
    if cls:
        attrs += ' class="%s"' % cls
    attrs += ' loading="lazy"' if lazy else ""
    attrs += ' fetchpriority="high"' if priority else ""

    if not entry:
        return '<img src="%s" alt="%s"%s decoding="async">' % (
            esc(src), esc(alt), attrs)

    sizes = SLOTS.get(slot, SLOTS["card"])
    sources = "".join(
        '<source type="%s" srcset="%s" sizes="%s">' % (MIME[f], _srcset(entry, f), sizes)
        for f in FORMATS if f in entry["files"])
    img = ('<img src="%s" srcset="%s" sizes="%s" width="%d" height="%d" '
           'alt="%s"%s decoding="async">') % (
        _at(entry, "jpg", 1280), _srcset(entry, "jpg"), sizes,
        entry["w"], entry["h"], esc(alt), attrs)
    return "<picture>%s%s</picture>" % (sources, img)


def preload(src):
    """<link rel=preload> для кадра первого экрана — грузится раньше CSS."""
    entry = IMAGES.get(src)
    if not entry:
        return ""
    fmt = FORMATS[0] if FORMATS else "jpg"
    return ('<link rel="preload" as="image" type="%s" imagesrcset="%s" '
            'imagesizes="100vw" fetchpriority="high">' % (
                MIME.get(fmt, "image/jpeg"), _srcset(entry, fmt)))
