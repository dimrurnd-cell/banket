"""Local preview with the same public page routes as the Apache export."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import json
import os

ROOT = Path(__file__).resolve().parent.parent
ROUTES = json.loads((ROOT / '_src/routes-v2.json').read_text(encoding='utf-8'))
ROUTES['/'] = 'variant2.html'


class Preview(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path.rstrip('/') or '/'
        if path in ROUTES:
            self.path = '/' + ROUTES[path]
        super().do_GET()


if __name__ == '__main__':
    port = int(os.environ.get('BANKET_PREVIEW_PORT', '8766'))
    print(f'Preview: http://127.0.0.1:{port}/variant2.html', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Preview).serve_forever()
