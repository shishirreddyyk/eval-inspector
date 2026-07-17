from __future__ import annotations

import sqlite3
from pathlib import Path


class TagStore:
    """
    Failure tags: why did this case fail, in a human's words. This is the part
    a pass-rate number throws away, and it is the part that tells you what to fix.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                run_id   TEXT NOT NULL,
                case_id  TEXT NOT NULL,
                tag      TEXT NOT NULL,
                note     TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (run_id, case_id)
            )
            """
        )
        self.conn.commit()

    def set_tag(self, run_id: str, case_id: str, tag: str, note: str = "") -> None:
        self.conn.execute(
            "INSERT INTO tags (run_id, case_id, tag, note) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(run_id, case_id) DO UPDATE SET tag = excluded.tag, note = excluded.note",
            (run_id, case_id, tag, note),
        )
        self.conn.commit()

    def for_run(self, run_id: str) -> dict[str, dict[str, str]]:
        rows = self.conn.execute(
            "SELECT case_id, tag, note FROM tags WHERE run_id = ?", (run_id,)
        ).fetchall()
        return {r["case_id"]: {"tag": r["tag"], "note": r["note"]} for r in rows}

    def counts(self) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT tag, COUNT(*) AS n FROM tags GROUP BY tag ORDER BY n DESC"
        ).fetchall()
        return {r["tag"]: r["n"] for r in rows}

    def close(self) -> None:
        self.conn.close()
