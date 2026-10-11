import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_build_report_handles_empty_and_populated_logs(tmp_path, monkeypatch):
    import reports.build_report as br

    monkeypatch.setattr(br, "LOG_DIR", tmp_path)
    out_file = tmp_path / "report.html"
    monkeypatch.setattr(br, "OUT_FILE", out_file)

    # empty case
    br.main()
    assert "No runs logged yet" in out_file.read_text()

    # populated case
    (tmp_path / "bot.jsonl").write_text(
        json.dumps({"ts": "t1", "bot": "bot", "status": "success", "action": "a", "details": {}}) + "\n"
        + json.dumps({"ts": "t2", "bot": "bot", "status": "failure", "action": "b", "error": "oops", "details": {}}) + "\n"
    )
    br.main()
    html = out_file.read_text()
    assert "oops" in html
    assert ">2<" in html  # total events count
