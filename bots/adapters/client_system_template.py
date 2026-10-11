"""
TEMPLATE -- intentionally incomplete.

Copy this file, rename the class, and fill in the three TODOs once you can
see the real client's system in a browser: its login URL, field selectors,
and the screen that holds the data to retrieve. That step needs a human
looking at the live site (credentials, 2FA prompts, odd markup, rate
limits all vary per client) -- it is left here on purpose rather than
guessed at.

Checklist when filling this in:
  [ ] Confirm with the client that automated login is permitted
      (check their ToS / ask directly -- note this in the proposal too).
  [ ] Never hardcode real credentials in the file; read them from
      environment variables, same pattern as GEMINI_API_KEY in core/llm.py.
  [ ] Handle 2FA / CAPTCHA explicitly -- if present, this needs a
      different approach (session cookie re-use, an API if one exists,
      or a manual step) rather than brute-forcing the login form.
  [ ] Keep fetch_rows() returning plain JSON-serialisable dicts so the
      rest of the pipeline (logging, reporting) doesn't need to change.
"""
from __future__ import annotations

import os
from typing import Any

from . import SystemAdapter


class ClientSystemAdapter(SystemAdapter):
    name = "client-system"  # TODO: rename to the real system's name

    LOGIN_URL = "https://example.com/login"  # TODO: real login URL

    def login(self, page: Any) -> None:
        username = os.getenv("CLIENT_SYSTEM_USER", "")
        password = os.getenv("CLIENT_SYSTEM_PASS", "")
        if not username or not password:
            raise RuntimeError(
                "Set CLIENT_SYSTEM_USER / CLIENT_SYSTEM_PASS before running "
                "against the real system."
            )
        page.goto(self.LOGIN_URL)
        # TODO: real field selectors, e.g.:
        # page.fill("#email", username)
        # page.fill("#password", password)
        # page.click("button[type=submit]")
        raise NotImplementedError("Fill in the real login flow for this system.")

    def fetch_rows(self, page: Any) -> list[dict[str, Any]]:
        # TODO: navigate to the real data screen and extract rows, e.g.:
        # page.goto(f"{self.LOGIN_URL}/loads")
        # rows = []
        # for row in page.locator("table tbody tr").all():
        #     rows.append({...})
        # return rows
        raise NotImplementedError("Fill in the real data-retrieval step for this system.")
