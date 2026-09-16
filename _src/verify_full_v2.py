"""Verify page coverage, links, labels, IDs and Tilda destinations without sending leads."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT=Path(__file__).resolve().parent.parent
routes=json.loads((ROOT/'_src/routes-v2.json').read_text(encoding='utf-8'))
inventory=json.loads((ROOT/'_src/export_inventory.json').read_text(encoding='utf-8'))
services=set(json.loads((ROOT/'_src/form-services-v2.json').read_text(encoding='utf-8')).values())

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(); self.ids=[]; self.links=[]; self.services=[]; self.h1=0; self.labels=[]; self.fields=[]
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1': self.h1+=1
        if 'id' in a:self.ids.append(a['id'])
        if tag=='label' and 'for' in a:self.labels.append(a['for'])
        if tag=='input' and a.get('name') in ['guests','event_date','event_type','Name','Email','Phone']:self.fields.append(a.get('id'))
        if tag=='input' and a.get('name')=='formservices[]':self.services.append(a.get('value'))
        for key in ['href','src']:
            if a.get(key):self.links.append(a[key])
        if a.get('srcset'):self.links.extend(x.strip().split()[0] for x in a['srcset'].split(','))

errors=[]
for entry in inventory:
    if entry['kind']=='page' and routes.get(entry['url'])!=entry['file']:errors.append('Export route missing: '+entry['url'])
for route,file in routes.items():
    p=Page((ROOT/file).read_text(encoding='utf-8'))
    if p.h1!=1:errors.append(route+': expected one h1')
    if len(p.ids)!=len(set(p.ids)):errors.append(route+': duplicate IDs')
    if route!='/404' and set(p.services)!=services:errors.append(route+': wrong form services')
    if any(x not in p.labels for x in p.fields):errors.append(route+': field without label')
    for link in p.links:
        path=unquote(urlsplit(link).path)
        if link.startswith('/') and path not in routes and not (ROOT/path.lstrip('/')).exists():errors.append(route+': missing '+link)
        if link.startswith('#') and link[1:] not in p.ids:errors.append(route+': missing anchor '+link)
if errors:raise SystemExit('\n'.join(errors))
print(f'PASS: {len(routes)} pages, export coverage, links/images, anchors, labels and four Tilda receivers')
