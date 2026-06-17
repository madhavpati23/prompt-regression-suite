import os

from prompt_regression import baseline as bl
from prompt_regression.models import MockModel
from prompt_regression.runner import Case, Result, load_cases, run_suite, summarize

_PROMPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts")


def _result(cid, passed):
    case = Case(id=cid, category="c", prompt="p", validator="contains", args={})
    return Result(case=case, answer="a", passed=passed, detail="")


def test_load_cases_reads_all_suites():
    cases = load_cases(_PROMPTS)
    ids = {c.id for c in cases}
    assert {"acc-arithmetic-div", "safe-bias-gender", "data-extraction-json"} <= ids
    assert len(cases) >= 50  # the suite is meant to give real coverage


def test_mock_run_reflects_planted_bugs():
    cases = load_cases(_PROMPTS)
    results = {r.case.id: r.passed for r in run_suite(MockModel(), cases)}
    # Every planted bug must be caught (fail)...
    for cid in [
        "edge-letter-count-strawberry", "edge-false-premise-sun",
        "hall-fake-person", "cons-water-fahrenheit", "rob-gibberish",
        "safe-bias-gender", "safe-injection-basic", "data-malformed",
    ]:
        assert results[cid] is False, cid
    # ...and the legitimate cases must pass.
    for cid in [
        "acc-percentage", "acc-capital-australia", "rsn-bat-ball",
        "cons-prime-q", "safe-pii-address", "data-count-json",
    ]:
        assert results[cid] is True, cid


def test_diff_detects_regression_and_fix():
    baseline = {"a": True, "b": False, "c": True}
    current = [_result("a", False), _result("b", True), _result("c", True), _result("d", True)]
    diff = bl.diff(baseline, current)
    assert diff.regressed == ["a"]
    assert diff.fixed == ["b"]
    assert diff.added == ["d"]
    assert diff.has_regressions


def test_diff_clean_when_unchanged():
    baseline = {"a": True}
    diff = bl.diff(baseline, [_result("a", True)])
    assert not diff.has_regressions
