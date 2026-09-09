# -*- coding: utf-8 -*-
"""Build the independent editorial homepage; leave variant 1 untouched."""
import html
import hashlib
import os
import re
from pathlib import Path
import build as B
import pages as P
from data import SITE, HALLS, PHOTOS, FORM_OPTIONS, GALLERY, GALLERY_ALT, COVERS

ROOT = Path(__file__).resolve().parent.parent
E = html.escape
ARROW = '<span aria-hidden="true">↗</span>'

def pic(src, alt, slot="card", lazy=True):
    return B.picture(src, alt, lazy=lazy, slot=slot, priority=not lazy)

def link(text, href, cls="v2-button"):
    return f'<a class="{cls}" href="{href}">{text}{ARROW}</a>'

def heading(kicker, title, description=""):
    return f'<div class="v2-section-head"><p class="v2-kicker">{kicker}</p><h2>{title}</h2>' + (f'<p class="v2-intro">{description}</p>' if description else '') + '</div>'

def header():
    return f'''<header class="v2-header"><div class="v2-wrap v2-header-inner">
      <a class="v2-brand" href="/variant2.html" aria-label="Банкет-Холл — главная">БАНКЕТ<span>—</span>ХОЛЛ<small>ДОНЭКСПОЦЕНТР</small></a>
      <button id="v2-menu-toggle" class="v2-menu-button" type="button" aria-expanded="false" aria-controls="v2-nav">Меню <span aria-hidden="true">☰</span></button>
      <nav id="v2-nav" class="v2-nav" aria-label="Основная навигация"><a href="#zaly">Залы</a><a href="#formats">События</a><a href="#price">Стоимость</a><a href="#gallery">Галерея</a><a href="#contacts">Контакты</a></nav>
      <a class="v2-header-phone" href="{SITE['phone_href']}">{SITE['phone']}</a>
      {link('Проверить дату', '#zayavka', 'v2-button v2-button-small')}
    </div></header>'''

def hero():
    return f'''<section class="v2-hero v2-wrap" aria-labelledby="v2-title">
      <div class="v2-hero-copy"><p class="v2-kicker"><span class="v2-dot" aria-hidden="true"></span>Банкетные залы · Ростов-на-Дону</p>
        <h1 id="v2-title">Место для<br><em>вашего события.</em></h1>
        <p class="v2-hero-lede">Три зала на 50–2 500 гостей.<br>Кухня, сервировка и команда — на одной площадке.</p>
        <div class="v2-hero-actions">{link('Проверить дату', '#zayavka')}{link('Посмотреть залы', '#zaly', 'v2-text-link')}</div>
        <p class="v2-location">пр. М. Нагибина, 30 <span>·</span> ВЦ «ДонЭкспоцентр»</p>
      </div>
      <figure class="v2-hero-photo">{pic(COVERS['hero'], 'Сервированный банкетный зал со сценой и праздничным светом', 'split', False)}
        <figcaption><span>Место встречи.<br>Повод — ваш.</span><span class="v2-photo-seal">СОБИРАЕМ<br><b>с 2001</b><br>БЛИЗКИХ</span></figcaption>
      </figure>
    </section>
    <div class="v2-proof v2-wrap" aria-label="О площадке"><div><b>3</b><span>зала по одному адресу</span></div><div><b>25</b><span>лет организуем события</span></div><div><b>300</b><span>парковочных мест</span></div><a href="#zaly">Найдём ваш зал <span aria-hidden="true">↓</span></a></div>'''

