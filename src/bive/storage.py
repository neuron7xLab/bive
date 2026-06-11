from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import VerificationReport, utc_now_iso
from .report import load_report

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    subject_scope TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class StoredReportSummary:
    report_id: str
    created_at: str
    status: str
    subject_scope: str

    def to_dict(self) -> dict[str, str]:
        return {
            "report_id": self.report_id,
            "created_at": self.created_at,
            "status": self.status,
            "subject_scope": self.subject_scope,
        }


class ReportStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(SCHEMA_SQL)
            current = conn.execute(
                "SELECT value FROM schema_metadata WHERE key = ?", ("schema_version",)
            ).fetchone()
            if current is None:
                conn.execute(
                    "INSERT INTO schema_metadata(key, value) VALUES (?, ?)",
                    ("schema_version", str(SCHEMA_VERSION)),
                )
            elif int(str(current["value"])) > SCHEMA_VERSION:
                raise RuntimeError("database_schema_version_newer_than_code")
            conn.commit()

    def save(self, report: VerificationReport) -> None:
        data = report.to_dict()
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO reports(report_id, created_at, status, subject_scope, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    report.report_id,
                    report.created_at,
                    report.final_status.value,
                    report.subject_scope,
                    json.dumps(data, ensure_ascii=False, sort_keys=True),
                ),
            )
            self.audit(
                "report_saved", report.report_id, {"status": report.final_status.value}, conn=conn
            )
            conn.commit()

    def get(self, report_id: str) -> VerificationReport | None:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT payload_json FROM reports WHERE report_id = ?", (report_id,)
            ).fetchone()
        if row is None:
            return None
        return VerificationReport.from_dict(json.loads(str(row["payload_json"])))

    def list(self, limit: int = 50) -> list[StoredReportSummary]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT report_id, created_at, status, subject_scope FROM reports ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [StoredReportSummary(**dict(row)) for row in rows]

    def audit(
        self,
        action: str,
        entity_id: str,
        metadata: dict[str, Any] | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        payload = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
        close = conn is None
        active = conn or self._connect()
        try:
            active.execute(
                "INSERT INTO audit_log(created_at, action, entity_id, metadata_json) VALUES (?, ?, ?, ?)",
                (utc_now_iso(), action, entity_id, payload),
            )
            if close:
                active.commit()
        finally:
            if close:
                active.close()

    def import_report_file(self, path: str | Path) -> VerificationReport:
        report = load_report(path)
        self.save(report)
        return report

    def healthcheck(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute("SELECT 1").fetchone()

    def schema_version(self) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT value FROM schema_metadata WHERE key = ?", ("schema_version",)
            ).fetchone()
        if row is None:
            raise RuntimeError("database_schema_version_missing")
        return int(str(row["value"]))

    def stats(self) -> dict[str, int]:
        with closing(self._connect()) as conn:
            report_count = int(conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0])
            audit_event_count = int(conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0])
        return {
            "report_count": report_count,
            "audit_event_count": audit_event_count,
            "schema_version": self.schema_version(),
        }
