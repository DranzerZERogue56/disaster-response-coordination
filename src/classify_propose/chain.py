"""Model fallback chain (docs/architecture.md section 5), Milestone 11 / FR-DEGRADE-02.

If the local model fails to load or crashes mid-session, the agent must not go silent. The order is: the
primary model, then a smaller model, then the rules-based workflow, then a manual workflow (a human). The
manual step is not a model: when every tier has failed, the caller escalates to a person.

Every `classify` call starts at the top, so a primary that crashed on one report is used again as soon as
it works. If every tier fails, the whole chain is retried `RetryPolicy.attempts` times, `every_seconds`
apart (6 times, 10 seconds: a minute), and the first success stops the retries. Only after the last retry
fails does it raise `ChainExhausted`. A tier fails by raising an Exception or by returning an answer that
does not pass validation. An empty slot (None) is skipped: today only the rules tier exists, because the
Ollama models are not wired yet.

The answer carries `model_identifier` and `model_version` of the tier that gave it, so a stored proposal
names the model that really answered, and `tier`. When an earlier tier failed in the pass that succeeded,
the reasoning starts with a note saying so, so a person reviewing it can see it came from a fallback.
"""
import time
from dataclasses import dataclass

from src.classify_propose.model import get_model

TIER_NAMES = ("primary", "smaller", "rules")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 6
    every_seconds: float = 10.0


class ChainExhausted(Exception):
    """Every tier failed on every attempt. `attempts` counts passes (first plus retries); `errors` maps each
    tier that exists to its last error."""

    def __init__(self, attempts, errors):
        self.attempts = attempts
        self.errors = errors
        detail = "; ".join(f"{tier}: {error}" for tier, error in errors.items())
        super().__init__(f"Every model failed after {attempts} attempts ({detail})")


class ModelChain:
    identifier = "model-chain"  # only used if an answer somehow names no model; every answer does
    version = "1"

    def __init__(self, primary=None, smaller=None, rules=None, retry=RetryPolicy(), sleep=time.sleep):  # noqa: B008 - frozen dataclass
        self.tiers = [(name, model) for name, model in zip(TIER_NAMES, (primary, smaller, rules), strict=True) if model is not None]
        if not self.tiers:
            raise ValueError("a model chain needs at least one model")
        self.retry = retry
        self.sleep = sleep

    def _one_pass(self, report, errors):
        # imported here, not at the top: service.py imports this module
        from src.classify_propose.service import _validate

        failed = []
        for name, model in self.tiers:
            try:
                answer = model.classify(report)
                _validate(answer)
            except Exception as exc:  # noqa: BLE001 - any failure of a model means "try the next tier"
                errors[name] = f"{type(exc).__name__}: {exc}"
                failed.append(name)
                continue
            answer = dict(answer)
            if failed:
                answer["reasoning"] = (
                    f"[Answered by the {name} tier because the {', '.join(failed)} tier failed.] {answer['reasoning']}"
                )
            answer.update(model_identifier=model.identifier, model_version=model.version, tier=name)
            return answer
        return None

    def classify(self, report):
        errors = {}
        answer = self._one_pass(report, errors)
        attempts = 1
        for _ in range(self.retry.attempts):
            if answer is not None:
                break
            self.sleep(self.retry.every_seconds)
            answer = self._one_pass(report, errors)
            attempts += 1
        if answer is None:
            raise ChainExhausted(attempts, errors)
        return answer


def build_chain():
    """The chain the app uses. Only the rules tier exists today (the model chosen by CLASSIFY_MODEL, the fake
    rules model); the primary and smaller slots take the Ollama models when they are wired."""
    return ModelChain(primary=None, smaller=None, rules=get_model())