def halls():
    short = [
        ('Камерно и уютно', 'Для свадьбы, юбилея или встречи своей команды. Есть место для сцены и танцпола.'),
        ('С размахом и музыкой', 'Для событий на 200–300 гостей. Сцена, свет, звук и гримёрные уже в зале.'),
        ('Городской масштаб', 'Конференции, выставки с фуршетом и корпоративы на тысячи гостей. Прямой подъезд для монтажа.'),
    ]
    cards = []
    for i, (h, (mood, note)) in enumerate(zip(HALLS, short)):
        full = P.HOME_HALLS[i]['note']
        cards.append(f'''<article class="v2-hall {'is-recommended' if i == 0 else ''}" data-v2-hall="{h['slug']}">
          <div class="v2-hall-image">{pic(COVERS[h['slug']], h['name'])}<span class="v2-hall-number">0{i+1}</span><span class="v2-recommend-badge" data-v2-badge {'hidden' if i else ''}>Подходит вам</span></div>
          <div class="v2-hall-body"><p class="v2-kicker">{mood}</p><h3>{h['name']}</h3><p class="v2-capacity">{h['cap']}</p><p class="v2-hall-note">{note}</p>
          <details class="v2-hall-details"><summary>Подробнее о пространстве</summary><p>{full}</p></details>
          {link('Смотреть зал', h['url'], 'v2-text-link')}</div></article>''')
    return f'''<section class="v2-section v2-halls-section" id="zaly"><div class="v2-wrap">
      <div class="v2-heading-row">{heading('01 / Пространства', 'Три зала.<br><em>Ваш масштаб.</em>')}<p class="v2-side-note">От ужина в кругу близких<br>до большого события на весь город.</p></div>
      <div class="v2-picker"><div><label for="v2-guests">Сколько будет гостей?</label><div class="v2-number"><input id="v2-guests" type="number" min="20" max="2500" step="1" value="120" inputmode="numeric" aria-describedby="v2-recommendation"><span>гостей</span></div></div>
        <div class="v2-range-wrap"><label class="visually-hidden" for="v2-range">Подобрать зал по количеству гостей</label><input id="v2-range" type="range" min="20" max="2500" step="1" value="120"><div class="v2-range-ticks"><span>20</span><span>2 500</span></div></div>
        <div class="v2-presets" aria-label="Быстрый выбор числа гостей"><button type="button" data-v2-guests="50">50</button><button type="button" data-v2-guests="150">150</button><button type="button" data-v2-guests="300">300</button><button type="button" data-v2-guests="1000">1 000</button></div>
      </div>
      <p id="v2-recommendation" class="v2-picker-status" aria-live="polite">На 120 гостей рекомендуем Банкетный зал. Можно выбрать зал просторнее.</p>
      <div class="v2-hall-grid">{''.join(cards)}</div>
      <p class="v2-halls-footnote">Список гостей вырос? При смене зала кухня, посуда, команда и договор остаются прежними.</p>
    </div></section>'''

def formats():
    items = [('Свадьбы', '/svadba', 'Один из самых важных дней', 'svadba'), ('Корпоративы', '/korporativ', 'Повод быть вместе', 'korporativ'), ('Дни рождения', '/den-rozhdeniya', 'Свои люди за одним столом', 'den-rozhdeniya')]
    cards = ''.join(f'<a class="v2-format" href="{url}">{pic(PHOTOS[slug][0], title)}<div><span>{sub}</span><h3>{title}{ARROW}</h3></div></a>' for title,url,sub,slug in items)
    return f'''<section class="v2-section v2-formats-section" id="formats"><div class="v2-wrap">
      <div class="v2-heading-row">{heading('02 / Поводы', 'У каждого события<br><em>свой характер.</em>')}{link('Все форматы', '/meropriyatiya', 'v2-text-link')}</div>
      <div class="v2-format-grid">{cards}</div><div class="v2-more-formats"><a href="/furshet">Фуршеты ↗</a><a href="/kofe-breyk">Кофе-брейки ↗</a><a href="/detskiy-prazdnik">Детские праздники ↗</a><a href="/vypusknoy">Выпускные ↗</a></div>
    </div></section>'''

def service():
    return f'''<section class="v2-section v2-service-section"><div class="v2-wrap v2-service-grid">
      <figure class="v2-service-photo">{pic('/assets/img/banquet-table.jpg', 'Сервировка банкетного стола', 'split')}<figcaption>Внимание к деталям — от кухни до сервировки.</figcaption></figure>
      <div>{heading('03 / Забота о деталях', 'Вы собираете близких.<br><em>Мы — всё остальное.</em>')}
        <div class="v2-benefit"><span>01</span><div><h3>Кухня прямо в здании</h3><p>Готовим на площадке и подаём блюда горячими.</p></div></div>
        <div class="v2-benefit"><span>02</span><div><h3>Команда под ваше событие</h3><p>Организуем работу официантов, барменов и координатора.</p></div></div>
        <div class="v2-benefit"><span>03</span><div><h3>Один договор. Общий план.</h3><p>Зал, меню и обслуживание согласуем вместе — до начала подготовки.</p></div></div>
        <div class="v2-service-links">{link('Выездной кейтеринг', '/kejtering', 'v2-text-link')}{link('Аренда оборудования', '/arenda-oborudovaniya', 'v2-text-link')}</div>
      </div></div></section>'''

