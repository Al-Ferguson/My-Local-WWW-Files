''' Use https://www.MKEjazz.live/shows.json to create an vCalendar format 
    subscription file for Apple & Google Calendar subscriptions.

    Note: This version uses the icalendar module to create the vCalendar format file. 
    Note: Run this locally via http://lyceum.local/~aferguson/cgi-bin/MkeJazzLive.wsgi
'''

# region Author & Version
__author__: str = "Al Ferguson"
__email__: str = "aferguson@neptunescove.org"
__updated__ = "2026-10-25 23:40:08"
__version__: str = "0.1.4"
# endregion Author & Version

# region Imports
# Script Dependencies:
#   - requests
#   - csv
#   - json
#   - typing

import datetime as dt
from zoneinfo import ZoneInfo as zi

import httpx as rq
from icalendar import Calendar as cal
from icalendar import Event as ev

# endregion Imports

# region Functions

def generate_event(thisEvent: dict) -> ev:
    ''' Generate an iCal event from a MKE Jazz Live event. -- Customize here '''
    if thisEvent['endTime'] is None:
        end_time: str = '23:59:59'
    else:
        end_time = thisEvent['endTime']   
    return ev.new(
        summary=thisEvent['artist'],
        description=f"{thisEvent['price']!s}\n\n{thisEvent['note']!s}\n\nAdded by: {thisEvent['source']!s}",
        location=f"{thisEvent['venue']!s}\n{thisEvent['address']!s}",
        start=dt.datetime.fromisoformat(f"{thisEvent['date']!s}T{thisEvent['time']!s}").astimezone(tz),
        end=dt.datetime.fromisoformat(f"{thisEvent['date']!s}T{end_time}").astimezone(tz),
        organizer=f"{thisEvent['source']!s}",
        url=thisEvent['ticketUrl']
    )


def build_calendar(thisCal: cal, events: tuple[dict]) -> cal:
    ''' Build an iCal calendar from the passed events. '''
    for event in events:
        thisCal.add_component(generate_event(event)) 
    return thisCal
    
# endregion Functions

# region Global Variables -- Customize here

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
SHOWS: tuple[dict] = tuple(rq.get(EVENTS_URL).json()['shows'])

new_iCal: cal = cal.new(
    calscale="GREGORIAN",
    color="silver",
    description="MKE Jazz Live Events",
    language="EN",
    method="PUBLISH",
    name="MKE Jazz Live Calendar",
    organization="MKE Jazz Live",
    source="https://www.MKEjazz.live",
    version="2.0"
    )

tz = zi("America/Chicago")

# endregion Global Variables

def main() -> None:
    ''' Main entry point for the script when called directly. '''
    print(build_calendar(new_iCal, SHOWS).to_ical().decode())

def application(environ, start_fn):
    ''' Main Entry Point for WSGI application for Publishing an iCal calendar. '''
    start_fn('200 OK', 
             [('Content-Type', 'text/calendar'),
              ('Cache-Control', 'no-cache, must-revalidate')])
    yield build_calendar(new_iCal, SHOWS).to_ical()


if __name__ == "__main__":
    main()
