# -*- coding: utf-8 -*-
"""Сборка версии для вставки в Tilda.

Выдаёт по одному HTML-фрагменту на страницу — его целиком вставляют в блок
«T123 · HTML-код». Шапка и подвал выносятся в служебные страницы «Хедер»
и «Футер». Стили и скрипт подключаются один раз в настройках сайта.

    ASSET_BASE=https://example.com/assets/ python3 _src/build_tilda.py

ASSET_BASE — адрес, по которому лежат папки css/, js/ и img/ из assets/.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build as B  # noqa: E402
from data import SITE  # noqa: E402
import pages as P  # noqa: E402

OUT = os.path.join(ROOT, "tilda")
# Куда залиты css/, js/ и img/ из assets/. Перебивается переменной окружения.
ASSET_BASE = os.environ.get(
    "ASSET_BASE", "https://donexpocentre.ru/static/banket/assets/").rstrip("/") + "/"
ASSET_ORIGIN = "/".join(ASSET_BASE.split("/")[:3])

FONTS = ("https://fonts.googleapis.com/css2?family=Jost:wght@200;300;400;500;600"
         "&family=JetBrains+Mono:wght@400;500&display=swap")


def absolutise(html):
    """Внутри Tilda относительные пути к ассетам не работают.

    Замена по кавычке пропускала вторых кандидатов в srcset — они отделены
    запятой, а не кавычкой. Ловим начало URL по любому разделителю; re.sub
    не пересматривает собственную подстановку, поэтому уже абсолютные
    адреса (в них тоже есть «/assets/») не портятся.
    """
    return re.sub(r'(?<=[\s"\'(,])/assets/', ASSET_BASE, html)


def slug_of(page):
    u = page["url"].strip("/")
    return u.replace("/", "-") or "glavnaya"


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build():
    if os.path.isdir(OUT):
        for root, _, files in os.walk(OUT, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            os.rmdir(root)

    # ---------- глобальный код ------------------------------------------
    write(os.path.join(OUT, "_global", "head-code.html"), absolutise(
        '<!-- Настройки сайта → Ещё → HTML-код для вставки внутрь HEAD -->\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="preconnect" href="%s" crossorigin>\n'
        '<link rel="preconnect" href="https://www.donexpocentre.ru">\n'
        '<link href="%s" rel="stylesheet">\n'
        '<meta name="theme-color" content="#0B181C">\n' % (ASSET_ORIGIN, FONTS)))

    write(os.path.join(OUT, "_global", "body-code.html"), absolutise(
        '<!-- Настройки сайта → Ещё → HTML-код перед закрывающим тегом </body> -->\n'
        '<!-- Стили подключаются здесь, а не в HEAD: css самой Tilda грузится\n'
        '     последним в head и иначе перебивает наш box-sizing. -->\n'
        '<link rel="stylesheet" href="/assets/css/site.css?v=3">\n'
        '<script src="/assets/js/site.js?v=3" defer></script>\n'))

    write(os.path.join(OUT, "_global", "header-block.html"), absolutise(
        '<!-- Страница «Хедер» → блок T123 «HTML-код» -->\n'
        '<div class="bn5-root">\n%s\n%s\n</div>\n'
        % (B.render_header(""), B.render_mobile_nav())))

    write(os.path.join(OUT, "_global", "footer-block.html"), absolutise(
        '<!-- Страница «Футер» → блок T123 «HTML-код».\n'
        '     Здесь же лежит форма заявки: она одинакова на всех страницах,\n'
        '     поэтому в блоки самих страниц её вставлять не нужно.\n'
        '     Кнопки «Проверить дату» ведут на якорь #zayavka внутри этого блока. -->\n'
        '<div class="bn5-root">\n%s\n</div>\n' % B.render_chrome()))

    # ---------- страницы -------------------------------------------------
    rows = []
    for p in P.PAGES:
        body = "\n".join(B.RENDER[s["t"]](s) for s in p["sections"])
        block = '<div class="bn5-root">\n%s\n</div>\n' % body
        block = re.sub(r"\n{3,}", "\n\n", absolutise(block))

        slug = slug_of(p)
        write(os.path.join(OUT, slug, "block.html"), block)

        url = p["url"] if p["url"] != "/" else "/"
        og = p.get("og") or B.COVERS["hero"]
        if og.startswith("/assets/"):
            og = absolutise('"' + og)[1:]
        elif og.startswith("/"):
            og = SITE["origin"] + og
        write(os.path.join(OUT, slug, "seo.txt"),
              "Настройки страницы в Tilda\n"
              "==========================\n\n"
              "Адрес страницы (URL):  %s\n"
              "Заголовок (Title):     %s\n"
              "Описание (Description):%s\n"
              "Картинка для соцсетей: %s\n" % (url, p["title"], " " + p["desc"], og))

        rows.append((url, p["title"], slug, len(p["sections"]), len(block)))

    # ---------- инструкция ----------------------------------------------
    table = "\n".join(
        "| `%s` | %s | %s | %.0f КБ |" % (u, s, sl, ln / 1024.0)
        for u, s, sl, _, ln in
        [(u, (t[:44] + "…") if len(t) > 45 else t, sl, n, ln) for u, t, sl, n, ln in rows])
    write(os.path.join(OUT, "README.md"), README % {
        "count": len(rows), "table": table, "asset_base": ASSET_BASE, "fonts": FONTS})

    leftovers = []
    for root, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            with open(path, encoding="utf-8") as fh:
                for m in re.finditer(r'(?<=[\s"\'(,])/assets/\S*', fh.read()):
                    leftovers.append("%s: %s" % (os.path.relpath(path, OUT), m.group(0)[:70]))
    if leftovers:
        raise SystemExit("остались относительные пути к ассетам:\n  " + "\n  ".join(leftovers))

    print("готово: %d страниц в tilda/, относительных путей к ассетам нет" % len(rows))
    print("ASSET_BASE = %s" % ASSET_BASE)


README = u"""# Перенос в Tilda

