# -*- coding: utf-8 -*-
"""Static site builder for banket-na5.ru.

Renders every page from _src/pages.py into the repository root, keeping the
page*.html filenames the existing .htaccess rewrites and sitemap point at.

    python3 _src/build.py
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from data import (SITE, NAV, LEGAL, HALLS, FORMATS, FORM_OPTIONS, LOGOS,
                  INCLUDED, TIMING, PROCESS, PRICE_PARTS, COVERS)  # noqa: E402

E = html.escape
ARROW = '<span class="btn__arrow" aria-hidden="true">→</span>'
CHEV = ('<svg width="13" height="10" viewBox="0 0 13 10" fill="none" aria-hidden="true">'
        '<path d="M1 5h10M8 1.5 11.5 5 8 8.5" stroke="currentColor" stroke-width="1.4" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')


# --------------------------------------------------------------------------- helpers
def attrs(d):
    return "".join(' %s="%s"' % (k, E(str(v), quote=True)) for k, v in (d or {}).items())


def button(label, href, kind="", extra=None):
    cls = "btn" + (" " + kind if kind else "")
    return '<a class="%s" href="%s"%s>%s%s</a>' % (cls, E(href), attrs(extra), E(label), ARROW)


def buttons(items):
    if not items:
        return ""
    return '<div class="btn-row mt-m">%s</div>' % "".join(
        button(i[0], i[1], i[2] if len(i) > 2 else "", i[3] if len(i) > 3 else None) for i in items)


def eyebrow(text):
    return '<p class="eyebrow">%s</p>' % E(text) if text else ""


def head_block(s, tone=""):
    """eyebrow + title + lede"""
    out = ['<div class="section__head reveal">']
    out.append(eyebrow(s.get("eyebrow", "")))
    if s.get("title"):
        out.append('<h2 class="h-lg">%s</h2>' % s["title"])
    if s.get("lede"):
        out.append('<p class="lede mt-s">%s</p>' % s["lede"])
    out.append("</div>")
    return "".join(out)


def section(inner, s):
    tone = s.get("tone", "")
    cls = "section"
    if tone:
        cls += " section--" + tone
    if s.get("tight"):
        cls += " section--tight"
    sid = ' id="%s"' % s["id"] if s.get("id") else ""
    return '<section class="%s"%s><div class="wrap">%s</div></section>' % (cls, sid, inner)


def picture(src, alt, cls="", lazy=True, sizes=None):
    return '<img src="%s" alt="%s"%s%s decoding="async"%s>' % (
        E(src), E(alt, quote=True), ' class="%s"' % cls if cls else "",
        ' loading="lazy"' if lazy else "", ' sizes="%s"' % sizes if sizes else "")


# --------------------------------------------------------------------------- sections
def s_hero(s):
    marks = "".join(
        '<div class="scale-mark" style="left:%s%%"><b>%s</b><span>%s</span></div>' % (pct, E(num), E(lbl))
        for pct, num, lbl in s.get("scale", []))
    lines = "".join('<span class="rise"><span>%s</span></span>' % l for l in s["lines"])
    media = picture(s["image"], s.get("alt", ""), lazy=False)
    if s["image"].startswith("/assets/img/hero-banquet"):
        media = ('<img src="/assets/img/hero-banquet-1668.jpg" '
                 'srcset="/assets/img/hero-banquet-504.jpg 504w, /assets/img/hero-banquet-1668.jpg 1668w" '
                 'sizes="100vw" alt="%s" fetchpriority="high" decoding="async">' % E(s.get("alt", ""), quote=True))
    return """<section class="hero">
  <div class="hero__media">%s</div>
  <div class="hero__scrim" aria-hidden="true"></div>
  <div class="wrap hero__body">
    %s
    <h1 class="h-xl hero__title">%s</h1>
    <p class="lede hero__lede">%s</p>
    %s
    %s
  </div>
  <div class="wrap hero__scale">
    <div class="ruler" aria-hidden="true"></div>
    <div class="scale-marks" aria-hidden="true">%s</div>
  </div>
</section>""" % (
        media,
        eyebrow(s.get("eyebrow", "")),
        lines,
        s["lede"],
        buttons(s.get("actions")),
        '<p class="hero__note">%s</p>' % E(s["note"]) if s.get("note") else "",
        marks)


def s_hero_page(s):
    if s.get("plain"):
        return """<section class="hero hero--page hero--plain">
  <div class="wrap hero__body">
    %s
    <h1 class="h-xl hero__title">%s</h1>
    <p class="lede hero__lede">%s</p>
    %s
  </div>
  <div class="wrap hero__scale"><div class="ruler" aria-hidden="true"></div></div>
