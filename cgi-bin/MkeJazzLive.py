# Copyright (c) 2026 Al Ferguson    # noqa: N999
"""Use JSON to create vCalendar for Apple & Google Calendar subscriptions.

Customize the "-- Customize here --" sections to your needs

NOTE: This uses the iCalendar module to create the vCalendar format file.
NOTE: I Run this via http://lyceum.local/~aferguson/cgi-bin/MkeJazzLive.wsgi
"""

# region Author
__author__: str = "Al Ferguson"
__created__: str = "2026-10-24 14:15:00"
__updated__: str = "2026-10-31 22:40:00"
__version__: str = "0.1.7"
# endregion Author

# region Imports
# Script Dependencies:

import datetime as dt
from zoneinfo import ZoneInfo

import httpx as rq
from icalendar import Calendar, Event

# endregion Imports

# region Functions

def generate_event(event: dict) -> Event:
    """Generate an event from event. -- Customize here -- MKE Jazz Live."""
    endtime = "23:59:59" if event["endTime"] is None else event["endTime"]
    return Event.new(
        summary=event["artist"],
        description=f"{event["price"]}\n\n{event["note"]}\n\nAdded by: {event["source"]}",  # noqa: E501
        location=f"{event["venue"]}\n{event["address"]}",
        start=dt.datetime.fromisoformat(f"{event["date"]!s}T{event["time"]!s}").astimezone(EVENTTZ),
        end=dt.datetime.fromisoformat(f"{event["date"]!s}T{endtime}").astimezone(EVENTTZ),
        organizer=f"{event["source"]}",
        url=event["ticketUrl"],
    )

def build_calendar() -> Calendar:
    """Add Events to iCalendar events. -- Customize here -- MKE Jazz Live."""
    shows: tuple[dict] = tuple(rq.get(EVENTS_URL).json()["shows"])
    calendar: Calendar = Calendar.new(
        calscale="GREGORIAN",
        color="silver",
        description="MKE Jazz Live Events",
        language="EN",
        method="PUBLISH",
        name="MKE Jazz Live Calendar",
        organization="MKE Jazz Live",
        source="https://www.MKEjazz.live",
        version="2.0",
        )
    for event in shows:
        calendar.add_component(generate_event(event))
    return calendar

# endregion Functions

# region Global Variables -- Customize here -- MKE Jazz Live

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
EVENTTZ = ZoneInfo("America/Chicago")

# endregion Global Variables

def main() -> None:
    """Entry point for testing when script is run directly."""
    print(build_calendar().to_ical().decode())  # noqa: T201

def app(environ: dict, start_fn: callable) -> bytes:  # noqa: ARG001
    """Entry Point for publishing a VCalendar when accessed via WSGI."""
    start_fn("200 OK", [("Content-Type", "text/calendar"),
                        ("Cache-Control", "no-cache, must-revalidate")])
    yield build_calendar().to_ical()

if __name__ == "__main__":
    main()
