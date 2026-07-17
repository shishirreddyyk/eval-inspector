from __future__ import annotations

from dataclasses import dataclass

from .models import CaseResult, DiffStatus


@dataclass(frozen=True)
class CaseDiff:
    case_id: str
    question: str
    status: DiffStatus
    a_verdict: str | None
    b_verdict: str | None
    a_output: str | None
    b_output: str | None
    a_failed: list[str]
    b_failed: list[str]


def diff_runs(a: list[CaseResult], b: list[CaseResult]) -> list[CaseDiff]:
    """
    Two runs, case by case. Regressions sort to the top because that is the only
    reason anyone opens this screen after a model swap.
    """
    by_a = {r.case_id: r for r in a}
    by_b = {r.case_id: r for r in b}
    out: list[CaseDiff] = []

    for case_id in sorted(set(by_a) | set(by_b)):
        ra, rb = by_a.get(case_id), by_b.get(case_id)
        av = ra.verdict if ra else None
        bv = rb.verdict if rb else None
        if bv is None:
            # Answered in A, absent from B. This is the one that hides: drop your
            # three hardest cases and the pass rate goes UP.
            status: DiffStatus = "dropped"
        elif av is None:
            status = "new"
        elif av == "pass" and bv == "fail":
            status = "regressed"
        elif av == "fail" and bv == "pass":
            status = "fixed"
        elif av == "fail" and bv == "fail":
            status = "still_failing"
        else:
            status = "still_passing"
        out.append(
            CaseDiff(
                case_id=case_id,
                question=(ra or rb).question,  # type: ignore[union-attr]
                status=status,
                a_verdict=av,
                b_verdict=bv,
                a_output=ra.output if ra else None,
                b_output=rb.output if rb else None,
                a_failed=[c.target for c in ra.failed_checks] if ra else [],
                b_failed=[c.target for c in rb.failed_checks] if rb else [],
            )
        )

    order = {"regressed": 0, "dropped": 1, "still_failing": 2, "fixed": 3, "new": 4, "still_passing": 5}
    return sorted(out, key=lambda d: (order[d.status], d.case_id))
