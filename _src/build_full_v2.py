"""Build every public route in the second visual direction, using latest Tilda IDs."""
import copy
import hashlib
import html
import json
import os
import re
from pathlib import Path
import build as B
import build_variant2 as V
import pages as P
import seo_v2 as SEO
from data import SITE, HALLS, FORMATS, LEGAL

ROOT = Path(__file__).resolve().parent.parent
CRITICAL_CSS = '.bn2 .v2-inner-content .band .btn--ghost{color:#2a2926!important;background:#fffdf9!important;border-color:#fffdf9!important}.bn2 .v2-inner-content .band .btn--ghost:hover{color:#2a2926!important;background:#e9dfd0!important}.bn2 .v2-inner-content .band .btn:not(.btn--ghost){color:#fffdf9!important;background:#a7432c!important}'
E = html.escape
INVENTORY = json.loads((ROOT / '_src/export_inventory.json').read_text(encoding='utf-8'))
FILES = {x['url']: x['file'] for x in INVENTORY if x['kind'] == 'page'}
PAGES = copy.deepcopy(P.PAGES)
for p in PAGES:
    p['file'] = FILES.get(p['url'], p['file'])
    if p['url'] == '/zaly':
        p['sections'] = [section for section in p['sections'] if section['t'] != 'cards']
    for section in p['sections']:
        if p['url'] == '/zaly/vystavochny' and section['t'] == 'gallery':
            section['title'] = 'Галерея'
            section['lede'] = ''
        if any(f['url'] == p['url'] for f in FORMATS):
            section.pop('note', None)
            if section['t'] == 'faq':
                section['items'] = [(q, a) for q, a in section['items'] if '6–12 месяцев' not in a]
        if section['t'] == 'cards':
            for card in section['items']:
                if card.get('url', '').startswith('/zaly/'):
                    card.pop('note', None)
                    card['short'] = ''



def asset(path):
    digest = hashlib.sha256((ROOT / path.lstrip('/')).read_bytes()).hexdigest()[:12]
    return path + '?v=' + digest


def logo():
    return '<a class="v2-brand v2-logo" href="/" aria-label="Банкет-Холл — главная"><img src="/assets/img/logo-banket-white.webp" alt="Банкет-Холл" width="4812" height="2716"></a>'


def header():
    return '<header class="v2-header"><div class="v2-wrap v2-header-inner">' + logo() + '''
    <button id="v2-menu-toggle" class="v2-menu-button" type="button" aria-expanded="false" aria-controls="v2-nav">Меню <span aria-hidden="true">☰</span></button>
    <nav id="v2-nav" class="v2-nav" aria-label="Основная навигация"><a href="/zaly">Залы</a><a href="/meropriyatiya">События</a><a href="/kejtering">Кейтеринг</a><a href="/galereya">Галерея</a><a href="/contacts">Контакты</a></nav>''' + f'<a class="v2-header-phone" href="{SITE["phone_href"]}">{SITE["phone"]}</a>' + V.link('Оставить заявку', '#zayavka', 'v2-button v2-button-small') + '</div></header>'


def footer():
    groups = [('Залы', [(h['name'],h['url']) for h in HALLS]), ('События', [(f['name'],f['url']) for f in FORMATS]), ('Услуги и информация', [('Кейтеринг','/kejtering'),('Аренда оборудования','/arenda-oborudovaniya'),('Галерея','/galereya'),('Контакты','/contacts')])]
    columns = ''.join('<div><h3>'+E(name)+'</h3>'+''.join(f'<a href="{url}">{E(label)}</a>' for label,url in links)+'</div>' for name,links in groups)
    legal = ''.join(f'<a href="{d["url"]}">{E(d["title"])}</a>' for d in LEGAL)
    return f'''<footer class="v2-footer" id="contacts"><div class="v2-wrap"><div class="v2-footer-top">{logo()}<p>{SITE['address']}<br>ВЦ «ДонЭкспоцентр»</p><div><a href="{SITE['phone_href']}">{SITE['phone']}</a><br><a href="mailto:{SITE['email']}">{SITE['email']}</a></div></div><nav class="v2-footer-links" aria-label="Все разделы сайта">{columns}</nav><details class="v2-legal-links"><summary>Правовая информация</summary>{legal}</details><div class="v2-footer-bottom"><span>© 2026 {SITE['legal_name']}</span><a href="/policy">Политика конфиденциальности</a></div></div></footer>'''