</section>""" % (eyebrow(s.get("eyebrow", "")), s["title"], s.get("lede", ""), buttons(s.get("actions")))
    return """<section class="hero hero--page">
  <div class="hero__media">%s</div>
  <div class="hero__scrim" aria-hidden="true"></div>
  <div class="wrap hero__body">
    %s
    <h1 class="h-xl hero__title">%s</h1>
    <p class="lede hero__lede">%s</p>
    %s
  </div>
  <div class="wrap hero__scale"><div class="ruler" aria-hidden="true"></div></div>
</section>""" % (
        picture(s["image"], s.get("alt", ""), lazy=False),
        eyebrow(s.get("eyebrow", "")),
        s["title"], s.get("lede", ""), buttons(s.get("actions")))


def s_stats(s):
    items = "".join(
        '<div class="stats__item reveal" data-delay="%d"><div class="stats__num"><span data-count="%s">0</span>%s</div>'
        '<p class="stats__label">%s</p></div>' % (i, n, sup, E(lbl))
        for i, (n, sup, lbl) in enumerate(s["items"]))
    return section('<div class="stats">%s</div>' % items, s)


def s_picker(s):
    import json
    payload = json.dumps([{k: h[k] for k in ("name", "note", "meta", "url", "to")} for h in HALLS], ensure_ascii=False)
    panels = "".join(
        '<div class="picker__panel%s" data-hall-panel>%s</div>' % (
            " is-active" if i == 0 else "", picture(COVERS[h["slug"]], "Зал: " + h["name"]))
        for i, h in enumerate(HALLS))
    # no-JS fallback: the halls stay reachable as plain links
    fallback = "".join('<li><a class="tlink" href="%s">%s — %s%s</a></li>' % (h["url"], E(h["name"]), E(h["cap"]), CHEV)
                       for h in HALLS)
    inner = """%s
<div class="picker reveal" data-picker='%s'>
  <div class="picker__stage">%s<span class="picker__badge">Зал подбирается по числу гостей</span></div>
  <div>
    <div class="picker__read"><div class="picker__count" data-picker-count>120</div>
      <div class="picker__count-label">гостей</div></div>
    <div class="picker__slider">
      <label class="visually-hidden" for="guest-range">Количество гостей</label>
      <input id="guest-range" type="range" min="0" max="100" value="45" step="1" data-picker-range>
      <div class="picker__ticks"><span>20</span><span>150</span><span>500</span><span>2 500</span></div>
    </div>
    <div class="picker__hall" data-picker-info>
      <noscript><ul class="picker__meta-list">%s</ul></noscript>
    </div>
    <p class="picker__hint">%s</p>
  </div>
</div>""" % (head_block(s), payload.replace("'", "&#39;"), panels, fallback, E(s.get("hint", "")))
    return section(inner, s)


def s_facts(s):
    rows = "".join(
        '<div class="fact reveal"><div class="fact__fig">%s<small>%s</small></div>'
        '<div class="fact__body"><h3>%s</h3><p>%s</p></div></div>' % (E(fig), E(small), E(h3), p)
        for fig, small, h3, p in s["items"])
    inner = """<div class="facts">
  <div class="facts__aside">%s</div>
  <div class="facts__list">%s</div>
