''' Use https://www.MKEjazz.live/shows.json to create an iCal format 
    subscription file for Apple & Google Calendar subscriptions.
'''

# region Author & Version
__author__: str = "Al Ferguson"
__email__: str = "aferguson@neptunescove.org"
__updated__ = "2026-10-24 06:26:08"
__version__: str = "0.1.1"
# endregion Author & Version

# region Imports
# Script Dependencies:
#   - requests
#   - csv
#   - json
#   - typing

import datetime as dt

import httpx as rq
import ical.calendar as cal
import ical.event as ev
import ical.timezone as tz
from ical.calendar_stream import IcsCalendarStream as cs

# endregion Imports

# region Functions

def generate_event(events: dict) -> ev.Event:
    ''' Generate an iCal event from a MKE Jazz Live event. '''
    now: dt.datetime = dt.datetime.now(tz=None)
    date: str = str(dt.date.fromisoformat(events['date']))
    if events['endTime'] is None:
        end_time: str = '23:59:59'
    else:
        end_time = events['endTime']
    
    return ev.Event(
        uid=f"{now!s}@MKEJazzLive.wsgi",
        dtstamp=now,
        dtstart=dt.datetime.fromisoformat(f"{date}T{events['time']!s}"),
        dtend=dt.datetime.fromisoformat(f"{date}T{end_time}"),
        summary=events['artist'],
        description=f"{events['price']!s}\n\n{events['note']!s}\n\nEntered by: {events['source']!s}",
        location=f"{events['venue']!s}\n{events['address']!s}",
        url=events['ticketUrl']
    )

def build_calendar() -> cal.Calendar:
    ''' Build an iCal calendar from MKE Jazz Live events. '''
    for show in SHOWS:
        MKE_JAZZ_LIVE_CAL.events.append(generate_event(show))
    return MKE_JAZZ_LIVE_CAL
    
# endregion Functions

# region Global Variables

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
SHOWS: tuple[dict] = tuple(rq.get(EVENTS_URL).json()['shows'])

MKE_JAZZ_LIVE_CAL: cal.Calendar = cal.Calendar(
    calscale="GREGORIAN",
    color="#C2407F",
    description=["MKE Jazz Live event Calendar"],
    method="PUBLISH",
    name=["MKE Jazz Live"],
    prodid="-//MKE Jazz Live Event ICS Exporter//EN",
    version="2.0",
    vtimezone=[tz.Timezone.from_tzif("America/Chicago")]
    )

# endregion Global Variables

def main() -> None:
    ''' Main entry point for the script when called directly. '''
    print(cs.calendar_to_ics(build_calendar()))

def application(environ, start_fn):
    ''' Main Entry Point for WSGI application for Publishing an iCal calendar. '''
    start_fn('200 OK', 
             [('Content-Type', 'text/calendar'),
              ('Cache-Control', 'no-cache, must-revalidate')])
    yield cs.calendar_to_ics(build_calendar()).encode("utf-8")


if __name__ == "__main__":
    main()
