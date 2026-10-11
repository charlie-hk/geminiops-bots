# GeminiOps Bots

![GeminiOps Bots cover](assets/cover.png?v=9882a9a)

A small, modular framework for three recurring ops-automation jobs, built
around Google's Gemini API:

1. **Calendar reminders** — reads tomorrow's Google Calendar events and
   sends a friendly reminder (Telegram by default) for each one.
2. **Modular data retrieval** — logs into a web system and pulls structured
   rows back out, through a pluggable *Adapter* so a new target system is
   "write one small file", not "rewrite the bot."
3. **Test runner / QA bot** — runs a list of functional checks against a
   web app, and asks Gemini to turn any failure into a plain-English
   explanation a non-technical client can read.

Every bot writes structured success/failure logs through one shared
`ActivityLogger` (see `core/logger.py`), and `reports/build_report.py`
turns those logs into a single static HTML page — the "record activity
and report on successes and failed attempts" requirement, in a form you
can just open in a browser.

This repo is a portfolio/demo build, modeled on a real automation brief
(three Gemini-bot use cases: calendar reminders, modular system login +
data retrieval, and functional testing with activity reporting). It is
**not** connected to any real client system — the data-retrieval and
test-runner bots ship with a working demo adapter against a public,
scraping-friendly practice site (the-internet.herokuapp.com), so you can
run the whole pipeline immediately with no credentials.

## Quick start (no credentials needed)

```bash
pip install -r requirements.txt
playwright install chromium

python -m bots.calendar_reminder --demo        # fake events, prints reminders
python -m bots.data_retrieval --adapter demo    # real browser run, public demo site
python -m bots.test_runner                      # 5 functional checks, public demo site

python reports/build_report.py                  # -> reports/report.html
```

Run the test suite:

```bash
pytest
```

## Architecture

```
core/
  llm.py      - one Gemini wrapper every bot calls through (swap models in one place)
  logger.py   - ActivityLogger: structured success/failure logging, shared by all bots
bots/
  calendar_reminder.py   - use case 1
  data_retrieval.py      - use case 2 (generic driver)
  test_runner.py         - use case 3
  adapters/
    demo_site.py                  - COMPLETE adapter, runs out of the box
    client_system_template.py     - EMPTY template, see "What you still need to supply"
  checks.json - the test_runner's check list (edit/replace per client)
reports/
  build_report.py  - turns reports/logs/*.jsonl into reports/report.html
```

## What you still need to supply

This framework is deliberately left unfinished in a few specific places —
the parts that genuinely depend on a real client and can't be guessed at
from a job post:

- **`GEMINI_API_KEY`** — get one at https://aistudio.google.com/apikey and
  `export GEMINI_API_KEY=...`. Every bot falls back to a non-AI default
  when it's unset, so the pipeline still runs without it.
- **Google Calendar OAuth** — a `credentials.json` (OAuth client, Desktop
  app type) from Google Cloud Console with the Calendar API enabled. The
  first run opens a browser to authorize and saves `token.json`.
- **`TG_BOT_TOKEN` / `TG_CHAT_ID`** (or swap `send_reminder()` in
  `calendar_reminder.py` for email/Slack/whatever channel the client wants).
- **The real client adapter** — copy
  `bots/adapters/client_system_template.py`, fill in the real login URL,
  field selectors and data screen once you can see the client's actual
  system (credentials, 2FA, odd markup, and rate limits all vary per
  client — see the checklist at the top of that file). Confirm automated
  login is permitted by the client/site's terms before pointing this at a
  production system.
- **`bots/checks.json`** for the real system under test, once you know
  what "working correctly" means for that client's test fleets/buyers.

## Design notes worth mentioning in a proposal

- Every bot shares one logger and one LLM client, so adding a fourth bot
  (a new use case) means writing the bot, not re-plumbing logging or model
  calls.
- The Adapter pattern in `bots/adapters/` is the actual mechanism behind
  "modular … use the same bot for other systems" — not just a design
  buzzword in the pitch.
- `core/llm.py` isolates the Gemini SDK in one file; switching models, or
  adding a second provider as a fallback, is a one-file change.
- Every bot degrades gracefully without its optional credentials (Gemini
  key, Telegram token) so a reviewer can run the whole thing immediately.