</div>""" % (head_block(s), rows)
    return section(inner, s)


def s_cards(s):
    cards = []
    for i, c in enumerate(s["items"]):
        cap = '<span class="card__cap data">%s</span>' % E(c["cap"]) if c.get("cap") else ""
        if c.get("image"):
            media = '<div class="card__media">%s%s</div>' % (
                picture(c["image"], c.get("alt", c["name"])), cap)
        else:
            # a format we deliberately do not illustrate keeps the grid rhythm
            media = '<div class="card__media card__media--blank">%s</div>' % cap
        cards.append(
            '<article class="card reveal" data-delay="%d">%s<div class="card__body"><h3>%s</h3><p>%s</p>'
            '<span class="tlink card__link">%s%s</span></div>'
            '<a class="card__stretch" href="%s"><span class="visually-hidden">%s</span></a></article>' % (
                i % 3, media, E(c["name"]), c["short"], E(c.get("cta", "Подробнее")), CHEV,
                E(c["url"]), E(c["name"])))
    inner = "%s<div class=\"grid grid--%d\">%s</div>" % (head_block(s), s.get("cols", 3), "".join(cards))
    return section(inner, s)


def s_steps(s):
    src = s.get("items") or PROCESS
    items = "".join(
        '<div class="steps__item reveal" data-delay="%d"><span class="steps__n">Шаг %02d</span>'
        '<h3>%s</h3><p>%s</p><span class="steps__time">%s</span></div>' % (i, i + 1, E(t), E(p), E(time))
        for i, (t, p, time) in enumerate(src))
    return section("%s<div class=\"steps\">%s</div>" % (head_block(s), items), s)


def s_split(s):
    media_cls = "split__media split__media--arch" if s.get("arch") else "split__media"
    body = "".join('<p class="lede mt-s">%s</p>' % p for p in s["body"])
    text = """<div class="reveal">%s<h2 class="h-lg">%s</h2>%s%s%s</div>""" % (
        eyebrow(s.get("eyebrow", "")), s["title"], body,
        '<p class="hero__note mt-m">%s</p>' % E(s["note"]) if s.get("note") else "",
        buttons(s.get("actions")))
    media = '<div class="%s reveal" data-delay="1">%s</div>' % (media_cls, picture(s["image"], s.get("alt", "")))
    order = [media, text] if s.get("reverse") else [text, media]
    return section('<div class="split">%s</div>' % "".join(order), s)


def s_rows(s):
    items = "".join('<li class="reveal"><h3>%s</h3><p>%s</p></li>' % (E(t), p) for t, p in s["items"])
    return section("%s<ul class=\"list-rows\">%s</ul>" % (head_block(s), items), s)


def s_tiles(s):
    items = "".join('<div class="tile reveal" data-delay="%d"><span class="tile__k">%s</span><h3>%s</h3><p>%s</p></div>'
                    % (i % 4, E(k), E(t), p) for i, (k, t, p) in enumerate(s["items"]))
    return section("%s<div class=\"tiles\">%s</div>" % (head_block(s), items), s)


def s_price(s):
    cells = "".join('<div class="price__cell reveal" data-delay="%d"><b>%s</b><h3>%s</h3><p>%s</p></div>'
                    % (i, E(k), E(t), E(p)) for i, (k, t, p) in enumerate(PRICE_PARTS))
    after = ""
    if s.get("after"):
        after = '<div class="mt-l reveal"><p class="lede">%s</p>%s</div>' % (s["after"], buttons(s.get("actions")))
    return section("%s<div class=\"price\">%s</div>%s" % (head_block(s), cells, after), s)


def s_gallery(s):
    chips = ""
    if s.get("filters"):
        chips = '<div class="filters reveal" data-filters>%s</div>' % "".join(
            '<button type="button" data-tag="%s" aria-pressed="%s">%s</button>' % (E(tag), "true" if i == 0 else "false", E(label))
            for i, (tag, label) in enumerate(s["filters"]))
    shots = "".join(
        '<button type="button" class="shot" data-tags="%s" data-full="%s">%s</button>' % (
            E(tags), E(src), picture(src, alt))
        for src, alt, tags in s["shots"])
    return section("%s%s<div class=\"masonry\">%s</div>%s" % (
        head_block(s), chips, shots, buttons(s.get("actions"))), s)


def s_marquee(s):
    row = "".join('<img src="%s" alt="" loading="lazy" decoding="async">' % E(u) for u in LOGOS)
    return section("%s<div class=\"marquee\"><div class=\"marquee__track\">%s%s</div></div>" % (
        head_block(s), row, row), s)


def s_faq(s):
    items = "".join('<details%s><summary>%s</summary><div class="faq__a">%s</div></details>'
                    % (" open" if i == 0 else "", E(q), a) for i, (q, a) in enumerate(s["items"]))
    return section("%s<div class=\"faq\">%s</div>" % (head_block(s), items), s)


def s_band(s):
    return """<section class="section band">
  <div class="band__media">%s</div>
  <div class="wrap"><div class="band__inner reveal">%s<h2 class="h-lg">%s</h2><p class="lede mt-s">%s</p>%s</div></div>
