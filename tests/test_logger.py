import json

from core.logger import ActivityLogger


def test_success_and_failure_are_logged(tmp_path):
    log = ActivityLogger(bot_name="unit_test", log_dir=tmp_path)
    log.success("step_a", count=3)
    try:
        with log.step("step_b"):
            raise ValueError("boom")
    except ValueError:
        pass

    lines = (tmp_path / "unit_test.jsonl").read_text().splitlines()
    records = [json.loads(line) for line in lines]

    assert records[0]["status"] == "success"
    assert records[0]["action"] == "step_a"
    assert records[0]["details"]["count"] == 3

    assert records[1]["status"] == "failure"
    assert records[1]["action"] == "step_b"
    assert "boom" in records[1]["error"]


def test_run_id_is_stable_within_one_logger_instance(tmp_path):
    log = ActivityLogger(bot_name="unit_test", log_dir=tmp_path)
    log.success("a")
    log.success("b")
    lines = (tmp_path / "unit_test.jsonl").read_text().splitlines()
    run_ids = {json.loads(line)["run_id"] for line in lines}
    assert len(run_ids) == 1
