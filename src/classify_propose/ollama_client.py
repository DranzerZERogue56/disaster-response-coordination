"""Ollama model client (docs/architecture.md section 9), Milestone 12 / CR-011.

The first real third-party seam: a model served by Ollama on THIS machine. It has the same `classify(report)`
shape as the fake rules model, so it slots into the fallback chain (chain.py) as the primary or smaller tier,
and every way it can fail is a distinct exception the chain treats as "try the next tier".

Rules this module keeps (each is tested in tests/unit/test_ollama_client.py against a stub server):
  * Local only. The base URL must be plain http to 127.0.0.1, localhost or ::1; anything else is refused at
    construction. NFR-SEC-01 says no reasoning step calls an external host; this is that rule in code.
  * No redirects are followed (a redirect could send the request, and the report text, elsewhere), no proxy
    is used, and a response over 1 MB is refused.
  * A hard time cap per call (default 60 s, FR-AGENT-04): a slow server raises OllamaTimeout.
  * Failure modes: nothing listening or a server error is OllamaUnavailable; 429 or 503 is OllamaBusy; a
    malformed or changed response is OllamaBadResponse. An answer of the wrong shape gets exactly one retry
    that restates the schema (architecture section 9), then OllamaBadResponse.
  * Only the report text is sent (location, severity text, description, time), not who sent it.
"""
import json
import re
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:1.7b"
DEFAULT_TIMEOUT = 60.0
MAX_RESPONSE_BYTES = 1024 * 1024
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ANSWER_KEYS = ("severity", "unit_type", "confidence", "reasoning")

SYSTEM_PROMPT = (
    "You classify emergency incident reports for a dispatcher. Reply with ONLY a JSON object with exactly these keys: "
    "severity (one of Minor, Moderate, Serious, Severe, Critical, following the NFPA-style scale), "
    "unit_type (one of Medical, Fire, Shelter, Security: the kind of responder to send), "
    "confidence (an integer from 0 to 100: how sure you are), "
    "reasoning (one or two short sentences). No other text."
)


class OllamaError(Exception):
    """Base for every failure of the model server; the fallback chain catches all of them."""


class OllamaUnavailable(OllamaError):
    """Nothing is listening, the model is missing, or the server returned an error."""


class OllamaTimeout(OllamaError):
    """The server did not answer within the time cap."""


class OllamaBusy(OllamaError):
    """The server is rate-limiting or out of capacity (HTTP 429 or 503)."""


class OllamaBadResponse(OllamaError):
    """The reply was malformed, oversized, redirected, or not an answer of the right shape."""


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # the 3xx then surfaces as an HTTPError, which we refuse


_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirects())


def _check_local(base_url):
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
        raise ValueError(f"the model server must be on this machine over plain http (127.0.0.1, localhost or ::1), got {base_url!r}")
    return base_url.rstrip("/")


def _prompt(report):
    lines = [f"location: {report.get('location')}", f"report: {report.get('severity_raw')}"]
    if report.get("description"):
        lines.append(f"description: {report['description']}")
    lines.append(f"time reported: {report.get('timestamp_reported')}")
    return "\n".join(lines)


class OllamaModel:
    version = "1"

    def __init__(self, model=DEFAULT_MODEL, base_url=DEFAULT_URL, timeout=DEFAULT_TIMEOUT):
        self.model = model
        self.base_url = _check_local(base_url)
        self.timeout = timeout
        self.identifier = f"ollama/{model}"

    def _post(self, messages):
        body = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0.2, "num_predict": 512},
                "messages": messages,
            }
        ).encode("utf-8")
        request = urllib.request.Request(self.base_url + "/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with _OPENER.open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503):
                raise OllamaBusy(f"the model server is busy (HTTP {exc.code})") from exc
            if 300 <= exc.code < 400:
                raise OllamaBadResponse(f"the model server tried to redirect (HTTP {exc.code}); redirects are refused") from exc
            raise OllamaUnavailable(f"the model server returned HTTP {exc.code}") from exc
        except TimeoutError as exc:
            raise OllamaTimeout(f"the model server did not answer within {self.timeout} s") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise OllamaTimeout(f"the model server did not answer within {self.timeout} s") from exc
            raise OllamaUnavailable(f"cannot reach the model server at {self.base_url}: {exc.reason}") from exc
        except OSError as exc:
            raise OllamaUnavailable(f"cannot reach the model server at {self.base_url}: {exc}") from exc
        if len(raw) > MAX_RESPONSE_BYTES:
            raise OllamaBadResponse("the model server's reply was larger than 1 MB")
        try:
            data = json.loads(raw)
            content = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise OllamaBadResponse("the model server's reply was not a chat message") from exc
        if not isinstance(content, str):
            raise OllamaBadResponse("the model server's reply had no text")
        return content

    @staticmethod
    def _parse(content):
        """The answer object from the model's text, or None if it is not a valid answer."""
        from src.classify_propose.service import (  # lazy: service imports the chain
            ClassifyError,
            _validate,
        )

        text = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        try:
            answer = json.loads(text)
        except ValueError:
            return None
        if not isinstance(answer, dict):
            return None
        try:
            _validate(answer)
        except ClassifyError:
            return None
        return {key: answer[key] for key in ANSWER_KEYS}

    def classify(self, report):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": _prompt(report)}]
        content = self._post(messages)
        answer = self._parse(content)
        if answer is None:
            messages += [
                {"role": "assistant", "content": content[:2000]},
                {
                    "role": "user",
                    "content": "Your previous answer was not valid. Reply with ONLY a JSON object with the keys "
                    "severity, unit_type, confidence (an integer 0 to 100) and reasoning, using the allowed values.",
                },
            ]
            answer = self._parse(self._post(messages))
        if answer is None:
            raise OllamaBadResponse("the model did not return a valid answer, even after one retry")
        return answer
