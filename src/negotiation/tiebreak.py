"""The tiebreak (FR-COORD-01, FR-COORD-03): one rule, as a pure function.

When two proposals cannot both be satisfied, the winner is decided by, in order:
  1. severity (a higher level wins),
  2. information richness (a higher score wins; how it is counted is ADR 0007),
  3. reported-first (the earlier report wins),
and a proposal that is identical on all three is a true tie, broken by the lower proposal id so the answer
never changes between runs (the Resolve Negotiation Conflict contract: resolving the same pair twice gives
the same winner).

Nothing here touches the database. src/negotiation/service.py applies it to stored proposals and logs it.
"""
import re
from dataclasses import dataclass
from datetime import UTC, datetime

SEVERITY_RANK = {"Minor": 1, "Moderate": 2, "Serious": 3, "Severe": 4, "Critical": 5}

# ADR 0007: words that carry no information of their own are not counted.
STOP_WORDS = frozenset(
    ["a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "is", "are", "was", "were", "not", "no", "it", "this", "that", "with", "for", "from", "by", "be", "has", "have", "had", "there", "their", "then", "so", "but"]
)

_WORD = re.compile(r"\b[a-z]{2,}\b")  # a word of two or more letters; "4th" and "2nd" are not words
_NUMBER = re.compile(r"\b\d+\b")  # a standalone number: a street or building number
_AND = re.compile(r"\band\b")

DESCRIPTION_BONUS = 2
SPECIFIC_LOCATION_BONUS = 2


@dataclass(frozen=True)
class Contender:
    proposal_id: int
    severity: str
    richness: int
    reported_at: str  # ISO 8601; a time with no offset is taken as UTC


@dataclass(frozen=True)
class Resolution:
    winner: int
    loser: int
    reason: str  # "severity" | "richness" | "reported-first" | "true-tie"


def _specific_location(location):
    return bool(_NUMBER.search(location) or "&" in location or "/" in location or _AND.search(location.lower()))


def richness(report):
    """The information richness score of a report (ADR 0007): distinct content words in `severity_raw` and
    `description` (1 point each), plus 2 if a separate description was supplied, plus 2 if the location is
    specific. A mapping with those keys (missing or empty ones count as nothing)."""
    description = report.get("description") or ""
    text = f"{report.get('severity_raw') or ''} {description}".lower()
    words = {w for w in _WORD.findall(text) if w not in STOP_WORDS}
    score = len(words)
    if description.strip():
        score += DESCRIPTION_BONUS
    if _specific_location(report.get("location") or ""):
        score += SPECIFIC_LOCATION_BONUS
    return score


def _moment(text):
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def compare(a, b):
    """Resolve two contending proposals. Raises ValueError for the same proposal twice or an unknown severity."""
    if a.proposal_id == b.proposal_id:
        raise ValueError("a proposal cannot contend with itself")
    for contender in (a, b):
        if contender.severity not in SEVERITY_RANK:
            raise ValueError(f"unknown severity {contender.severity!r}")

    def result(winner, loser, reason):
        return Resolution(winner.proposal_id, loser.proposal_id, reason)

    rank_a, rank_b = SEVERITY_RANK[a.severity], SEVERITY_RANK[b.severity]
    if rank_a != rank_b:
        return result(a, b, "severity") if rank_a > rank_b else result(b, a, "severity")
    if a.richness != b.richness:
        return result(a, b, "richness") if a.richness > b.richness else result(b, a, "richness")
    moment_a, moment_b = _moment(a.reported_at), _moment(b.reported_at)
    if moment_a != moment_b:
        return result(a, b, "reported-first") if moment_a < moment_b else result(b, a, "reported-first")
    first, second = (a, b) if a.proposal_id < b.proposal_id else (b, a)
    return result(first, second, "true-tie")