</section>""" % (picture(s["image"], ""), eyebrow(s.get("eyebrow", "")), s["title"], s["lede"], buttons(s.get("actions")))


def s_contacts(s):
    cards = "".join(
        '<div class="contact-card reveal" data-delay="%d"><b>%s</b><div class="val">%s</div><p>%s</p></div>'
        % (i % 3, E(k), v, E(p)) for i, (k, v, p) in enumerate(s["items"]))
    return section("%s<div class=\"grid grid--3\">%s</div>" % (head_block(s), cards), s)


def s_map(s):
    return section("%s<div class=\"map reveal\"><iframe src=\"%s\" title=\"Карта: как доехать до Банкет-Холла\" "
                   "loading=\"lazy\" allowfullscreen></iframe></div>" % (head_block(s), E(SITE["map"])), s)


def s_doc(s):
    body = s["html"]
    body = re.sub(r'(?<!__wrapper">)(<table)', r'<div class="doc__table">\1', body)
    body = body.replace("</table>", "</table></div>")
    body = body.replace('<div class="quill-table__wrapper"><div class="doc__table">',
                        '<div class="quill-table__wrapper">')
    body = body.replace("</table></div></div>", "</table></div>")
    toc = ""
    if s.get("toc"):
        toc = '<div class="doc__toc"><b>Другие документы:</b><br>%s</div>' % " · ".join(
            '<a href="%s">%s</a>' % (E(d["url"]), E(d["title"])) for d in LEGAL if d["url"] != s.get("self"))
    return section('<div class="doc">%s%s</div>' % (toc, body), s)


def s_html(s):
    return section(s["html"], s)


RENDER = {
    "hero": s_hero, "hero_page": s_hero_page, "stats": s_stats, "picker": s_picker,
    "facts": s_facts, "cards": s_cards, "steps": s_steps, "split": s_split, "rows": s_rows,
    "tiles": s_tiles, "price": s_price, "gallery": s_gallery, "marquee": s_marquee,
    "faq": s_faq, "band": s_band, "contacts": s_contacts, "map": s_map, "doc": s_doc, "html": s_html,
}


# --------------------------------------------------------------------------- chrome
LOGO_MARK = ('<svg class="logo-mark" width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">'
             '<path d="M22.5 4.2A13 13 0 1 0 26 12.2" stroke="#D9A441" stroke-width="1.5" stroke-linecap="round"/>'
             '<path d="M24.8 3A13 13 0 1 0 28 13.8" stroke="#F3EAD8" stroke-width="1" stroke-linecap="round" '
             'opacity=".45"/></svg>')


def render_header(active):
    links = []
    for n in NAV:
        cur = ' aria-current="page"' if n["key"] == active else ""
        if n.get("sub"):
            sub = "".join('<a href="%s">%s<i>%s</i></a>' % (E(x["url"]), E(x["title"]), E(x.get("meta", "")))
                          for x in n["sub"])
            links.append('<div class="has-sub"><a class="header__link" href="%s"%s>%s</a><div class="sub">%s</div></div>'
                         % (E(n["url"]), cur, E(n["title"]), sub))
        else:
            links.append('<a class="header__link" href="%s"%s>%s</a>' % (E(n["url"]), cur, E(n["title"])))
    return """<header class="header">
  <div class="wrap header__inner">
    <a class="header__logo" href="/" aria-label="Банкет-Холл — на главную">
      <b>Банкет-Холл</b><span>ВЦ «ДонЭкспоцентр»</span>
    </a>
    <nav class="header__nav" aria-label="Основная навигация">%s</nav>
    <a class="header__tel data" href="%s">%s</a>
    <a class="btn header__cta" href="#zayavka">Проверить дату</a>
    <button class="burger" type="button" aria-expanded="false" aria-controls="mnav" aria-label="Меню">
      <span></span><span></span>
    </button>
  </div>
</header>""" % ("".join(links), SITE["phone_href"], E(SITE["phone"]))


def render_mobile_nav():
    groups = []
    for n in NAV:
        if n.get("sub"):
            sub = "".join('<a href="%s">%s<i>%s</i></a>' % (E(x["url"]), E(x["title"]), E(x.get("meta", "")))
                          for x in n["sub"])
            groups.append('<div class="mnav__group"><a class="mnav__title" href="%s">%s</a>'
                          '<div class="mnav__sub">%s</div></div>' % (E(n["url"]), E(n["title"]), sub))
        else:
            groups.append('<div class="mnav__group"><a href="%s">%s</a></div>' % (E(n["url"]), E(n["title"])))
    return """<div class="mnav" id="mnav">
  <div class="mnav__group"><a href="/">Главная</a></div>
  %s
  <div class="mnav__foot">
    <a class="data" href="%s">%s</a>
    <a class="data" href="mailto:%s">%s</a>
    <a class="btn" href="#zayavka">Проверить дату%s</a>
  </div>