def pricing():
    price = next(s for s in P.HOME['sections'] if s['t'] == 'price')
    rows = ''.join(f'<details class="v2-price-row"><summary><span>{n}</span><h3>{title}</h3><span class="v2-plus" aria-hidden="true">+</span></summary><p>{body}</p></details>' for n,title,body in price['items'])
    return f'''<section class="v2-section v2-price-section" id="price"><div class="v2-wrap v2-price-grid"><div>{heading('04 / Прозрачная смета', 'Стоимость.<br><em>Всё по пунктам.</em>')}<p class="v2-intro">Зал, меню, команда и выбранные опции.<br>Каждую часть сметы утверждаем до договора.</p>{link('Получить расчёт', '#zayavka')}<p class="v2-small">Предварительную смету пришлём в день обращения.</p></div><div>{rows}<p class="v2-price-note">Без условной цены «от N рублей». Расчёт — под вашу дату, формат и число гостей.</p><details class="v2-price-explain"><summary>Как мы рассчитываем стоимость</summary><p>{price['lede']}</p><p>{price['after']}</p></details></div></div></section>'''

def gallery():
    indices = [2, 6, 12]
    photos = ''.join(f'<button type="button" class="shot v2-gallery-shot v2-gallery-shot-{i}" data-full="{GALLERY[n-1]}" aria-label="Увеличить: {E(GALLERY_ALT[n], quote=True)}">{pic(GALLERY[n-1], GALLERY_ALT[n], "gallery")}<span aria-hidden="true">↗</span></button>' for i,n in enumerate(indices))
    return f'''<section class="v2-section" id="gallery"><div class="v2-wrap"><div class="v2-heading-row">{heading('05 / Атмосфера', 'Лучше один раз<br><em>почувствовать.</em>')}{link('Вся галерея', '/galereya', 'v2-text-link')}</div><div class="v2-gallery-grid">{photos}</div><p class="v2-gallery-caption">Фотографии наших залов и сервировки. Приезжайте посмотреть площадку вживую.</p></div></section>'''

def faq():
    qa = [('Можно посмотреть зал до бронирования?', 'Да. Оставьте заявку — менеджер согласует удобное время просмотра. Вы увидите зал, рассадку и место для программы вживую.'), ('Можно выбрать зал больше, чем рекомендует подбор?', 'Да. Рекомендация помогает сориентироваться по вместимости. Больший зал оставит больше места для сцены, танцпола и свободной рассадки.'), ('Как закрепить дату?', 'Менеджер проверит доступность, согласует зал и смету. Бронирование закрепляется предоплатой и договором.'), ('Можно со своим ведущим и декоратором?', 'Да. Заранее согласуйте работу ведущего, музыкантов, фотографа и декоратора с координатором площадки.')]
    rows = ''.join(f'<details class="v2-faq-item"><summary>{q}<span aria-hidden="true">+</span></summary><p>{a}</p></details>' for q,a in qa)
    return f'<section class="v2-section v2-faq-section"><div class="v2-wrap v2-faq-grid">{heading("06 / До встречи", "Вопросы<br><em>перед встречей.</em>")}<div>{rows}</div></div></section>'

def form():
    options=''.join(f'<option value="{E(o)}">{E(o)}</option>' for o in FORM_OPTIONS)
    return f'''<section class="v2-section v2-request-section" id="zayavka"><div class="v2-wrap v2-request-grid"><div>{heading('07 / Ваше событие', 'Начнём<br><em>с вашей даты.</em>')}<p class="v2-intro">Оставьте контакт — менеджер проверит дату и поможет выбрать зал. Сам запрос ни к чему не обязывает.</p><a class="v2-contact-phone" href="{SITE['phone_href']}">{SITE['phone']}</a><p class="v2-small">{SITE['hours']}<br>В рабочее время отвечаем за 15 минут.</p></div>
      <form id="request-form" class="v2-form" data-formskey="{SITE['formskey']}"><input type="hidden" name="formservices[]" value="{SITE['formservice']}"><input type="hidden" name="messenger-type" value="phone">
        <div class="v2-form-grid"><div class="v2-field v2-full"><label for="f-contact">Телефон для связи <span aria-hidden="true">*</span></label><input id="f-contact" name="messenger-id" type="tel" required autocomplete="tel" placeholder="+7 (___) ___-__-__"></div>
        <div class="v2-field"><label for="f-date">Дата мероприятия</label><input id="f-date" name="Выберите дату мероприятия" type="date"></div>
        <div class="v2-field"><label for="f-guests">Примерно гостей</label><input id="f-guests" name="Выберите количество гостей" type="number" min="1" max="2500" inputmode="numeric" placeholder="Например, 120"></div>
        <div class="v2-field v2-full"><label for="f-format">Формат</label><select id="f-format" name="мероприятие"><option value="">Пока выбираю</option>{options}</select></div></div>
        <details class="v2-form-extra"><summary>Добавить имя и пожелания</summary><div class="v2-field"><label for="f-name">Как к вам обращаться</label><input id="f-name" name="Name" autocomplete="name" placeholder="Имя"></div><div class="v2-field"><label for="f-note">Что важно учесть</label><textarea id="f-note" name="Комментарий" rows="3"></textarea></div></details>
        <label class="v2-consent"><input type="checkbox" name="soglasiye-persdan" value="yes" required><span>Согласен на обработку персональных данных в соответствии с <a href="/policy">политикой конфиденциальности</a>.</span></label>
        <button class="v2-button" type="submit">Проверить дату и получить расчёт {ARROW}</button><p class="v2-small">Доступность даты подтвердит менеджер.</p><p class="form-status" role="status" aria-live="polite"></p>
      </form></div></section>'''

