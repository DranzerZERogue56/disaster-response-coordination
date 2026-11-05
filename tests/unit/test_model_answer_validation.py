"""Named regression tests for DEF-015 (found by the property test P4): the validator accepted a model
answer whose reasoning was not text, or whose confidence was a boolean."""
import pytest

from src.classify_propose.service import ClassifyError, _validate

GOOD = {"severity": "Serious", "unit_type": "Medical", "confidence": 90, "reasoning": "matched keywords"}


def refused(answer):
    with pytest.raises(ClassifyError) as exc:
        _validate(answer)
    assert exc.value.code == "MODEL_OUTPUT_INVALID"


@pytest.mark.covers("FR-AGENT-01-AC2")
def test_a_well_formed_answer_is_accepted():
    _validate(GOOD)  # does not raise
    _validate({**GOOD, "confidence": 0})
    _validate({**GOOD, "confidence": 100})


@pytest.mark.covers("FR-AGENT-01-AC2")
@pytest.mark.defect("DEF-015")
@pytest.mark.parametrize("reasoning", [None, 0, 12.5, ["because"], {"why": "x"}, True, "", "   "])
def test_reasoning_must_be_non_empty_text(reasoning):
    refused({**GOOD, "reasoning": reasoning})


@pytest.mark.covers("FR-AGENT-01-AC2")
@pytest.mark.defect("DEF-015")
@pytest.mark.parametrize("confidence", [True, False, 90.0, 0.5, "90", None, -1, 101])
def test_confidence_must_be_a_whole_number_from_0_to_100(confidence):
    refused({**GOOD, "confidence": confidence})


@pytest.mark.covers("FR-AGENT-01-AC2")
@pytest.mark.parametrize("answer", [[], "text", 5, None, {}, {"severity": "Serious"}])
def test_an_answer_that_is_not_the_right_object_is_refused(answer):
    refused(answer)
