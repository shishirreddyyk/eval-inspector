from pathlib import Path

import pytest

from app.diffing import diff_runs
from app.grading import grade_run
from app.loader import load_eval_set, load_run
from app.models import CaseResult

DATA = Path(__file__).resolve().parent.parent / "data"


def test_load_eval_set_reads_every_case():
    cases = load_eval_set(DATA / "eval_set.jsonl")
    assert len(cases) == 8
    assert cases["unknown-question"].tags == ["refusal", "adversarial"]


def test_load_run_pulls_model_from_the_header_line():
    model, created_at, outputs = load_run(DATA / "runs" / "2026-07-09_gemini-2.0-flash.jsonl")
    assert model == "gemini-2.0-flash"
    assert created_at.startswith("2026-07-09")
    assert len(outputs) == 8


def test_bad_json_names_the_line_it_died_on(tmp_path: Path):
    p = tmp_path / "broken.jsonl"
    p.write_text('{"case_id": "a", "output": "ok"}\nnot json at all\n', encoding="utf-8")
    with pytest.raises(ValueError, match="broken.jsonl:2"):
        load_run(p)


def test_duplicate_case_ids_are_rejected(tmp_path: Path):
    p = tmp_path / "dupes.jsonl"
    p.write_text(
        '{"case_id": "a", "question": "q", "must_include": ["x"]}\n'
        '{"case_id": "a", "question": "q2", "must_include": ["y"]}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate case_id"):
        load_eval_set(p)


def _results(name: str) -> list[CaseResult]:
    cases = load_eval_set(DATA / "eval_set.jsonl")
    _, _, outputs = load_run(DATA / "runs" / f"{name}.jsonl")
    return grade_run(cases, outputs)


def test_diff_classifies_the_real_regression_between_the_two_sample_runs():
    diffs = diff_runs(_results("2026-07-09_gemini-2.0-flash"), _results("2026-07-16_gemini-2.5-flash"))
    by_id = {d.case_id: d.status for d in diffs}
    assert by_id["warranty-length"] == "regressed"      # invented lifetime coverage
    assert by_id["no-invented-policy"] == "regressed"   # invented a price match
    assert by_id["cite-source"] == "regressed"          # dropped the citation
    assert by_id["refund-window"] == "still_passing"


def test_regressions_sort_to_the_top():
    diffs = diff_runs(_results("2026-07-09_gemini-2.0-flash"), _results("2026-07-16_gemini-2.5-flash"))
    assert diffs[0].status == "regressed"


def test_a_case_dropped_by_the_newer_run_is_not_silently_a_pass():
    diffs = diff_runs(_results("2026-07-09_gemini-2.0-flash"), _results("2026-07-16_gemini-2.5-flash"))
    dropped = next(d for d in diffs if d.case_id == "empty-context")
    assert dropped.a_verdict == "pass" and dropped.b_verdict is None
    assert dropped.status == "dropped"  # not "still_passing" - the run never answered it
