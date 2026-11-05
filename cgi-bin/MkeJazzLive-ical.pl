''' Use https://www.MKEjazz.live/shows.json to create an iCal format 
    subscription file for Apple & Google Calendar subscriptions.
'''

# region Author & Version
__author__: str = "Al Ferguson"
__email__: str = "aferguson@neptunescove.org"
__updated__ = "2026-10-26 12:26:00"
__version__: str = "0.1.4"
# endregion Author & Version

# region Imports
# Script Dependencies:

import datetime as dt

import httpx as rq
import ical.calendar as cal
import ical.event as ev
import ical.timezone as tz
from ical.calendar_stream import IcsCalendarStream as cs

# endregion Imports

# region Functions

def generate_event(thisEvent: dict) -> ev.Event:
    ''' Generate an iCal event from a MKE Jazz Live event. -- Customize here '''
    now: dt.datetime = dt.datetime.now(tz=None)
    date: dt.date = thisEvent['date']
    endTime = '23:59:59' if thisEvent['endTime'] is None else thisEvent['endTime']
    
    return ev.Event(
        uid=f"{hash(f"{date!s}T{thisEvent['time']!s}-{thisEvent['venue']!s}")}@MKEJazzLive.wsgi",
        dtstamp=now,
        dtstart=dt.datetime.fromisoformat(f"{date!s}T{thisEvent['time']!s}"),
        dtend=dt.datetime.fromisoformat(f"{date!s}T{endTime}"),
        summary=thisEvent['artist'],
        description=f"{thisEvent['price']!s}\n\n{thisEvent['note']!s}\n\nAdded by: {thisEvent['source']!s}",
        location=f"{thisEvent['venue']!s}\n{thisEvent['address']!s}",
        url=thisEvent['ticketUrl']
    )

def build_calendar(thisICal: cal.Calendar, events: tuple[dict]) -> cal.Calendar:
    ''' Build an iCal calendar from the passed events. '''
    for event in events:
        thisICal.events.append(generate_event(event))
    return thisICal
    
# endregion Functions

# region Global Variables -- Customize here

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
SHOWS: tuple[dict] = tuple(rq.get(EVENTS_URL).json()['shows'])

newICal: cal.Calendar = cal.Calendar(
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
    print(cs.calendar_to_ics(build_calendar(newICal, SHOWS)))

def application(environ, start_fn):
    ''' Main Entry Point for WSGI application for Publishing an iCal calendar. '''
    start_fn('200 OK', 
             [('Content-Type', 'text/calendar'),
              ('Cache-Control', 'no-cache, must-revalidate')])
    yield cs.calendar_to_ics(build_calendar(newICal, SHOWS)).encode("utf-8")


if __name__ == "__main__":
    main()
