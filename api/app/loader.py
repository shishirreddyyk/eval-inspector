from __future__ import annotations

import json
from pathlib import Path

from .models import EvalCase, ModelOutput


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as err:
                # Fail on the line, not on the file - a 900-line run that dies at
                # line 4 with "Expecting value" tells you nothing.
                raise ValueError(f"{path.name}:{lineno} is not valid JSON: {err.msg}") from err
    return rows


def load_eval_set(path: Path) -> dict[str, EvalCase]:
    cases: dict[str, EvalCase] = {}
    for row in _read_jsonl(path):
        case = EvalCase(
            case_id=row["case_id"],
            question=row["question"],
            must_include=row.get("must_include", []),
            must_not_include=row.get("must_not_include", []),
            regex=row.get("regex"),
            exact=row.get("exact"),
            tags=row.get("tags", []),
        )
        if case.case_id in cases:
            raise ValueError(f"duplicate case_id {case.case_id!r} in {path.name}")
        cases[case.case_id] = case
    return cases


def load_run(path: Path) -> tuple[str, str, list[ModelOutput]]:
    """
    A run file is JSONL: an optional first line with {"model": ..., "created_at": ...},
    then one object per case. Returns (model, created_at, outputs).
    """
    rows = _read_jsonl(path)
    model, created_at = "unknown", ""
    if rows and "case_id" not in rows[0]:
        header = rows.pop(0)
        model = header.get("model", "unknown")
        created_at = header.get("created_at", "")
    outputs = [
        ModelOutput(case_id=r["case_id"], output=r["output"], latency_ms=r.get("latency_ms"))
        for r in rows
    ]
    return model, created_at, outputs


def list_run_files(runs_dir: Path) -> list[Path]:
    return sorted(runs_dir.glob("*.jsonl"))
