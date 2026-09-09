"""Local preview with the same public page routes as the Apache export."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import pages

ROOT = Path(__file__).resolve().parent.parent
ROUTES = {p['url'].rstrip('/') or '/': p['file'] for p in pages.PAGES}
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
    print('Preview: http://127.0.0.1:8765/variant2.html', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Preview).serve_forever()