def form(page):
    native = (ROOT/'_src/native_form_v2.html').read_text(encoding='utf-8')
    native=native.replace('js/tilda-', '/assets/vendor/tilda-').replace('css/tilda-', '/assets/vendor/tilda-')
    # Stable original field names keep CRM mappings from the current site.
    native = native.replace('id="input_7511158071260"', 'id="f-guests"').replace('for="input_7511158071260"', 'for="f-guests"')
    native = native.replace('id="input_1788250367252"', 'id="f-format"').replace('for="input_1788250367252"', 'for="f-format"')
    native = native.replace('action=\'\'', 'action="https://forms.tildacdn.com/procces/"')
    native = native.replace('class="t-form js-form-proccess', 'class="v2-native-form t-form js-form-proccess')
    labels = {'guests':'Примерно гостей', 'event_date':'Дата мероприятия', 'event_type':'Формат мероприятия', 'Name':'Как к вам обращаться', 'Email':'Email (необязательно)', 'Phone':'Телефон для связи'}
    def add_label(match):
        tag=match.group(0)
        name=re.search(r'name="([^"]+)"',tag)
        ident=re.search(r'id="([^"]+)"',tag)
        if name and ident and name.group(1) in labels:
            return f'<label class="t-input-title" for="{ident.group(1)}">{labels[name.group(1)]}</label>'+tag
        return tag
    native=re.sub(r'<input\b[^>]*>',add_label,native)
    # Supplied pages can prefill the format without forcing a visitor to retype it.
    fmt = next((f['name'] for f in FORMATS if f['url'] == page['url']), '')
    if page['url'] == '/kejtering': fmt = 'Кейтеринг'
    native = native.replace('name="event_type"', 'name="event_type" data-default-format="'+E(fmt,quote=True)+'"')
    native = re.sub(r'(<input\s+type="text"\s+name="event_type".*?\bvalue=")"', lambda m:m.group(1)+E(fmt,quote=True)+'"',native,flags=re.S)
    return f'''<section class="v2-section v2-request-section r" id="rec3493827001" data-record-type="560"><div id="zayavka" class="v2-wrap v2-request-grid"><div>{V.heading('Ваше событие', 'Обсудим<br><em>детали.</em>')}<p class="v2-intro">Расскажите о формате и дате. Менеджер уточнит доступность и подготовит расчёт.</p><a class="v2-contact-phone" href="{SITE['phone_href']}">{SITE['phone']}</a><p class="v2-small">{SITE['hours']}</p></div><div>{native}<p class="v2-preview-message" role="status" aria-live="polite"></p></div></div></section>'''


def inner_hero(s, page):
    title = s.get('title','')
    crumbs = '<a href="/">Главная</a>'
    if page['url'].startswith('/zaly/'): crumbs += ' / <a href="/zaly">Залы</a>'
    elif any(f['url']==page['url'] for f in FORMATS): crumbs += ' / <a href="/meropriyatiya">События</a>'
    crumbs += ' / <span>'+re.sub('<[^>]+>','',title)+'</span>'
    image = '' if s.get('plain') or not s.get('image') else '<figure>'+V.pic(s['image'],s.get('alt',re.sub('<[^>]+>','',title)),'split',False)+'</figure>'
    return f'<section class="v2-inner-hero v2-wrap {"v2-inner-hero-plain" if not image else ""}"><nav class="v2-breadcrumbs" aria-label="Хлебные крошки">{crumbs}</nav><div class="v2-inner-hero-grid"><div><p class="v2-kicker">{s.get("eyebrow","")}</p><h1>{title}</h1><p class="v2-intro">{s.get("lede","")}</p>{B.buttons(s.get("actions"))}</div>{image}</div></section>'


def all_formats():
    items = sorted(FORMATS, key=lambda f: f['slug'] != 'novogodniy-korporativ')
    items = items + [{'slug': 'kejtering', 'url': '/kejtering', 'name': 'Кейтеринг'}]
    cards = []
    for index, f in enumerate(items, 1):
        photo = V.PHOTOS[f['slug']][0] if f['slug'] in V.PHOTOS else next(s['image'] for p in PAGES if p['url']=='/kejtering' for s in p['sections'] if s.get('image'))
        badge = '<span class="v2-booking-badge">Открыта бронь на Декабрь 2026</span>' if f['slug']=='novogodniy-korporativ' else ''
        cards.append(f'<a class="v2-format v2-occasion" href="{f["url"]}"><span class="v2-occasion-photo">{V.pic(photo, f["name"])}<span class="v2-occasion-number" aria-hidden="true">{index:02d}</span>{badge}</span><div><h3>{E(f["name"])}{V.ARROW}</h3><span class="v2-occasion-more">Подробнее о формате</span></div></a>')
    return f'<section class="v2-section v2-formats-section" id="formats"><div class="v2-wrap"><div class="v2-heading-row">{V.heading("02 / Поводы", "У каждого события<br><em>свой характер.</em>")}{V.link("Все форматы", "/meropriyatiya", "v2-text-link")}</div><div class="v2-format-grid">{"".join(cards)}</div></div></section>'


def main_content(page):
    B.seed_page_images(page)
    if page['url']=='/':
        return V.hero()+V.halls()+all_formats()+V.service()+V.pricing()+V.gallery()+V.faq()
    out = []
    for s in page['sections']:
        if s['t']=='hero_page': out.append(inner_hero(s,page))
        elif s['t']=='picker': out.append(V.halls().replace('id="zaly"','id="podbor"'))
        else: out.append('<div class="v2-inner-content">'+B.RENDER[s['t']](s).replace('<p></p>', '')+'</div>')
    return ''.join(out)


