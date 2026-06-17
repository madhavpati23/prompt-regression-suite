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
    assert {"acc-arithmetic-div", "safe-bias", "data-extraction-json"} <= ids


def test_mock_run_has_known_failures():
    cases = load_cases(_PROMPTS)
    summary = summarize("mock", run_suite(MockModel(), cases))
    # The mock answers accuracy/geography correctly but trips the planted bugs.
    assert summary.passed > 0
    assert summary.failed > 0
    assert summary.by_category["safety"][0] == 0  # all three safety cases fail


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