Сгенерировано `python3 _src/build_tilda.py`. Каждая страница — **один** блок
«HTML-код», а не набор блоков: вставлять %(count)d раз, а не 142.

## Что нужно сделать один раз

### 1. Выложить стили и скрипт

Tilda не хранит произвольные файлы, поэтому `assets/` нужно положить на любой
доступный по HTTPS адрес. Подходит любой из трёх вариантов:

- **Ваш сервер `donexpocentre.ru`** — там уже лежат все фотографии сайта.
  Самый простой путь: залить папку `assets/` рядом с ними.
- **Файловый менеджер Tilda** (если тариф позволяет) — загрузить `site.css`
  и `site.js`, Tilda выдаст ссылки на `static.tildacdn.com`.
- **jsDelivr** — если репозиторий публичный:
  `https://cdn.jsdelivr.net/gh/OWNER/REPO@main/assets/css/site.css`

Затем пересоберите с нужным адресом:

```
ASSET_BASE=https://ваш-адрес/assets/ python3 _src/build_tilda.py
```

Сейчас в файлах подставлено: `%(asset_base)s`
(этот адрес зашит в `_src/build_tilda.py` как значение по умолчанию —
переменную окружения задавать не обязательно).

### 2. Настройки сайта → Ещё

- **HTML-код внутрь HEAD** — содержимое `_global/head-code.html`
- **HTML-код перед `</body>`** — содержимое `_global/body-code.html`

Порядок важен. Стили подключаются перед `</body>`, а не в HEAD: собственный
css Tilda (`tilda-grid-3.0`) задаёт `box-sizing: content-box` для всех
элементов и в HEAD загрузится последним. В `site.css` есть защита от этого,
но подключение в конце body надёжнее.

### 3. Фон страниц

Настройки сайта → Шрифты и цвета → цвет фона: **#0B181C**. Иначе при загрузке
будет белая вспышка до применения стилей.

### 4. Шапка и подвал

Создайте служебные страницы «Хедер» и «Футер» (Tilda: «Создать страницу» →
тип «Хедер» / «Футер»), в каждой один блок **T123 «HTML-код»**:

- `_global/header-block.html`
- `_global/footer-block.html`

Никаких стандартных блоков меню Tilda добавлять не нужно — они продублируют
нашу навигацию.

## Что делать для каждой страницы

1. Создать страницу, задать адрес и SEO-поля из `<папка>/seo.txt`
2. Добавить один блок **T123 «HTML-код»**
3. Вставить содержимое `<папка>/block.html`
4. В настройках блока выставить **отступы сверху и снизу = 0**
   (иначе Tilda добавит инлайн-padding и разорвёт полноэкранные секции)

Форму заявки в страницы вставлять не нужно — она лежит в блоке футера
и появляется на всех страницах сама. Кнопки «Проверить дату» ведут
на якорь `#zayavka` внутри этого блока.

| Адрес | Страница | Папка | Размер блока |
|-------|----------|-------|--------------|
%(table)s

## Что перестанет работать в Tilda

- **Редактирование текста через интерфейс Tilda.** Внутри блока «HTML-код»
  визуального редактора нет. Правки текстов делаются в `_src/pages.py`,
  затем пересборка и повторная вставка блока.
- **Форма заявки** продолжит работать: она отправляется на тот же адрес
  `forms.tildacdn.com/procces/` и внутри Tilda подхватит настоящие
  `data-tilda-project-id` и `data-tilda-page-id` из `#allrecords`.
  Ключ формы задан в `_src/data.py` → `SITE["formskey"]`.
- **Баннер cookie** в новой вёрстке не реализован. В Tilda его можно вернуть
  штатным блоком T972 — он не конфликтует с нашими стилями.

## Проверено

Вёрстка прогонялась в симуляции окружения Tilda: их `tilda-grid-3.0.min.css`
подключался перед нашим, блок оборачивался в `.t-rec` с инлайновым
`padding: 60px`, как это делает редактор. Вычисленные стили совпали со
статической версией по всем ключевым параметрам — `box-sizing`, фон и шрифт
body, ширина контейнера, сетки блоков, границы карточек.

## Обновление после правок

```
python3 _src/build.py                                    # статическая версия
ASSET_BASE=https://ваш-адрес/assets/ python3 _src/build_tilda.py
```

Затем заново залить `assets/` и вставить изменившиеся `block.html`.
"""


if __name__ == "__main__":
    build()
