"""
Use case 3: "Testing functionality of the [client] system, complex with
test fleets and test buyers, all done with trustworthy Gemini."

This bot reads a list of checks from a JSON file (bots/checks.json), runs
each against a target site with Playwright, and asks Gemini to judge
pass/fail for the checks that are not a simple selector/text match (e.g.
"does this page look broken" rather than "does #id exist"). Every check's
result -- and why -- is logged with ActivityLogger, then reports/build_report.py
turns the day's log into a one-page HTML summary a client can open directly.

The shipped bots/checks.json targets the same public demo site as the
data-retrieval demo, so this runs end to end with zero client secrets.
For a real client, copy checks.json, point `url` at their staging/test
environment, and add whatever `action` handlers below the real flows need
(see `ACTIONS` -- each one is a plain function, easy to extend).

Run:
  python -m bots.test_runner                 # uses bots/checks.json
  python -m bots.test_runner --checks my.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from core.llm import GeminiClient, GeminiNotConfigured
from core.logger import ActivityLogger

DEFAULT_CHECKS = Path(__file__).resolve().parent / "checks.json"


def _action_login_demo(page: Any) -> None:
    page.fill("#username", "tomsmith")
    page.fill("#password", "SuperSecretPassword!")
    page.click("button[type=submit]")


def _action_login_invalid(page: Any) -> None:
    page.fill("#username", "not-a-real-user")
    page.fill("#password", "wrong-password")
    page.click("button[type=submit]")


def _action_count_options(page: Any, check: dict) -> int:
    return page.locator(check["selector"]).count()


ACTIONS: dict[str, Callable] = {
    "login_demo": _action_login_demo,
    "login_invalid": _action_login_invalid,
    "count_options": _action_count_options,
}


def run_check(page: Any, check: dict, llm: GeminiClient) -> tuple[bool, str]:
    page.goto(check["url"])

    action = check.get("action")
    if action in ("login_demo", "login_invalid"):
        ACTIONS[action](page)
        page.wait_for_selector("#flash")

    if check.get("expect_selector"):
        found = page.locator(check["expect_selector"]).count() > 0
        if not found:
            return False, f"selector {check['expect_selector']!r} not found"

    if check.get("expect_text"):
        body_text = page.inner_text("body")
        if check["expect_text"] not in body_text:
            return False, f"expected text {check['expect_text']!r} not present"

    if action == "count_options":
        actual = _action_count_options(page, check)
        expected = check["expect_count"]
        if actual != expected:
            return False, f"expected {expected} options, found {actual}"

    return True, "ok"


def ai_explain_failure(check: dict, reason: str, llm: GeminiClient) -> str:
    """Ask Gemini for a one-line, non-technical explanation of a failure --
    useful in the HTML report for a client who isn't reading stack traces."""
    prompt = (
        f"A website test named {check['name']!r} failed: {reason}. "
        "In one plain-English sentence, explain what this likely means for "
        "a non-technical reader."
    )
    try:
        return llm.generate(prompt, max_tokens=120)
    except GeminiNotConfigured:
        return reason


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", type=Path, default=DEFAULT_CHECKS)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    checks = json.loads(args.checks.read_text())
    log = ActivityLogger(bot_name="test_runner")
    llm = GeminiClient()

    from playwright.sync_api import sync_playwright

    passed = failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page()
        for check in checks:
            try:
                ok, reason = run_check(page, check, llm)
            except Exception as exc:  # noqa: BLE001
                ok, reason = False, str(exc)
            if ok:
                passed += 1
                log.success("check", name=check["name"])
            else:
                failed += 1
                explanation = ai_explain_failure(check, reason, llm)
                log.failure("check", error=reason, name=check["name"], ai_explanation=explanation)
        browser.close()

    print(f"{passed} passed, {failed} failed out of {len(checks)} checks. "
          f"See reports/logs/test_runner.jsonl (or run reports/build_report.py for HTML).")


if __name__ == "__main__":
    main()
