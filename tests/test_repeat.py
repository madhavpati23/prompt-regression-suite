from prompt_regression.runner import Case, run_suite


class FlakyModel:
    """Alternates pass/fail answers so we can test repeat + threshold logic."""
    name = "flaky"

    def __init__(self):
        self._n = 0

    def ask(self, prompt: str) -> str:
        self._n += 1
        return "yes" if self._n % 2 == 1 else "no"   # pass, fail, pass, fail, ...


def _case():
    return Case(id="c", category="accuracy", prompt="p", validator="contains",
                args={"value": "yes"})


def test_single_run_is_backward_compatible():
    # deterministic-ish: 1 run, threshold 1.0 -> behaves like the old runner
    r = run_suite(FlakyModel(), [_case()], repeat=1, pass_threshold=1.0)[0]
    assert r.runs == 1 and r.passes == 1 and r.passed and not r.flaky


def test_threshold_requires_enough_passes():
    # 4 runs -> 2 pass, 2 fail -> rate 0.5
    r = run_suite(FlakyModel(), [_case()], repeat=4, pass_threshold=0.75)[0]
    assert r.passes == 2 and r.runs == 4
    assert not r.passed          # 0.5 < 0.75
    assert r.flaky               # passed some but not all


def test_threshold_met_passes():
    r = run_suite(FlakyModel(), [_case()], repeat=4, pass_threshold=0.5)[0]
    assert r.passed and r.flaky  # 0.5 >= 0.5, still flaky


def test_failing_run_is_shown_as_representative():
    r = run_suite(FlakyModel(), [_case()], repeat=2, pass_threshold=1.0)[0]
    assert not r.passed and r.answer == "no"   # surfaces the failing run
