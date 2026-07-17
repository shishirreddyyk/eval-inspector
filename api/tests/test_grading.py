import pytest

from app.grading import grade, grade_run, missing_cases
from app.models import EvalCase, ModelOutput


def case(**kw) -> EvalCase:
    return EvalCase(case_id=kw.pop("case_id", "c1"), question=kw.pop("question", "q?"), **kw)


def out(text: str, case_id: str = "c1") -> ModelOutput:
    return ModelOutput(case_id=case_id, output=text)


def test_must_include_passes_regardless_of_case_and_spacing():
    r = grade(case(must_include=["30 days"]), out("Refunds within   30 DAYS of delivery."))
    assert r.verdict == "pass"


def test_must_include_failure_names_the_missing_string():
    r = grade(case(must_include=["30 days"]), out("Refunds are accepted promptly."))
    assert r.verdict == "fail"
    assert r.failed_checks[0].target == "30 days"
    assert "missing" in r.failed_checks[0].detail


def test_must_not_include_catches_an_invented_policy():
    r = grade(
        case(must_include=["not covered"], must_not_include=["yes, we match"]),
        out("Yes, we match any competitor price."),
    )
    assert r.verdict == "fail"
    assert {c.target for c in r.failed_checks} == {"not covered", "yes, we match"}


def test_a_case_fails_if_any_single_check_fails():
    r = grade(case(must_include=["12 months"], must_not_include=["lifetime"]),
              out("12 months, extendable to lifetime coverage."))
    assert r.verdict == "fail"
    assert len(r.checks) == 2 and len(r.failed_checks) == 1


def test_regex_check():
    c = case(regex=r"\[section\s?\d")
    assert grade(c, out("Exchanges allowed [section 4].")).verdict == "pass"
    assert grade(c, out("Exchanges are allowed.")).verdict == "fail"


def test_exact_check_ignores_surrounding_whitespace():
    assert grade(case(exact="yes"), out("  Yes  ")).verdict == "pass"
    assert grade(case(exact="yes"), out("Yes, definitely")).verdict == "fail"


def test_a_case_with_no_checks_raises_rather_than_passing():
    with pytest.raises(ValueError, match="no checks"):
        grade(case(), out("anything at all"))


def test_grade_run_skips_outputs_with_no_matching_case():
    cases = {"c1": case(must_include=["a"])}
    results = grade_run(cases, [out("a", "c1"), out("b", "ghost-case")])
    assert [r.case_id for r in results] == ["c1"]


def test_missing_cases_reports_what_the_run_never_answered():
    cases = {"c1": case(must_include=["a"]), "c2": case(case_id="c2", must_include=["b"])}
    assert missing_cases(cases, [out("a", "c1")]) == ["c2"]
