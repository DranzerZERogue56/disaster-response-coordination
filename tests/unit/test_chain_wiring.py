"""How the app builds its model chain from the environment, including the kill switch (CR-011)."""
import pytest

from src.classify_propose.chain import build_chain

VARS = ("OLLAMA_ENABLED", "OLLAMA_URL", "OLLAMA_MODEL", "OLLAMA_SMALLER_MODEL", "OLLAMA_TIMEOUT", "CLASSIFY_MODEL")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in VARS:
        monkeypatch.delenv(name, raising=False)


def tiers(chain):
    return {name: model for name, model in chain.tiers}


def test_by_default_only_the_rules_tier_exists_so_nothing_touches_a_real_model():
    assert list(tiers(build_chain())) == ["rules"]


def test_switching_it_on_adds_the_ollama_model_as_the_primary_tier_with_the_rules_tier_behind_it(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    chain = build_chain()
    assert list(tiers(chain)) == ["primary", "rules"]
    assert tiers(chain)["primary"].identifier == "ollama/qwen3:1.7b" and tiers(chain)["primary"].timeout == 60.0


def test_model_url_and_timeout_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_MODEL", "phi4-mini:latest")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11500")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "12.5")
    primary = tiers(build_chain())["primary"]
    assert (primary.identifier, primary.base_url, primary.timeout) == ("ollama/phi4-mini:latest", "http://localhost:11500", 12.5)


def test_a_second_model_name_adds_the_smaller_tier_between_the_primary_and_the_rules(monkeypatch):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_SMALLER_MODEL", "smollm2:360m")
    chain = build_chain()
    assert list(tiers(chain)) == ["primary", "smaller", "rules"] and tiers(chain)["smaller"].identifier == "ollama/smollm2:360m"


@pytest.mark.parametrize("value", ["0", "", "no", "false"])
def test_the_kill_switch_turns_the_model_off_without_a_redeploy_even_with_everything_else_set(monkeypatch, value):
    monkeypatch.setenv("OLLAMA_ENABLED", value)
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_SMALLER_MODEL", "smollm2:360m")
    assert list(tiers(build_chain())) == ["rules"]


def test_a_url_that_is_not_this_machine_is_refused_loudly_and_the_app_keeps_working_on_the_rules_tier(monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_URL", "http://example.com:11434")
    assert list(tiers(build_chain())) == ["rules"]
    assert "this machine" in capsys.readouterr().err


def test_a_timeout_that_is_not_a_positive_number_is_refused_loudly_and_the_default_is_used(monkeypatch, capsys):
    monkeypatch.setenv("OLLAMA_ENABLED", "1")
    monkeypatch.setenv("OLLAMA_TIMEOUT", "soon")
    assert tiers(build_chain())["primary"].timeout == 60.0
    assert "OLLAMA_TIMEOUT" in capsys.readouterr().err