def build():
    routes={}
    for page in PAGES:
        content=main_content(page)
        full=header()+'<main id="v2-main">'+content+(form(page) if page['url']!='/404' else '<div id="zayavka"></div>')+'</main>'+footer()
        canonical=SITE['origin']+page['url']
        schema=SEO.structured(page)
        styles=''.join(f'<link rel="stylesheet" href="{asset(path)}">' for path in ['/assets/css/site.css','/assets/vendor/tilda-forms-1.0.min.css','/assets/css/variant2.css','/assets/css/full-v2.css'])
        bootstrap=f'<script src="{asset("/assets/js/forms-v2.js")}"></script>'
        scripts=bootstrap+''.join(f'<script defer src="{asset(path)}"></script>' for path in ['/assets/vendor/tilda-scripts-3.0.min.js','/assets/vendor/tilda-forms-1.0.min.js','/assets/vendor/tilda-date-picker-1.0.min.js','/assets/js/site.js','/assets/js/variant2.js'])
        robots='<meta name="robots" content="noindex,follow">' if page.get('noindex') else ''
        doc=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(page['title'])}</title><meta name="description" content="{E(page['desc'],quote=True)}"><link rel="canonical" href="{canonical}">{robots}<meta property="og:title" content="{E(page['title'],quote=True)}"><meta property="og:description" content="{E(page['desc'],quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{B.og_url(page.get('og') or V.COVERS['hero'])}"><meta name="theme-color" content="#f7f4ee"><link rel="icon" href="/assets/img/favicon.ico">{styles}{scripts}{schema}<meta property="og:type" content="website"><meta property="og:locale" content="ru_RU"><meta property="og:site_name" content="Банкет-Холл"></head><body class="v2-page"><div id="allrecords" data-tilda-project-id="{SITE['project_id']}" data-tilda-page-id="{page['file'].removeprefix('page').removesuffix('.html')}" data-tilda-formskey="{SITE['formskey']}" data-tilda-project-lang="RU" data-tilda-root-zone="com"><div class="bn2"><a class="v2-skip" href="#v2-main">Перейти к содержанию</a>{full}</div></div></body></html>'''
        (ROOT/page['file']).write_text(doc,encoding='utf-8')
        routes[page['url']]=page['file']
        if page['url']=='/': (ROOT/'variant2.html').write_text(doc,encoding='utf-8')
        # One self-contained page block for a blank Tilda page, including shared chrome/form.
        slug=page['url'].strip('/').replace('/','-') or 'glavnaya'
        dest=ROOT/'tilda/full-v2'/slug;dest.mkdir(parents=True,exist_ok=True)
        base=os.environ.get('ASSET_BASE','https://cdn.jsdelivr.net/gh/dimrurnd-cell/banket@codex/complete-site-v2/assets/').rstrip('/')+'/'
        block=schema+styles+'<style>'+CRITICAL_CSS+'</style>'+scripts+'<div class="bn2">'+full+'</div>'
        block=re.sub(r'(?<=[\s\"\'(,])/assets/',base,block)
        (dest/'block.html').write_text(block,encoding='utf-8')
        (dest/'seo.txt').write_text(page['title']+'\n'+page['desc']+'\n'+page['url']+'\nTilda page ID: '+page['file'],encoding='utf-8')
    (ROOT/'_src/routes-v2.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2),encoding='utf-8')
    rules=['DirectoryIndex page139817136.html','ErrorDocument 404 /404.html','RewriteEngine On',
           'RewriteCond %{HTTP:X-Forwarded-Proto} =http',
           r'RewriteRule ^(.*)$ https://banket-na5.ru/$1 [R=301,L]',
           r'RewriteCond %{HTTP_HOST} ^www\.banket-na5\.ru$ [NC]',
           r'RewriteRule ^(.*)$ https://banket-na5.ru/$1 [R=301,L]']
    for url,file in routes.items():
        if url not in ['/','/404']:rules.append('RewriteRule ^'+re.escape(url.strip('/'))+'/?$ '+file+' [L]')
    # Old preview identifiers resolve to their real, supplied Tilda counterparts.
    for old,new in [('page171645209.html','/novogodniy-korporativ'),('page171645109.html','/pominalny-obed'),('page171645009.html','/vypusknoy')]:
        (ROOT/old).write_text(f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={new}"><link rel="canonical" href="{SITE["origin"]+new}"><title>Переход</title></head><body><a href="{new}">Перейти на страницу</a></body></html>',encoding='utf-8')
    for name in ['.htaccess','htaccess']:(ROOT/name).write_text('\n'.join(rules)+'\n',encoding='utf-8')
    sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+SITE['origin']+p['url']+'</loc></url>' for p in PAGES if not p.get('noindex'))+'</urlset>'
    (ROOT/'sitemap.xml').write_text(sitemap,encoding='utf-8')
    SEO.export(ROOT, PAGES)
    print(f'Built {len(PAGES)} complete pages and Tilda blocks')


if __name__=='__main__':build()
