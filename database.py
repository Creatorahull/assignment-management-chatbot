import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "data/assignments.db"


class Database:
    """SQLite wrapper for storing assignments, deadlines, and progress."""

    def __init__(self):
        Path("data").mkdir(exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject     TEXT NOT NULL,
                    solution    TEXT,
                    deadline    TEXT,
                    estimated_hours REAL DEFAULT 4,
                    daily_plan  TEXT,
                    progress    INTEGER DEFAULT 0,
                    created_at  TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    # ── Write ──────────────────────────────────────────────────────────────────
    def save_assignment(self, data: dict) -> int:
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO assignments (subject, solution, deadline, estimated_hours, daily_plan, progress)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                data.get("subject", "Unknown"),
                data.get("solution", ""),
                data.get("deadline", ""),
                data.get("estimated_hours", 4),
                json.dumps(data.get("daily_plan", []))
            ))
            conn.commit()
            return cur.lastrowid

    def update_progress(self, assignment_id: int, progress: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE assignments SET progress = ? WHERE id = ?",
                (progress, assignment_id)
            )
            conn.commit()

    # ── Read ───────────────────────────────────────────────────────────────────
    def get_all_assignments(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM assignments ORDER BY deadline ASC"
            ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["daily_plan"] = json.loads(d.get("daily_plan") or "[]")
            result.append(d)
        return result

    def get_upcoming(self, days: int = 7) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM assignments
                WHERE deadline >= date('now')
                  AND deadline <= date('now', ? || ' days')
                  AND progress < 100
                ORDER BY deadline ASC
            """, (str(days),)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["daily_plan"] = json.loads(d.get("daily_plan") or "[]")
            result.append(d)
        return result

    def delete_assignment(self, assignment_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
            conn.commit()
