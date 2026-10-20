"""Dashboard server (standard library only, plus the scientific stack in engine.py).

Run:  python app/server.py [--port 8765] [--no-browser]
"""
import argparse, json, mimetypes, os, socket, sys, threading, traceback, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine  # noqa: E402

STATIC = os.path.join(HERE, "static")
RESULTS = os.path.join(engine.ROOT, "research", "results.json")
FIG_DIR = os.path.join(engine.ROOT, "research", "figures")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % a))

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path):
        if not os.path.isfile(path):
            return self._send(404, {"error": "not found"})
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            self._send(200, f.read(), ctype)

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                return self._file(os.path.join(STATIC, "index.html"))
            if u.path == "/api/meta":
                return self._send(200, {"datasets": engine.DATASETS, "methods": engine.METHODS,
                                        "default_k": engine.DEFAULT_K, "default_noise": engine.DEFAULT_NOISE, "max_points": engine.MAX_POINTS})
            if u.path == "/api/results":
                with open(RESULTS, encoding="utf-8") as f:
                    return self._send(200, f.read())
            if u.path == "/api/sweep/noise":
                return self._send(200, engine.noise_sweep(q.get("dataset", ["moons"])[0], seeds=int(q.get("seeds", [3])[0])))
            if u.path == "/api/sweep/scale":
                return self._send(200, engine.scalability())
            if u.path.startswith("/figures/"):
                name = os.path.basename(u.path)
                return self._file(os.path.join(FIG_DIR, name))
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def do_POST(self):
        if self.path != "/api/cluster":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            return self._send(200, engine.cluster(req))
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})


def free_port(start):
    for p in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise RuntimeError("no free port")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    port = free_port(a.port)
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}/"
    print(f"\n  MST Clustering Dashboard running at {url}\n  Press Ctrl+C to stop.\n")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
