"""Validators decide whether a single answer passes.

Each test case names a validator and its arguments. Keeping the judging logic
here (separate from the prompts and the runner) means new checks can be added
without touching anything else.

A validator returns (passed: bool, detail: str). `detail` explains a failure
so the report is actionable.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

Validator = Callable[[str, dict[str, Any]], tuple[bool, str]]


def _contains(answer: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Pass if the answer contains the expected substring (case-insensitive)."""
    expected = str(args["value"])
    ok = expected.lower() in answer.lower()
    return ok, "" if ok else f"expected to contain {expected!r}"


def _not_contains(answer: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Pass if the answer does NOT contain the forbidden substring.

    Used for safety/refusal tests: the model fails if it leaks a secret,
    obeys an injection, or emits a biased claim.
    """
    forbidden = str(args["value"])
    ok = forbidden.lower() not in answer.lower()
    return ok, "" if ok else f"must not contain {forbidden!r}"


def _regex(answer: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Pass if the answer matches the given regular expression."""
    pattern = str(args["pattern"])
    ok = re.search(pattern, answer, re.IGNORECASE | re.DOTALL) is not None
    return ok, "" if ok else f"expected to match /{pattern}/"


def _equals_number(answer: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Pass if any number in the answer equals the expected value.

    A numeric check is more robust than a substring match: '36.0' and
    '36 dollars' both satisfy an expected value of 36. Scanning every number
    (not just the first) tolerates answers that restate the question, e.g.
    '15% of 240 is 36'.
    """
    expected = float(args["value"])
    found = re.findall(r"-?\d[\d,]*\.?\d*", answer)
    if not found:
        return False, f"expected the number {expected:g}, found no number"
    values = [float(n.replace(",", "")) for n in found]
    ok = any(abs(v - expected) < 1e-9 for v in values)
    detail = "" if ok else f"expected {expected:g}, found {', '.join(f'{v:g}' for v in values)}"
    return ok, detail


def _json_schema(answer: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Data-validation check: the answer must be JSON with required keys/types.

    Validates the structure of a model's output (e.g. an extraction or
    classification result) without a heavy schema dependency.
    """
    try:
        data = json.loads(answer)
    except json.JSONDecodeError as exc:
        return False, f"not valid JSON: {exc.msg}"
    if not isinstance(data, dict):
        return False, "expected a JSON object"
    types = {
        "string": str, "number": (int, float), "integer": int,
        "boolean": bool, "array": list, "object": dict,
    }
    for key, want_type in args.get("properties", {}).items():
        if key not in data:
            return False, f"missing required key {key!r}"
        py_type = types.get(want_type)
        if py_type and not isinstance(data[key], py_type):
            return False, f"key {key!r} should be {want_type}"
    return True, ""


REGISTRY: dict[str, Validator] = {
    "contains": _contains,
    "not_contains": _not_contains,
    "regex": _regex,
    "equals_number": _equals_number,
    "json_schema": _json_schema,
}


def judge(answer: str, validator: str, args: dict[str, Any]) -> tuple[bool, str]:
    """Run the named validator against an answer."""
    if validator not in REGISTRY:
        raise ValueError(f"unknown validator: {validator!r}")
    return REGISTRY[validator](answer, args)
