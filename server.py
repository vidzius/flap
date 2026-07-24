import http.server
import socketserver
import os

PORT = 5000
WEB_DIR = os.path.join(os.path.dirname(__file__), "build", "web")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        # Required for SharedArrayBuffer (used by pygbag WASM)
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # silence request logs

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving Flappy Race at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
