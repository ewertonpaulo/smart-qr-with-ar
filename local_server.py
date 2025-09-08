import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PUBLIC_DIR = Path("public").resolve()
MEDIA_SUBDIR = PUBLIC_DIR / "media"
DEFAULT_PORT = 8000

_httpd = None
_http_thread = None

class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_local_server() -> int:
    global _httpd, _http_thread
    if _httpd:
        return _httpd.server_port

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    port = DEFAULT_PORT
    while True:
        try:
            handler_args = {'directory': str(PUBLIC_DIR)}
            _httpd = ThreadingHTTPServer(("0.0.0.0", port), lambda *a, **kw: QuietHTTPRequestHandler(*a, **handler_args))
            break
        except OSError:
            port += 1
            if port > DEFAULT_PORT + 50:
                raise RuntimeError("Could not find a free port.")

    _http_thread = threading.Thread(target=_httpd.serve_forever, daemon=True)
    _http_thread.start()
    return port

def stop_local_server():
    global _httpd
    if _httpd:
        _httpd.shutdown()
        _httpd.server_close()
        _httpd = None