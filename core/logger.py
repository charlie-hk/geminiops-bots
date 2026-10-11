"""
Activity logger shared by every bot in this framework.

Every run of every bot writes one structured record per attempt (success or
failure) to a JSONL file and an optional human-readable summary line to
stdout. This is the piece the job post asked for explicitly: "record
activity and report on successes and failed attempts."

Design notes:
- JSONL (one JSON object per line) instead of CSV, because each bot logs a
  different shape of detail (a calendar bot logs event ids, a scraper logs
  a target URL, a test runner logs a check name) and JSONL tolerates that
  without a shared column schema.
- A tiny HTML report generator (reports/build_report.py) turns the JSONL
  into a static page a non-technical client can open and skim.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "reports" / "logs"


@dataclass
class ActivityLogger:
    bot_name: str
    log_dir: Path = DEFAULT_LOG_DIR
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def __post_init__(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / f"{self.bot_name}.jsonl"

    def _write(self, record: dict[str, Any]) -> None:
        record = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run_id": self.run_id,
            "bot": self.bot_name,
            **record,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def success(self, action: str, **details: Any) -> None:
        self._write({"status": "success", "action": action, "details": details})
        print(f"[{self.bot_name}] OK  {action} {details if details else ''}")

    def failure(self, action: str, error: str, **details: Any) -> None:
        self._write({"status": "failure", "action": action, "error": error, "details": details})
        print(f"[{self.bot_name}] FAIL {action}: {error}")

    def info(self, action: str, **details: Any) -> None:
        self._write({"status": "info", "action": action, "details": details})

    @contextmanager
    def step(self, action: str, **details: Any) -> Iterator[None]:
        """Wrap one unit of work; logs success or failure automatically.

        Usage:
            with log.step("login", url=target_url):
                page.fill(...)
        """
        try:
            yield
        except Exception as exc:  # noqa: BLE001 - we want to log and re-raise
            self.failure(action, error=str(exc), **details)
            raise
        else:
            self.success(action, **details)
