import http.server
import socketserver
import os

PORT = 5000
WEB_DIR = os.path.join(os.path.dirname(__file__), "game", "build", "web")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        super().end_headers()

    def log_message(self, format, *args):
        pass  # silence request logs

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving Flappy Race at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
