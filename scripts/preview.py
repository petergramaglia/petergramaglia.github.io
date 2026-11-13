#!/usr/bin/env python3
"""Serve the checkout without browser caching while iterating on the artwork."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        # A cached document can still send validators on its first reload.
        # Always return current bytes, including same-second asset rewrites.
        for name in ['If-Modified-Since', 'If-None-Match']:
            if name in self.headers:
                del self.headers[name]
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 4173), partial(PreviewHandler, directory=str(ROOT)))
    print('Preview: http://localhost:4173 (browser caching disabled)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
