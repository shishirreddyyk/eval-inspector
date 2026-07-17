from __future__ import annotations

import re

from .models import CaseResult, CheckResult, EvalCase, ModelOutput


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def grade(case: EvalCase, out: ModelOutput) -> CaseResult:
    """
    Deterministic checks only. Every verdict here is reproducible and explainable -
    if a case fails you can point at the exact check and the exact string.
    An LLM judge would catch more nuance and would also make the eval itself
    a moving target, so that stays out until there is a labeled set to calibrate it against.
    """
    checks: list[CheckResult] = []
    hay = _norm(out.output)

    for target in case.must_include:
        ok = _norm(target) in hay
        checks.append(
            CheckResult("must_include", target, ok, "found" if ok else "missing from output")
        )

    for target in case.must_not_include:
        ok = _norm(target) not in hay
        checks.append(
            CheckResult(
                "must_not_include", target, ok, "absent" if ok else "appeared in output"
            )
        )

    if case.regex is not None:
        ok = re.search(case.regex, out.output) is not None
        checks.append(CheckResult("regex", case.regex, ok, "matched" if ok else "no match"))

    if case.exact is not None:
        ok = _norm(case.exact) == hay
        checks.append(
            CheckResult("exact", case.exact, ok, "identical" if ok else "differs from expected")
        )

    if not checks:
        # A case with no checks is a bug in the eval set, not a passing case.
        raise ValueError(f"eval case {case.case_id!r} defines no checks")

    verdict = "pass" if all(c.passed for c in checks) else "fail"
    return CaseResult(
        case_id=case.case_id,
        question=case.question,
        output=out.output,
        verdict=verdict,
        checks=checks,
        latency_ms=out.latency_ms,
    )


def grade_run(cases: dict[str, EvalCase], outputs: list[ModelOutput]) -> list[CaseResult]:
    results: list[CaseResult] = []
    for out in outputs:
        case = cases.get(out.case_id)
        if case is None:
            # An output with no eval case is silently ignored by most harnesses.
            # Surfacing it is the point of this tool.
            continue
        results.append(grade(case, out))
    return results


def missing_cases(cases: dict[str, EvalCase], outputs: list[ModelOutput]) -> list[str]:
    """Cases the run never answered. A run that skips its hard cases looks great otherwise."""
    answered = {o.case_id for o in outputs}
    return sorted(set(cases) - answered)
