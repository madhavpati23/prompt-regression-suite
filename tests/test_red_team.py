import os

from prompt_regression.models import MockModel
from prompt_regression.runner import load_cases, run_suite

_PROMPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _red_team_results():
    cases = [c for c in load_cases(_PROMPTS) if c.category == "red_team"]
    return {r.case.id: r for r in run_suite(MockModel(), cases)}


def test_red_team_pack_exists():
    assert len(_red_team_results()) >= 6


def test_model_refuses_common_jailbreaks():
    res = _red_team_results()
    for cid in ["rt-direct-override", "rt-roleplay-dan", "rt-hypothetical-framing",
                "rt-refusal-suppression", "rt-prefix-injection"]:
        assert res[cid].passed, f"{cid} should refuse the jailbreak"


def test_indirect_injection_is_caught_as_failure():
    # the sneaky one: instruction hidden in pasted content slips through the mock
    assert not _red_team_results()["rt-indirect-injection"].passed
