"""The Ollama client, tested across a real HTTP seam against a stub server (docs/architecture.md section 9).

Each failure mode of the third-party dependency the design lists (slow, down, rate-limited, changed response)
is provoked here and must raise the matching error, so the fallback chain can move on.
"""
import pytest

from src.classify_propose.ollama_client import (
    OllamaBadResponse,
    OllamaBusy,
    OllamaModel,
    OllamaTimeout,
    OllamaUnavailable,
)
from tests.ollama_stub import GOOD, StubOllama

REPORT = {
    "location": "4th & Main St",
    "severity_raw": "person fell, visible leg injury, conscious and talking",
    "description": None,
    "timestamp_reported": "2026-11-01T12:00:00+00:00",
    "reporting_unit": "field-unit-7",
}


@pytest.fixture
def stub():
    with StubOllama() as s:
        yield s


def model(stub, **kw):
    return OllamaModel(model="qwen3:1.7b", base_url=stub.url, timeout=kw.pop("timeout", 5.0), **kw)


def test_a_good_answer_comes_back_in_the_shape_the_service_needs(stub):
    assert model(stub).classify(REPORT) == GOOD


def test_it_names_itself_so_a_stored_proposal_says_which_model_answered(stub):
    m = model(stub)
    assert m.identifier == "ollama/qwen3:1.7b" and m.version


def test_the_request_is_a_non_streaming_json_chat_without_thinking_and_carries_only_the_report_text(stub):
    model(stub).classify(REPORT)
    sent = stub.requests[0]
    assert (sent["model"], sent["stream"], sent["format"], sent["think"]) == ("qwen3:1.7b", False, "json", False)
    assert sent["options"]["temperature"] == 0.2 and sent["options"]["num_predict"] == 512
    text = " ".join(m["content"] for m in sent["messages"])
    assert "4th & Main St" in text and "visible leg injury" in text
    assert "field-unit-7" not in text  # who sent it is not needed to classify it


def test_a_thinking_block_in_front_of_the_json_is_ignored(stub):
    stub.mode = "think"
    assert model(stub).classify(REPORT) == GOOD


def test_nothing_listening_is_reported_as_unavailable():
    with StubOllama() as s:
        url = s.url
    # the server is stopped: the port refuses connections
    with pytest.raises(OllamaUnavailable):
        OllamaModel(base_url=url, timeout=10.0).classify(REPORT)  # Windows takes about 2 s to report a refused connection


def test_a_slow_server_times_out_instead_of_waiting_forever(stub):
    stub.mode, stub.delay = "slow", 1.5
    with pytest.raises(OllamaTimeout):
        model(stub, timeout=0.3).classify(REPORT)


@pytest.mark.parametrize("mode", ["429", "503"])
def test_a_busy_or_rate_limited_server_is_reported_as_busy(stub, mode):
    stub.mode = mode
    with pytest.raises(OllamaBusy):
        model(stub).classify(REPORT)


def test_a_server_error_is_reported_as_unavailable(stub):
    stub.mode = "500"
    with pytest.raises(OllamaUnavailable):
        model(stub).classify(REPORT)


@pytest.mark.parametrize("mode", ["garbage", "no_message", "prose", "huge"])
def test_a_changed_or_malformed_response_is_reported_as_bad(stub, mode):
    stub.mode = mode
    with pytest.raises(OllamaBadResponse):
        model(stub).classify(REPORT)


def test_an_answer_of_the_wrong_shape_gets_one_retry_that_restates_the_schema(stub):
    stub.script = ["wrong_shape"]  # first call is invalid, then the default mode answers properly
    assert model(stub).classify(REPORT) == GOOD
    assert len(stub.requests) == 2
    retry_text = " ".join(m["content"] for m in stub.requests[1]["messages"])
    assert "previous answer was not valid" in retry_text and "severity" in retry_text


def test_an_answer_that_is_wrong_twice_is_given_up_on_after_exactly_two_calls(stub):
    stub.mode = "wrong_shape"
    with pytest.raises(OllamaBadResponse):
        model(stub).classify(REPORT)
    assert len(stub.requests) == 2


def test_a_redirect_is_never_followed(stub):
    stub.mode = "redirect"
    with pytest.raises(OllamaBadResponse):
        model(stub).classify(REPORT)
    assert len(stub.requests) == 1


@pytest.mark.parametrize("url", ["http://example.com:11434", "http://10.0.0.5:11434", "https://127.0.0.1:11434", "http://127.0.0.1.evil.test", "ftp://127.0.0.1"])
def test_it_refuses_to_talk_to_anything_but_this_machine_over_plain_http(url):
    with pytest.raises(ValueError, match="this machine"):
        OllamaModel(base_url=url)


@pytest.mark.parametrize("url", ["http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"])
def test_it_accepts_the_loopback_addresses(url):
    assert OllamaModel(base_url=url).identifier.startswith("ollama/")


# ---- DEF-035: the thinking-block stripper must be linear, not quadratic ------------------------------------


@pytest.mark.defect("DEF-035")
def test_a_reply_of_many_unclosed_thinking_tags_is_handled_in_linear_time():
    import time

    reply = "<think>" * 30000  # about 210 KB; the old regex needed minutes
    started = time.perf_counter()
    assert OllamaModel._parse(reply) is None  # not a valid answer, and quickly so
    assert time.perf_counter() - started < 1.0


def test_a_closed_thinking_block_is_removed_and_everything_else_is_kept():
    answer = '{"severity": "Serious", "unit_type": "Medical", "confidence": 90, "reasoning": "r"}'
    assert OllamaModel._parse("<think>a</think>" + answer + "<think>b</think>") is not None
    assert OllamaModel._parse("<think>one</think><think>two</think>" + answer)["severity"] == "Serious"


def test_an_unclosed_thinking_tag_leaves_the_text_alone_so_the_answer_is_refused_not_guessed():
    answer = '{"severity": "Serious", "unit_type": "Medical", "confidence": 90, "reasoning": "r"}'
    assert OllamaModel._parse("<think>never closed " + answer) is None

