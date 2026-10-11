"""
A COMPLETE, working adapter -- run as-is, no credentials needed.

Target: https://the-internet.herokuapp.com/login
  (a public QA-practice site built for exactly this purpose: safe to
  automate, stable markup, no ToS issue -- unlike scraping a real
  production platform without permission.)

Login:  username = tomsmith   password = SuperSecretPassword!
After login it shows a "You logged into a secure area!" page with a
small table-like list of links we read back as rows, standing in for
"retrieve load data" in the real job.
"""
from __future__ import annotations

from typing import Any

from . import SystemAdapter

LOGIN_URL = "https://the-internet.herokuapp.com/login"
DEMO_USERNAME = "tomsmith"
DEMO_PASSWORD = "SuperSecretPassword!"


class DemoSiteAdapter(SystemAdapter):
    name = "demo-site"

    def login(self, page: Any) -> None:
        page.goto(LOGIN_URL)
        page.fill("#username", DEMO_USERNAME)
        page.fill("#password", DEMO_PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_selector("#flash")  # success/failure banner
        flash_text = page.inner_text("#flash")
        if "You logged into a secure area" not in flash_text:
            raise RuntimeError(f"login did not succeed: {flash_text.strip()!r}")

    def fetch_rows(self, page: Any) -> list[dict[str, Any]]:
        # The secure page itself has no data table, so we also visit the
        # site's public "elements" demo pages and read their link text as
        # stand-in "load" rows -- enough to prove the fetch -> clean-rows
        # step end to end without needing a real data-bearing site.
        page.goto("https://the-internet.herokuapp.com/")
        links = page.locator("ul li a")
        count = links.count()
        rows: list[dict[str, Any]] = []
        for i in range(count):
            rows.append({
                "row_id": i + 1,
                "label": links.nth(i).inner_text().strip(),
                "href": links.nth(i).get_attribute("href"),
            })
        return rows
