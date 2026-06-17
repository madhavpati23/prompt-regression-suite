import json

from prompt_regression.gating import decide
from prompt_regression.report import build_report, render_html, render_json
from prompt_regression.runner import Case, Result, summarize


def _r(cid, category, severity, passed):
    case = Case(id=cid, category=category, prompt=f"p-{cid}", validator="contains",
                args={"value": "x"}, severity=severity)
    return Result(case=case, answer="a", passed=passed, detail="" if passed else "why")


def test_verdict_ship_when_no_high_or_critical_fail():
    results = [_r("a", "accuracy", "medium", False), _r("b", "safety", "low", False)]
    assert decide(results).decision == "SHIP"


def test_verdict_blocks_on_critical_failure():
    v = decide([_r("a", "edge_cases", "critical", False)])
    assert v.decision == "BLOCK" and v.blockers[0].case.id == "a"


def test_high_safety_failure_blocks_but_high_accuracy_needs_signoff():
    assert decide([_r("s", "safety", "high", False)]).decision == "BLOCK"
    assert decide([_r("a", "accuracy", "high", False)]).decision == "NEEDS SIGN-OFF"


def test_passing_high_severity_does_not_block():
    assert decide([_r("s", "safety", "critical", True)]).decision == "SHIP"


def test_json_report_structure():
    results = [_r("a", "accuracy", "medium", True), _r("s", "safety", "critical", False)]
    summary = summarize("model-x", results)
    rpt = json.loads(render_json(summary, results))
    assert rpt["model"] == "model-x"
    assert rpt["verdict"] == "BLOCK"
    assert rpt["severity_failed"]["critical"] == 1
    assert rpt["by_category"]["safety"]["total"] == 1
    assert any(c["id"] == "s" and not c["passed"] for c in rpt["cases"])


def test_html_report_is_self_contained_and_shows_verdict():
    results = [_r("s", "safety", "critical", False)]
    html = render_html(summarize("model-x", results), results)
    assert "<!doctype html>" in html.lower()
    assert "BLOCK" in html
    assert "model-x" in html
