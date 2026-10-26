''' Use web based calendar JSON to create a vCalendar for Apple & Google Calendar 
    subscriptions. Customize the "-- Customize here --" sections to your needs.

    NOTE: This version uses the iCalendar module to create the vCalendar format file. 
    NOTE: I Run this via http://lyceum.local/~aferguson/cgi-bin/MkeJazzLive.wsgi
'''

# region Author & Version
__author__: str = "Al Ferguson"
__email__: str = "aferguson@neptunescove.org"
__updated__ = "2026-10-26 12:40:00"
__version__: str = "0.1.5"
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
    ''' Generate an event from event. -- Customize here -- MKE Jazz Live '''
    if thisEvent['endTime'] is None:
        end_time: str = '23:59:59'
    else:
        end_time = thisEvent['endTime']   
    return ev.new(
        summary=thisEvent['artist'],
        description=f"{thisEvent['price']}\n\n{thisEvent['note']}\n\nAdded by: {thisEvent['source']}",
        location=f"{thisEvent['venue']}\n{thisEvent['address']}",
        start=dt.datetime.fromisoformat(f"{thisEvent['date']!s}T{thisEvent['time']!s}").astimezone(glblTZ),
        end=dt.datetime.fromisoformat(f"{thisEvent['date']!s}T{end_time}").astimezone(glblTZ),
        organizer=f"{thisEvent['source']}",
        url=thisEvent['ticketUrl']
    )

def build_calendar(thisCal: cal, events: tuple[dict]) -> cal:
    ''' Add Events to iCalendar events. '''
    for event in events:
        thisCal.add_component(generate_event(event)) 
    return thisCal
    
# endregion Functions

# region Global Variables -- Customize here -- MKE Jazz Live

EVENTS_URL: str = "https://www.MKEjazz.live/shows.json"
SHOWS: tuple[dict] = tuple(rq.get(EVENTS_URL).json()['shows'])

glblTZ = zi("America/Chicago")
newICal: cal = cal.new(
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

# endregion Global Variables

def main() -> None:
    ''' Main entry point for directly calling the script when testing. '''
    print(build_calendar(newICal, SHOWS).to_ical().decode())

def application(environ, start_fn):
    ''' Main Entry Point as WSGI application for Publishing the VCalendar. '''
    start_fn('200 OK', 
             [('Content-Type', 'text/calendar'),
              ('Cache-Control', 'no-cache, must-revalidate')])
    yield build_calendar(newICal, SHOWS).to_ical()

if __name__ == "__main__":
    main()
