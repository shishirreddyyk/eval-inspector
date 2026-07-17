from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

CheckKind = Literal["must_include", "must_not_include", "regex", "exact"]
Verdict = Literal["pass", "fail"]
DiffStatus = Literal[
    "regressed", "dropped", "still_failing", "fixed", "new", "still_passing"
]


@dataclass(frozen=True)
class EvalCase:
    """One question plus the checks that decide whether an answer is acceptable."""

    case_id: str
    question: str
    must_include: list[str] = field(default_factory=list)
    must_not_include: list[str] = field(default_factory=list)
    regex: str | None = None
    exact: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ModelOutput:
    case_id: str
    output: str
    latency_ms: int | None = None


@dataclass(frozen=True)
class CheckResult:
    kind: CheckKind
    target: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    question: str
    output: str
    verdict: Verdict
    checks: list[CheckResult]
    latency_ms: int | None = None

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed]


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    model: str
    created_at: str
    total: int
    passed: int

    @property
    def pass_rate(self) -> float:
        return 0.0 if self.total == 0 else round(self.passed / self.total, 4)
