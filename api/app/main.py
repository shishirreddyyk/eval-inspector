from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .diffing import diff_runs
from .grading import grade_run, missing_cases
from .loader import list_run_files, load_eval_set, load_run
from .models import RunSummary
from .store import TagStore

DATA_DIR = Path(os.environ.get("EVAL_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))


class TagRequest(BaseModel):
    run_id: str
    case_id: str
    tag: str = Field(min_length=1, max_length=40)
    note: str = ""


def create_app(data_dir: Path = DATA_DIR, db_path: str = ":memory:") -> FastAPI:
    app = FastAPI(title="eval-inspector", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    store = TagStore(db_path)

    def _cases():
        return load_eval_set(data_dir / "eval_set.jsonl")

    def _run_path(run_id: str) -> Path:
        path = data_dir / "runs" / f"{run_id}.jsonl"
        if not path.exists():
            raise HTTPException(404, f"no run named {run_id!r}")
        return path

    def _results(run_id: str):
        model, created_at, outputs = load_run(_run_path(run_id))
        cases = _cases()
        return model, created_at, cases, outputs, grade_run(cases, outputs)

    @app.get("/api/health")
    def health():
        return {"ok": True, "data_dir": str(data_dir)}

    @app.get("/api/runs")
    def runs():
        cases = _cases()
        summaries = []
        for path in list_run_files(data_dir / "runs"):
            model, created_at, outputs = load_run(path)
            results = grade_run(cases, outputs)
            s = RunSummary(
                run_id=path.stem,
                model=model,
                created_at=created_at,
                total=len(results),
                passed=sum(r.verdict == "pass" for r in results),
            )
            summaries.append({**asdict(s), "pass_rate": s.pass_rate})
        return {"runs": sorted(summaries, key=lambda s: s["created_at"], reverse=True)}

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str):
        model, created_at, cases, outputs, results = _results(run_id)
        tags = store.for_run(run_id)
        return {
            "run_id": run_id,
            "model": model,
            "created_at": created_at,
            "total": len(results),
            "passed": sum(r.verdict == "pass" for r in results),
            # Unanswered cases are reported, not quietly dropped from the denominator.
            "unanswered": missing_cases(cases, outputs),
            "cases": [
                {**asdict(r), "tag": tags.get(r.case_id, {}).get("tag"),
                 "note": tags.get(r.case_id, {}).get("note", "")}
                for r in sorted(results, key=lambda r: (r.verdict == "pass", r.case_id))
            ],
        }

    @app.get("/api/diff")
    def diff(a: str, b: str):
        _, _, _, _, ra = _results(a)
        _, _, _, _, rb = _results(b)
        diffs = diff_runs(ra, rb)
        return {
            "a": a,
            "b": b,
            "counts": {
                k: sum(d.status == k for d in diffs)
                for k in ("regressed", "dropped", "still_failing", "fixed", "new", "still_passing")
            },
            "cases": [asdict(d) for d in diffs],
        }

    @app.post("/api/tags")
    def tag(req: TagRequest):
        _run_path(req.run_id)
        store.set_tag(req.run_id, req.case_id, req.tag, req.note)
        return {"ok": True, "counts": store.counts()}

    @app.get("/api/tags")
    def tag_counts():
        return {"counts": store.counts()}

    return app


app = create_app()