</div>""" % ("".join(groups), SITE["phone_href"], E(SITE["phone"]), E(SITE["email"]), E(SITE["email"]), ARROW)


def render_form():
    options = "".join('<option value="%s">%s</option>' % (E(o), E(o)) for o in FORM_OPTIONS)
    return """<section class="section section--ink2" id="zayavka">
  <div class="wrap">
    <div class="split split--wide-left">
      <div class="reveal">
        <p class="eyebrow">Заявка</p>
        <h2 class="h-lg">Первое, что скажем, — свободна ли ваша дата</h2>
        <p class="lede mt-s">Достаточно формата, даты и примерного числа гостей — остальное уточним сами.
          В рабочее время отвечаем за 15 минут: сначала про дату, потом про зал и смету.</p>
        <div class="contact-methods mt-m">
          <a class="data" href="%(phone_href)s">%(phone)s</a>
          <a class="data" href="mailto:%(email)s">%(email)s</a>
        </div>
        <p class="hero__note mt-m">%(hours)s · %(address)s</p>
      </div>
      <div class="formwrap reveal" data-delay="1">
        <form id="request-form" data-formskey="%(formskey)s">
          <input type="hidden" name="formservices[]" value="%(formservice)s">
          <div class="form-grid">
            <div class="field field--full">
              <label for="f-name">Как к вам обращаться</label>
              <input id="f-name" name="Name" type="text" required placeholder="Имя">
            </div>
            <div class="field">
              <label for="f-mtype">Как удобнее связаться</label>
              <select id="f-mtype" name="messenger-type">
                <option value="phone">Позвонить</option>
                <option value="telegram">Telegram</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="max_messenger">Max</option>
              </select>
            </div>
            <div class="field">
              <label for="f-contact">Телефон или ник</label>
              <input id="f-contact" name="messenger-id" type="text" required placeholder="+7 (___) ___-__-__">
            </div>
            <div class="field">
              <label for="f-format">Формат мероприятия</label>
              <select id="f-format" name="мероприятие">%(options)s</select>
            </div>
            <div class="field">
              <label for="f-date">Дата</label>
              <input id="f-date" name="Выберите дату мероприятия" type="date">
            </div>
            <div class="field">
              <label for="f-guests">Сколько гостей примерно</label>
              <input id="f-guests" name="Выберите количество гостей" type="number" min="1" inputmode="numeric" placeholder="120">
            </div>
            <div class="field">
              <label for="f-email">E-mail, если нужен расчёт письмом</label>
              <input id="f-email" name="Email" type="email" placeholder="you@example.com">
            </div>
            <div class="field field--full">
              <label for="f-note">Что важно знать заранее</label>
              <textarea id="f-note" name="Комментарий" placeholder="Например: свой ведущий, выездная регистрация, детское меню на 10 человек"></textarea>
            </div>
            <div class="field field--full">
              <label class="consent">
                <input type="checkbox" name="soglasiye-persdan" value="yes" required>
                <span>Согласен на обработку персональных данных в соответствии с
                  <a href="/policy">политикой конфиденциальности</a>.</span>
              </label>
            </div>
          </div>
          <div class="mt-m"><button class="btn btn--lg btn--block" type="submit">Проверить дату и получить расчёт</button></div>
          <p class="form-status" role="status" aria-live="polite"></p>
        </form>
      </div>
    </div>
  </div>
</section>""" % dict(SITE, options=options)


def render_footer():
    halls = "".join('<li><a href="%s">%s</a></li>' % (E(h["url"]), E(h["name"])) for h in HALLS)
    formats = "".join('<li><a href="%s">%s</a></li>' % (E(f["url"]), E(f["name"])) for f in FORMATS)
    legal = "".join('<a href="%s">%s</a>' % (E(d["url"]), E(d["title"])) for d in LEGAL[:3])
    return """<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <a class="header__logo" href="/"><b>Банкет-Холл</b><span>ВЦ «ДонЭкспоцентр»</span></a>
        <p class="footer__about">Три банкетных зала от 50 до 2 500 гостей, кухня в здании и собственный
          инвентарь — на территории выставочного центра в Ростове-на-Дону.</p>
      </div>
      <div><h4>Залы</h4><ul class="footer__list">%s</ul></div>
      <div><h4>Мероприятия</h4><ul class="footer__list">%s</ul></div>
      <div><h4>Контакты</h4>
        <div class="footer__contacts">
          <a class="data" href="%s">%s</a>
          <a href="mailto:%s">%s</a>
          <span>%s</span>
          <span>%s</span>
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© 2026 %s. Работает на территории ВЦ «ДонЭкспоцентр».</span>
      <span class="footer__legal">%s</span>
    </div>
  </div>
