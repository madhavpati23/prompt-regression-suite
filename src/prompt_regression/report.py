"""Human-readable report rendering for a run and a regression diff."""

from __future__ import annotations

from .baseline import Diff
from .runner import Result, Summary

_LINE = "=" * 64
_THIN = "-" * 64


def render_run(summary: Summary, results: list[Result]) -> str:
    out = [_LINE, f"  PROMPT-REGRESSION REPORT  -  model: {summary.model}", _LINE]
    out.append(f"  Total tests : {summary.total}")
    out.append(f"  Passed      : {summary.passed}")
    out.append(f"  Failed      : {summary.failed}")
    out.append(f"  PASS RATE   : {summary.pass_rate:.1f}%")
    out.append(_THIN)
    out.append("  PASS RATE BY CATEGORY:")
    for cat, (passed, total) in sorted(summary.by_category.items()):
        rate = passed / total * 100 if total else 0.0
        bar = "#" * int(rate // 10)
        out.append(f"   {cat:<14} {passed:>2}/{total:<3} {rate:5.0f}%  {bar}")

    failures = [r for r in results if not r.passed]
    if failures:
        out.append(_THIN)
        out.append("  FAILURES:")
        for r in failures:
            out.append(f"   [FAIL] {r.case.id} [{r.case.category}] {r.case.prompt}")
            out.append(f"          got : {r.answer}")
            out.append(f"          why : {r.detail}")
    out.append(_LINE)
    out.append("  NOTE: A high pass rate is evidence of quality on the TESTED")
    out.append("  inputs only -- it is not a certificate of safety. Untested")
    out.append("  inputs remain unknown.")
    out.append(_LINE)
    return "\n".join(out)


def render_diff(diff: Diff) -> str:
    out = [_THIN, "  REGRESSION DIFF vs BASELINE", _THIN]
    if diff.regressed:
        out.append(f"  REGRESSED ({len(diff.regressed)})  <-- newly failing:")
        out.extend(f"     - {cid}" for cid in diff.regressed)
    else:
        out.append("  REGRESSED (0)  -- no previously-passing case is now failing.")
    if diff.fixed:
        out.append(f"  FIXED ({len(diff.fixed)}):")
        out.extend(f"     + {cid}" for cid in diff.fixed)
    if diff.added:
        out.append(f"  ADDED ({len(diff.added)}): {', '.join(diff.added)}")
    if diff.removed:
        out.append(f"  REMOVED ({len(diff.removed)}): {', '.join(diff.removed)}")
    out.append(_THIN)
    return "\n".join(out)
