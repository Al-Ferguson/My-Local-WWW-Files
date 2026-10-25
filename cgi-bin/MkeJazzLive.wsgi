''' Use https://www.MKEjazz.live/shows.json to create an iCal format 
    subscription file for Apple & Google Calendar subscriptions.
'''

# region Author & Version
__author__: str = "Al Ferguson"
__email__: str = "aferguson@neptunescove.org"
__updated__ = "2026-10-24 06:26:08"
__version__: str = "0.1.2"
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

def generate_event(thisEvent: dict) -> ev.Event:
    ''' Generate an iCal event from a MKE Jazz Live event. '''
    now: dt.datetime = dt.datetime.now(tz=None)
    date: str = str(dt.date.fromisoformat(thisEvent['date']))
    if thisEvent['endTime'] is None:
        end_time: str = '23:59:59'
    else:
        end_time = thisEvent['endTime']
    
    return ev.Event(
        uid=f"{now!s}@MKEJazzLive.wsgi",
        dtstamp=now,
        dtstart=dt.datetime.fromisoformat(f"{date}T{thisEvent['time']!s}"),
        dtend=dt.datetime.fromisoformat(f"{date}T{end_time}"),
        summary=thisEvent['artist'],
        description=f"{thisEvent['price']!s}\n\n{thisEvent['note']!s}\n\nAdded by: {thisEvent['source']!s}",
        location=f"{thisEvent['venue']!s}\n{thisEvent['address']!s}",
        url=thisEvent['ticketUrl']
    )

def build_calendar(thisCal: cal.Calendar, events: tuple[dict]) -> cal.Calendar:
    ''' Build an iCal calendar from MKE Jazz Live events. '''
    for event in events:
        thisCal.events.append(generate_event(event))
    return thisCal
    
# endregion Functions

# region Global Variables

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
SHOWS: tuple[dict] = tuple(rq.get(EVENTS_URL).json()['shows'])

new_iCal: cal.Calendar = cal.Calendar(
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
    print(cs.calendar_to_ics(build_calendar(new_iCal, SHOWS)))

def application(environ, start_fn):
    ''' Main Entry Point for WSGI application for Publishing an iCal calendar. '''
    start_fn('200 OK', 
             [('Content-Type', 'text/calendar'),
              ('Cache-Control', 'no-cache, must-revalidate')])
    yield cs.calendar_to_ics(build_calendar(new_iCal, SHOWS)).encode("utf-8")


if __name__ == "__main__":
    main()