</footer>""" % (halls, formats, SITE["phone_href"], E(SITE["phone"]), E(SITE["email"]), E(SITE["email"]),
                E(SITE["address_full"]), E(SITE["hours"]), E(SITE["legal_name"]), legal)


LIGHTBOX = """<div class="lightbox" role="dialog" aria-modal="true" aria-label="Просмотр фотографии">
  <button class="lightbox__close" type="button" aria-label="Закрыть">✕</button>
  <button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Предыдущее фото">‹</button>
  <img alt="" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
  <button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Следующее фото">›</button>
</div>"""


def render_chrome(include_form=True):
    """Подвал и лайтбокс — одинаковы на всех страницах.

    include_form=False — форму даёт что-то внешнее: в Tilda это штатный
    блок формы, он сам прописывает получателей заявок. Кнопки по сайту
    ведут на якорь #zayavka, поэтому этот якорь должен быть у внешнего
    блока (в Tilda: настройки блока → ID блока для ссылки → zayavka).
    """
    parts = [render_form()] if include_form else []
    return "\n".join(parts + [render_footer(), LIGHTBOX])


LD = """{
  "@context":"https://schema.org",
  "@type":"EventVenue",
  "name":"Банкет-Холл — ВЦ «ДонЭкспоцентр»",
  "url":"https://banket-na5.ru",
  "telephone":"+78632563530",
  "email":"banket@donexpocentre.ru",
  "maximumAttendeeCapacity":2500,
  "address":{"@type":"PostalAddress","addressLocality":"Ростов-на-Дону",
    "streetAddress":"проспект Михаила Нагибина, 30","addressCountry":"RU"},
  "openingHours":"Mo-Sa 09:00-18:00",
  "image":"%s"
}""" % (SITE["origin"] + COVERS["hero"])


PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(canonical)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Банкет-Холл">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:image" content="%(og)s">
<meta property="og:locale" content="ru_RU">
<meta name="theme-color" content="#0B181C">
<link rel="icon" href="/assets/img/favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://www.donexpocentre.ru">
%(preload)s
<link href="https://fonts.googleapis.com/css2?family=Jost:wght@200;300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v=2">
<script type="application/ld+json">%(ld)s</script>
</head>
<body>
<a class="skip" href="#main">Перейти к содержанию</a>
<div id="allrecords" data-tilda-project-id="%(project)s" data-tilda-page-id="%(pageid)s"></div>
%(header)s
%(mnav)s
<main id="main">
%(body)s
</main>
%(chrome)s
<script src="/assets/js/site.js?v=2" defer></script>
</body>
</html>
"""


def build():
    import pages as P
    n = 0
    for p in P.PAGES:
        body = "\n".join(RENDER[s["t"]](s) for s in p["sections"])
        html_out = PAGE % {
            "title": E(p["title"], quote=True),
            "desc": E(p["desc"], quote=True),
            "canonical": SITE["origin"] + (p["url"] if p["url"] != "/" else ""),
            "og": (SITE["origin"] + p["og"]) if p.get("og", "").startswith("/") else p.get("og") or (SITE["origin"] + COVERS["hero"]),
            "ld": LD,
            "project": SITE["project_id"],
            "pageid": p["file"].replace("page", "").replace(".html", ""),
            "preload": ('<link rel="preload" as="image" href="/assets/img/hero-banquet-1668.jpg" '
                        'imagesrcset="/assets/img/hero-banquet-504.jpg 504w, /assets/img/hero-banquet-1668.jpg 1668w" '
                        'imagesizes="100vw" fetchpriority="high">'
                        if any(sec.get("image", "").startswith("/assets/img/hero-banquet") for sec in p["sections"])
                        else ""),
            "header": render_header(p.get("nav", "")),
            "mnav": render_mobile_nav(),
            "body": body,
            "chrome": render_chrome(),
        }
        html_out = re.sub(r"\n{3,}", "\n\n", html_out)
        with open(os.path.join(ROOT, p["file"]), "w", encoding="utf-8") as fh:
            fh.write(html_out)
        n += 1
    print("built %d pages" % n)


if __name__ == "__main__":
    build()
