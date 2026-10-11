"""
Use case 2: "Log into a [transportation management] system and retrieve
load data; this needs to be modular so we can use some of the same bot for
other systems."

This file is the modular driver: it knows nothing about any specific
website. It takes an Adapter (see bots/adapters/), drives a headless
browser through login() and fetch_rows(), saves the rows, and logs every
step. Pointing this bot at a new system is "write a new Adapter", never
"rewrite this file" -- that is the actual requirement behind the word
"modular" in the job post.

Run:
  python -m bots.data_retrieval --adapter demo
    -> runs against the public demo site, no credentials needed, writes
       reports/data/demo-site.json

  python -m bots.data_retrieval --adapter client
    -> runs ClientSystemAdapter (bots/adapters/client_system_template.py),
       which raises NotImplementedError until it's filled in for the real
       client system (see that file's docstring -- left for you on purpose).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.logger import ActivityLogger
from bots.adapters import SystemAdapter
from bots.adapters.demo_site import DemoSiteAdapter

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "data"

ADAPTERS: dict[str, type[SystemAdapter]] = {"demo": DemoSiteAdapter}
try:
    from bots.adapters.client_system_template import ClientSystemAdapter
    ADAPTERS["client"] = ClientSystemAdapter
except ImportError:
    pass


def run(adapter_key: str, headless: bool = True) -> list[dict]:
    from playwright.sync_api import sync_playwright

    adapter_cls = ADAPTERS[adapter_key]
    adapter = adapter_cls()
    log = ActivityLogger(bot_name="data_retrieval")
    log.info("run_started", adapter=adapter.name)

    rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            with log.step("login", adapter=adapter.name):
                adapter.login(page)
            with log.step("fetch_rows", adapter=adapter.name):
                rows = adapter.fetch_rows(page)
            log.success("rows_retrieved", adapter=adapter.name, count=len(rows))
            with log.step("logout", adapter=adapter.name):
                adapter.logout(page)
        finally:
            browser.close()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{adapter.name}.json"
    out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    log.info("rows_saved", path=str(out_path))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", choices=sorted(ADAPTERS), default="demo")
    parser.add_argument("--headed", action="store_true", help="show the browser window (debugging)")
    args = parser.parse_args()
    rows = run(args.adapter, headless=not args.headed)
    print(f"Retrieved {len(rows)} row(s). See reports/data/{ADAPTERS[args.adapter]().name}.json")


if __name__ == "__main__":
    main()
