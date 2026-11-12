"""A stand-in Ollama server for tests: a real HTTP server on 127.0.0.1 whose behaviour each test chooses.

It lets the Ollama client be tested across a real network seam, and lets every failure mode be provoked on
demand: down (stopped), slow, busy (429/503), server error, malformed, changed shape, oversized, a redirect.
`script` is a list of modes consumed one per call; when it runs out the default `mode` is used.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

GOOD = {"severity": "Serious", "unit_type": "Medical", "confidence": 90, "reasoning": "clear injury, patient talking"}


class StubOllama:
    def __init__(self, mode="ok", delay=0.0, answer=None):
        self.mode = mode
        self.delay = delay
        self.answer = answer if answer is not None else dict(GOOD)
        self.script = []
        self.requests = []
        self._server = None
        self._thread = None

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def start(self):
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # keep test output quiet
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    stub.requests.append(json.loads(body))
                except ValueError:
                    stub.requests.append({"unparsed": body.decode("utf-8", "replace")})
                mode = stub.script.pop(0) if stub.script else stub.mode
                stub._respond(self, mode)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    # -- behaviours ------------------------------------------------------------------------------

    def _send(self, handler, status, payload, raw=False, headers=()):
        data = payload if raw else json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(data)))
        for key, value in headers:
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(data)

    def _chat(self, content):
        return {"model": "stub", "message": {"role": "assistant", "content": content}, "done": True, "done_reason": "stop"}

    def _respond(self, handler, mode):
        answer = json.dumps(self.answer)
        if mode == "slow":
            time.sleep(self.delay)
            mode = "ok"
        if mode == "ok":
            self._send(handler, 200, self._chat(answer))
        elif mode == "think":
            self._send(handler, 200, self._chat("<think>the person can talk, so not critical</think>\n" + answer))
        elif mode in ("429", "503"):
            self._send(handler, int(mode), {"error": "server busy, try again later"})
        elif mode == "500":
            self._send(handler, 500, {"error": "model runner crashed"})
        elif mode == "garbage":
            self._send(handler, 200, b"this is not json at all", raw=True)
        elif mode == "no_message":
            self._send(handler, 200, {"done": True})
        elif mode == "prose":
            self._send(handler, 200, self._chat("I think it is probably Moderate, send a medic."))
        elif mode == "wrong_shape":
            self._send(handler, 200, self._chat(json.dumps({"severity": "Catastrophic", "unit_type": "Medical", "confidence": 90, "reasoning": "x"})))
        elif mode == "huge":
            self._send(handler, 200, b"x" * (3 * 1024 * 1024), raw=True)
        elif mode == "redirect":
            self._send(handler, 302, b"", raw=True, headers=[("Location", "http://example.invalid/steal")])
        else:  # pragma: no cover - a typo in a test
            raise AssertionError(f"unknown stub mode {mode!r}")
