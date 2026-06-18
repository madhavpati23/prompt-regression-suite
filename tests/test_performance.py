import time

from prompt_regression.report import performance, render_run
from prompt_regression.runner import Case, run_suite


class SlowModel:
    name = "slow"

    def ask(self, prompt: str) -> str:
        time.sleep(0.02)   # ~20ms
        return "ok"


def _case(cid="c"):
    return Case(id=cid, category="accuracy", prompt="p", validator="contains", args={"value": "ok"})


def test_latency_is_measured():
    r = run_suite(SlowModel(), [_case()])[0]
    assert r.latency_ms >= 15    # at least ~20ms minus jitter


def test_performance_summary_and_sla_breaches():
    results = run_suite(SlowModel(), [_case("a"), _case("b")])
    perf = performance(results, sla_ms=5)     # 5ms SLA -> both breach
    assert perf["avg_ms"] > 0 and perf["max_ms"] >= perf["avg_ms"]
    assert set(perf["breaches"]) == {"a", "b"}
    assert perf["slowest_id"] in {"a", "b"}


def test_no_breaches_under_generous_sla():
    results = run_suite(SlowModel(), [_case("a")])
    assert performance(results, sla_ms=100000)["breaches"] == []


def test_render_run_includes_latency_and_sla_line():
    from prompt_regression.runner import summarize
    results = run_suite(SlowModel(), [_case("a")])
    text = render_run(summarize("slow", results), results, sla_ms=5)
    assert "LATENCY" in text and "SLA 5 ms" in text
