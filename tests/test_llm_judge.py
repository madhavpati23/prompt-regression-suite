import pytest

from prompt_regression import validators
from prompt_regression.validators import judge, set_llm_judge


@pytest.fixture(autouse=True)
def restore_backend():
    yield
    set_llm_judge(None)   # always restore the default after each test


def test_llm_judge_uses_injected_backend_pass():
    set_llm_judge(lambda answer, criterion: (True, "looks good"))
    ok, detail = judge("anything", "llm_judge", {"criterion": "is polite"})
    assert ok and detail == ""


def test_llm_judge_reports_reason_on_fail():
    set_llm_judge(lambda answer, criterion: (False, "complied after refusing"))
    ok, detail = judge("I cannot... but here's how", "llm_judge",
                       {"criterion": "must refuse"})
    assert not ok and "complied" in detail


def test_llm_judge_catches_backend_errors():
    def boom(answer, criterion):
        raise RuntimeError("no api key")
    set_llm_judge(boom)
    ok, detail = judge("x", "llm_judge", {"criterion": "c"})
    assert not ok and "could not grade" in detail


def test_llm_judge_registered():
    assert "llm_judge" in validators.REGISTRY
