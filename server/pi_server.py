"""
Minimal HTTP server for the Pi - no external packages required.
Replicates the /execute endpoint from main.py.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from robot.command_executor import execute_command

PORT = 8000


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._json(200, {"status": "online", "message": "Rover server is running"})

    def do_POST(self):
        if self.path == '/execute':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                result = execute_command(payload)
                self._json(200, result)
            except Exception as e:
                self._json(500, {"status": "error", "error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"Rover server running on port {PORT}")
    server.serve_forever()
