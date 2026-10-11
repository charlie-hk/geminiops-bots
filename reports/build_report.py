"""
Turn reports/logs/*.jsonl into one static reports/report.html page --
the "report on successes and failed attempts" deliverable, in a form a
non-technical client can open directly in a browser with no server, no
login, no dependencies beyond the file itself.

Run after any bot (or after several):
  python reports/build_report.py
"""
from __future__ import annotations

import json
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
OUT_FILE = Path(__file__).resolve().parent / "report.html"

ROW_TMPL = """<tr class="{cls}">
  <td>{ts}</td><td>{bot}</td><td>{status}</td><td>{action}</td><td>{detail}</td>
</tr>"""

PAGE_TMPL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>GeminiOps Bot Activity Report</title>
<style>
  body {{ font: 14px/1.4 -apple-system, Segoe UI, sans-serif; margin: 2rem; color: #1a1a1a; background: #fafafa; }}
  h1 {{ font-size: 1.3rem; }}
  .summary {{ display: flex; gap: 1.5rem; margin: 1rem 0 2rem; }}
  .card {{ background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; padding: .75rem 1.25rem; }}
  .card b {{ font-size: 1.4rem; display: block; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff; }}
  th, td {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #eee; font-size: 13px; }}
  th {{ background: #f0f0f0; }}
  tr.success td:nth-child(3) {{ color: #137333; font-weight: 600; }}
  tr.failure td:nth-child(3) {{ color: #c5221f; font-weight: 600; }}
  tr.info td:nth-child(3) {{ color: #666; }}
</style></head>
<body>
  <h1>GeminiOps Bot Activity Report</h1>
  <div class="summary">
    <div class="card"><b>{total}</b>total events</div>
    <div class="card"><b>{succ}</b>successes</div>
    <div class="card"><b>{fail}</b>failures</div>
  </div>
  <table>
    <thead><tr><th>Time</th><th>Bot</th><th>Status</th><th>Action</th><th>Detail</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body></html>"""


def load_records() -> list[dict]:
    records = []
    for path in sorted(LOG_DIR.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                records.append(json.loads(line))
    records.sort(key=lambda r: r.get("ts", ""))
    return records


def detail_of(r: dict) -> str:
    if r.get("status") == "failure":
        base = r.get("error", "")
        ai = (r.get("details") or {}).get("ai_explanation")
        return f"{base} — {ai}" if ai else base
    d = r.get("details") or {}
    return ", ".join(f"{k}={v}" for k, v in d.items())


def main() -> None:
    records = load_records()
    rows_html = "\n".join(
        ROW_TMPL.format(
            cls=r.get("status", "info"), ts=r.get("ts", ""), bot=r.get("bot", ""),
            status=r.get("status", ""), action=r.get("action", ""), detail=detail_of(r),
        )
        for r in records
    )
    succ = sum(1 for r in records if r.get("status") == "success")
    fail = sum(1 for r in records if r.get("status") == "failure")
    OUT_FILE.write_text(PAGE_TMPL.format(total=len(records), succ=succ, fail=fail, rows=rows_html or "<tr><td colspan=5>No runs logged yet — run a bot first.</td></tr>"))
    print(f"Wrote {OUT_FILE} ({len(records)} events, {succ} success, {fail} failure)")


if __name__ == "__main__":
    main()