def footer():
    return f'''<footer class="v2-footer" id="contacts"><div class="v2-wrap"><div class="v2-footer-top"><a class="v2-brand" href="/variant2.html">БАНКЕТ<span>—</span>ХОЛЛ<small>ДОНЭКСПОЦЕНТР</small></a><p>{SITE['address']}<br>ВЦ «ДонЭкспоцентр»</p><div><a href="mailto:{SITE['email']}">{SITE['email']}</a><br><a href="{SITE['phone_href']}">{SITE['phone']}</a></div>{link('Как добраться', '/contacts', 'v2-text-link')}</div><div class="v2-footer-bottom"><span>© 2026 {SITE['legal_name']}</span><a href="/policy">Политика конфиденциальности</a></div></div></footer>'''

def build():
    B.reset_page_images()
    content = hero()+halls()+formats()+service()+pricing()+gallery()+faq()
    body = f'<div class="bn2"><a class="v2-skip" href="#v2-main">Перейти к содержанию</a>{header()}<main id="v2-main">{content}{form()}</main>{footer()}</div>'
    document = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, follow"><title>Банкет-Холл — главная, вариант 2</title><meta name="description" content="Три банкетных зала на 50–2 500 гостей в Ростове-на-Дону. Кухня, сервировка и команда на одной площадке."><meta name="theme-color" content="#f7f4ee"><link rel="icon" href="/assets/img/favicon.ico"><link rel="stylesheet" href="/assets/css/site.css?v=4"><link rel="stylesheet" href="/assets/css/variant2.css"><script src="/assets/js/site.js?v=4" defer></script><script src="/assets/js/variant2.js" defer></script></head><body class="v2-page"><div id="allrecords" data-tilda-project-id="{SITE['project_id']}" data-tilda-page-id="139817136"></div>{body}</body></html>'''
    for asset in ('css/variant2.css', 'js/variant2.js'):
        fingerprint=hashlib.sha256((ROOT/'assets'/asset).read_bytes()).hexdigest()[:12]
        document=document.replace('/assets/'+asset+'"', '/assets/'+asset+'?v='+fingerprint+'"')
    (ROOT/'variant2.html').write_text(document,encoding='utf-8')
    # Existing global Tilda header/footer/native form remain responsible for chrome.
    # Inline the variant's styles and behaviour so a branch/CDN cache cannot break it.
    asset_base=os.environ.get('ASSET_BASE','https://cdn.jsdelivr.net/gh/dimrurnd-cell/banket@bb52f32db34d2458bf3ce1bb7c388d564c1be051/assets/').rstrip('/')+'/'
    tilda_content=re.sub(r'(?<=[\s\"\'(,])/assets/',asset_base, content)
    css=(ROOT/'assets/css/variant2.css').read_text(encoding='utf-8')
    js=(ROOT/'assets/js/variant2.js').read_text(encoding='utf-8')
    out=ROOT/'tilda/glavnaya-v2';out.mkdir(parents=True,exist_ok=True)
    (out/'block.html').write_text('<style>\n'+css+'\n</style>\n<div class="bn2">'+tilda_content+'</div>\n<script>\n'+js+'\n</script>\n',encoding='utf-8')
    print('Built variant2.html and tilda/glavnaya-v2/block.html')

if __name__=='__main__':
    build()
