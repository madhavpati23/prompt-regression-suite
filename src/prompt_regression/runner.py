"""Load test cases, run them against a model, and judge each answer."""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from .models import Model
from .validators import judge


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    prompt: str
    validator: str
    args: dict[str, Any]


@dataclass
class Result:
    case: Case
    answer: str
    passed: bool
    detail: str


def load_cases(prompts_dir: str) -> list[Case]:
    """Read every *.yaml file in prompts_dir into a flat list of cases."""
    cases: list[Case] = []
    seen: set[str] = set()
    for path in sorted(glob.glob(os.path.join(prompts_dir, "*.yaml"))):
        with open(path, encoding="utf-8") as fh:
            doc = yaml.safe_load(fh) or {}
        category = doc.get("category", os.path.splitext(os.path.basename(path))[0])
        for raw in doc.get("cases", []):
            cid = raw["id"]
            if cid in seen:
                raise ValueError(f"duplicate case id: {cid}")
            seen.add(cid)
            cases.append(Case(
                id=cid,
                category=category,
                prompt=raw["prompt"],
                validator=raw["validator"],
                args=raw.get("args", {}),
            ))
    if not cases:
        raise ValueError(f"no test cases found in {prompts_dir}")
    return cases


def run_suite(model: Model, cases: list[Case]) -> list[Result]:
    """Ask the model each prompt and judge the answer."""
    results: list[Result] = []
    for case in cases:
        answer = model.ask(case.prompt)
        passed, detail = judge(answer, case.validator, case.args)
        results.append(Result(case=case, answer=answer, passed=passed, detail=detail))
    return results


@dataclass
class Summary:
    model: str
    total: int
    passed: int
    by_category: dict[str, tuple[int, int]] = field(default_factory=dict)  # cat -> (pass, total)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total * 100 if self.total else 0.0


def summarize(model_name: str, results: list[Result]) -> Summary:
    by_cat: dict[str, list[int]] = {}
    passed = 0
    for r in results:
        bucket = by_cat.setdefault(r.case.category, [0, 0])
        bucket[1] += 1
        if r.passed:
            bucket[0] += 1
            passed += 1
    return Summary(
        model=model_name,
        total=len(results),
        passed=passed,
        by_category={k: (v[0], v[1]) for k, v in by_cat.items()},
    )
