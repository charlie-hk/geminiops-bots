"""
Use case 1: "Send out reminders late afternoon for next-day meetings on
Google Calendar."

Flow:
  1. Read tomorrow's events from a Google Calendar via the Calendar API.
  2. Ask Gemini to turn each event into a short, friendly reminder line
     (this is the one place an LLM genuinely helps: turning a raw event
     title/time/attendee list into a message a human enjoys reading,
     instead of a robotic "Event: X at Y").
  3. Send each reminder to Telegram (swap send_reminder() for email/Slack
     if the client prefers a different channel -- it's one function).
  4. Log every event processed and every send attempt via ActivityLogger,
     success or failure, as the job post asked for.

SETUP (left for you -- see README "What you still need to supply"):
  - A Google Cloud OAuth client (credentials.json) with Calendar
    readonly scope, and a token.json produced by the first interactive run.
  - GEMINI_API_KEY (see core/llm.py).
  - TG_BOT_TOKEN / TG_CHAT_ID if using the Telegram sender (or implement
    send_reminder() for your own channel).

Run:
  python -m bots.calendar_reminder          # real run (needs the above)
  python -m bots.calendar_reminder --demo    # offline demo with fake events
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from core.llm import GeminiClient, GeminiNotConfigured
from core.logger import ActivityLogger

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_FILE = Path(os.getenv("GOOGLE_TOKEN_FILE", "token.json"))
CREDENTIALS_FILE = Path(os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))


@dataclass
class CalendarEvent:
    title: str
    start: str
    attendees: list[str]


def get_tomorrows_events() -> list[CalendarEvent]:
    """Real Google Calendar read. Requires credentials.json + token.json
    (see README). Kept separate from --demo mode so the whole pipeline is
    runnable and testable without Google credentials."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"{CREDENTIALS_FILE} not found. Download an OAuth client "
                    "(Desktop app type) from Google Cloud Console > APIs & "
                    "Services > Credentials, enable the Calendar API, and "
                    "save it as credentials.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    tz = dt.datetime.now().astimezone().tzinfo
    tomorrow = dt.datetime.now(tz).date() + dt.timedelta(days=1)
    start = dt.datetime.combine(tomorrow, dt.time.min, tzinfo=tz).isoformat()
    end = dt.datetime.combine(tomorrow, dt.time.max, tzinfo=tz).isoformat()

    events_result = service.events().list(
        calendarId="primary", timeMin=start, timeMax=end,
        singleEvents=True, orderBy="startTime",
    ).execute()

    out = []
    for e in events_result.get("items", []):
        start_time = e["start"].get("dateTime", e["start"].get("date"))
        attendees = [a.get("email", "") for a in e.get("attendees", [])]
        out.append(CalendarEvent(title=e.get("summary", "(no title)"), start=start_time, attendees=attendees))
    return out


def demo_events() -> list[CalendarEvent]:
    """Fake events so the rest of the pipeline can be demoed with no
    Google account at all."""
    tomorrow_9am = (dt.datetime.now() + dt.timedelta(days=1)).replace(hour=9, minute=0)
    return [
        CalendarEvent("Weekly ops sync", tomorrow_9am.isoformat(), ["dispatch@example.com"]),
        CalendarEvent("Client QA review", (tomorrow_9am + dt.timedelta(hours=3)).isoformat(), ["qa-lead@example.com"]),
    ]


def draft_reminder(event: CalendarEvent, llm: GeminiClient) -> str:
    prompt = (
        f"Write a short, friendly Slack/Telegram-style reminder (max 2 "
        f"sentences, no emoji spam) for this meeting:\n"
        f"Title: {event.title}\nStart: {event.start}\nAttendees: {', '.join(event.attendees) or 'n/a'}"
    )
    try:
        return llm.generate(prompt, system="You write brief, friendly meeting reminders.")
    except GeminiNotConfigured:
        # Deterministic fallback so the bot still runs end-to-end without a key.
        return f"Reminder: \"{event.title}\" is scheduled for {event.start}."


def send_reminder(text: str) -> None:
    token, chat_id = os.getenv("TG_BOT_TOKEN", ""), os.getenv("TG_CHAT_ID", "")
    if not (token and chat_id):
        raise RuntimeError("TG_BOT_TOKEN / TG_CHAT_ID not set (or implement your own channel here)")
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text}, timeout=15,
    )
    r.raise_for_status()
    if not r.json().get("ok"):
        raise RuntimeError(f"Telegram rejected the message: {r.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="use fake events and print instead of sending")
    args = parser.parse_args()

    log = ActivityLogger(bot_name="calendar_reminder")
    llm = GeminiClient()

    events = demo_events() if args.demo else get_tomorrows_events()
    log.info("events_fetched", count=len(events), demo=args.demo)

    for event in events:
        with log.step("draft_reminder", title=event.title):
            text = draft_reminder(event, llm)
        if args.demo:
            print(f"  -> {text}")
            log.success("send_reminder", title=event.title, channel="stdout-demo")
            continue
        with log.step("send_reminder", title=event.title, channel="telegram"):
            send_reminder(text)


if __name__ == "__main__":
    main()
