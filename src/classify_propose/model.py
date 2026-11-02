"""The swappable "brain" behind Classify & Propose (docs/architecture.md
§5, FR-AGENT-01, FR-AGENT-02).

Everything the rest of the system knows about the model is the
`ClassifierModel` shape below: give it a report, get back a plain dict
(severity, unit_type, confidence, reasoning). To use a different model,
write another class with the same `classify` method and register it in
`get_model`. Nothing in service.py changes.

Planned order (decided with Ben, 2026-11-01): Ollama is the main model,
a tiny local Python-side model is the fallback, and this rules-based
`FakeModel` stands in for both until they exist. Neither real model is
built yet.
"""
import os

SEVERITIES = ("Minor", "Moderate", "Serious", "Severe", "Critical")
UNIT_TYPES = ("Medical", "Fire", "Shelter", "Security")

# Word lists the fake model reads. Deliberately crude: it only has to be
# predictable, so tests and the demo behave the same way every run.
_UNIT_WORDS = {
    "Medical": ("injur", "fell", "hurt", "bleed", "breath", "conscious", "chest", "pain"),
    "Fire": ("fire", "smoke", "burn", "flame", "explosion"),
    "Shelter": ("evacuat", "homeless", "displaced", "shelter", "flood"),
    "Security": ("weapon", "threat", "gun", "riot", "assault"),
}
_SEVERE_WORDS = ("not breathing", "unconscious", "explosion", "trapped", "gun")
_SERIOUS_WORDS = ("injur", "bleed", "fire", "smoke", "chest", "fell")


class FakeModel:
    """Rules-based stand-in: same inputs always give the same outputs."""

    identifier = "fake-rules"
    version = "1"

    def classify(self, report):
        text = f"{report['severity_raw']} {report.get('description') or ''}".lower()

        scores = {
            unit: sum(word in text for word in words)
            for unit, words in _UNIT_WORDS.items()
        }
        unit_type, hits = max(scores.items(), key=lambda item: item[1])
        if hits == 0:
            return {
                "severity": "Moderate",
                "unit_type": "Medical",
                "confidence": 40,
                "reasoning": "No recognizable keywords in the report; guessing Medical.",
            }

        if any(word in text for word in _SEVERE_WORDS):
            severity = "Severe"
        elif any(word in text for word in _SERIOUS_WORDS):
            severity = "Serious"
        else:
            severity = "Moderate"
        return {
            "severity": severity,
            "unit_type": unit_type,
            "confidence": min(60 + 15 * hits, 95),
            "reasoning": f"Matched {hits} {unit_type} keyword(s) in the report text.",
        }


def get_model():
    """Pick the model from CLASSIFY_MODEL (default: the fake one)."""
    name = os.environ.get("CLASSIFY_MODEL", "fake")
    if name == "fake":
        return FakeModel()
    raise ValueError(f"Unknown CLASSIFY_MODEL {name!r}; only 'fake' exists so far")
