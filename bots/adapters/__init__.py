"""
Adapter pattern for "log into system X, retrieve data, hand back clean rows."

The job this framework is modeled on needed a bot that logs into one
transportation-management system today and, soon, other systems -- without
a rewrite each time. The fix is the classic one: every system gets its own
small Adapter class that implements the same three methods; the bot that
drives them (bots/data_retrieval.py) never changes.

Two adapters ship in this repo:

- DemoSiteAdapter (adapters/demo_site.py): a COMPLETE, working adapter
  against a public, scraping-friendly demo login page
  (the-internet.herokuapp.com). Run it as-is to see the whole pipeline work
  end to end, with no credentials needed.

- ClientSystemAdapter (adapters/client_system_template.py): an EMPTY
  template with every method stubbed and a TODO. This is the one Ali fills
  in once he has the real system's URL, field names and login flow in
  front of him -- that last step always needs a human who can see the
  client's actual site, so it is left for him on purpose rather than
  guessed at here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SystemAdapter(ABC):
    """Implement this once per external system."""

    name: str = "unnamed-system"

    @abstractmethod
    def login(self, page: Any) -> None:
        """Drive a Playwright `page` through this system's login flow."""

    @abstractmethod
    def fetch_rows(self, page: Any) -> list[dict[str, Any]]:
        """After login, navigate to the data screen and return clean rows
        (one dict per row, plain JSON-serialisable values only)."""

    def logout(self, page: Any) -> None:
        """Optional: override if the system needs an explicit logout."""
        return None
