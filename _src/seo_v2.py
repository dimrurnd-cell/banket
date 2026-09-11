"""SEO exports shared by standalone pages and Tilda code blocks."""
import csv
import html
import json
import re
from pathlib import Path
from data import SITE, FORMATS, COVERS
import images as IMG

CDN = 'https://cdn.jsdelivr.net/gh/dimrurnd-cell/banket@codex/complete-site-v2'

def plain(value):
    return html.unescape(re.sub('<[^>]+>', ' ', value)).strip()

def structured(page):
    if page.get('noindex'): return ''
    origin = SITE['origin']
    url = origin + page['url']
    title = plain(page['sections'][0].get('title', page['title']))
    business = {'@type':'LocalBusiness', '@id':origin+'/#business', 'name':SITE['name'], 'url':origin+'/', 'telephone':SITE['phone'], 'email':SITE['email'], 'image':CDN+'/assets/img/photo/supplied-svadba.webp', 'logo':CDN+'/assets/img/logo-banket-white.webp', 'address':{'@type':'PostalAddress','streetAddress':'проспект Михаила Нагибина, 30','addressLocality':'Ростов-на-Дону','addressCountry':'RU'}}
    nodes = [business, {'@type':'WebSite','@id':origin+'/#website','url':origin+'/','name':SITE['name'],'inLanguage':'ru-RU','publisher':{'@id':origin+'/#business'}}, {'@type':'WebPage','@id':url+'#webpage','url':url,'name':page['title'],'description':page['desc'],'inLanguage':'ru-RU','isPartOf':{'@id':origin+'/#website'},'about':{'@id':origin+'/#business'}}]
    if page['url'] != '/':
        crumbs=[('Главная',origin+'/')]
        if page['url'].startswith('/zaly/'):crumbs.append(('Залы',origin+'/zaly'))
        elif any(f['url']==page['url'] for f in FORMATS):crumbs.append(('События',origin+'/meropriyatiya'))
        crumbs.append((title,url))
        nodes.append({'@type':'BreadcrumbList','@id':url+'#breadcrumbs','itemListElement':[{'@type':'ListItem','position':i,'name':n,'item':u} for i,(n,u) in enumerate(crumbs,1)]})
    return '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':nodes},ensure_ascii=False).replace('<','\u003c')+'</script>'

def export(root, pages):
    directory = root/'tilda/full-v2'
    with (directory/'SEO-settings.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';')
        writer.writerow(['Адрес','Title','Description','Canonical','Индексация','Изображение для соцсетей','Папка кода'])
        for p in pages:
            writer.writerow([p['url'],p['title'],p['desc'],SITE['origin']+p['url'],'noindex,follow' if p.get('noindex') else 'index,follow',CDN+IMG.og(p.get('og') or COVERS['hero']),p['url'].strip('/').replace('/','-') or 'glavnaya'])
    (root/'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+SITE['origin']+'/sitemap.xml\n',encoding='utf-8')
