from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(data_dir=DATA, db_path=str(tmp_path / "tags.db")))


def test_runs_lists_both_runs_with_pass_rates(client: TestClient):
    body = client.get("/api/runs").json()
    assert [r["run_id"] for r in body["runs"]] == [
        "2026-07-16_gemini-2.5-flash",
        "2026-07-09_gemini-2.0-flash",
    ]
    older = body["runs"][1]
    assert older["passed"] == 8 and older["pass_rate"] == 1.0


def test_run_detail_puts_failures_first_and_reports_unanswered_cases(client: TestClient):
    body = client.get("/api/runs/2026-07-16_gemini-2.5-flash").json()
    assert body["cases"][0]["verdict"] == "fail"
    assert body["unanswered"] == ["empty-context"]
    assert body["total"] == 7  # 7 answered, denominator is not padded


def test_run_detail_explains_why_a_case_failed(client: TestClient):
    body = client.get("/api/runs/2026-07-16_gemini-2.5-flash").json()
    warranty = next(c for c in body["cases"] if c["case_id"] == "warranty-length")
    failed = [c for c in warranty["checks"] if not c["passed"]]
    assert [c["target"] for c in failed] == ["lifetime"]
    assert failed[0]["kind"] == "must_not_include"


def test_unknown_run_404s(client: TestClient):
    assert client.get("/api/runs/does-not-exist").status_code == 404


def test_diff_counts_regressions_between_the_two_runs(client: TestClient):
    body = client.get(
        "/api/diff", params={"a": "2026-07-09_gemini-2.0-flash", "b": "2026-07-16_gemini-2.5-flash"}
    ).json()
    assert body["counts"]["regressed"] == 3
    assert body["counts"]["dropped"] == 1
    assert body["cases"][0]["status"] == "regressed"


def test_tagging_a_failure_persists_and_shows_up_on_the_run(client: TestClient):
    r = client.post("/api/tags", json={
        "run_id": "2026-07-16_gemini-2.5-flash",
        "case_id": "no-invented-policy",
        "tag": "hallucination",
        "note": "invented a price match policy that does not exist",
    })
    assert r.status_code == 200
    assert r.json()["counts"]["hallucination"] == 1

    body = client.get("/api/runs/2026-07-16_gemini-2.5-flash").json()
    tagged = next(c for c in body["cases"] if c["case_id"] == "no-invented-policy")
    assert tagged["tag"] == "hallucination"
    assert "price match" in tagged["note"]


def test_retagging_replaces_rather_than_duplicates(client: TestClient):
    payload = {"run_id": "2026-07-16_gemini-2.5-flash", "case_id": "cite-source", "tag": "formatting"}
    client.post("/api/tags", json=payload)
    r = client.post("/api/tags", json={**payload, "tag": "missing-citation"})
    counts = r.json()["counts"]
    assert counts.get("formatting") is None and counts["missing-citation"] == 1


def test_tagging_an_unknown_run_404s(client: TestClient):
    r = client.post("/api/tags", json={"run_id": "nope", "case_id": "x", "tag": "t"})
    assert r.status_code == 404
