from datetime import datetime, timedelta
from typing import Optional
from icalendar import Calendar, Event
from ..models.booking import Booking
from ..models.user import User


class CalendarService:
    @staticmethod
    def generate_ics_invite(
        booking: Booking,
        host: User,
        guest: User,
        description: Optional[str] = None
    ) -> str:
        """
        Generate an ICS calendar invite for a booking.
        """
        cal = Calendar()
        cal.add('prodid', '-//BCal//Calendar Booking//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')

        event = Event()
        event.add('summary', booking.title)
        event.add('dtstart', booking.start_time)
        event.add('dtend', booking.end_time)
        event.add('dtstamp', datetime.utcnow())
        event.add('uid', f'bcal-booking-{booking.id}@bcal.com')
        event.add('organizer', f'mailto:{host.email}')
        event.add('attendee', f'mailto:{guest.email}')
        
        # Add description
        if description:
            event.add('description', description)
        elif booking.description:
            event.add('description', booking.description)
        else:
            event.add('description', f'Meeting with {host.full_name}')

        # Add location if available
        if hasattr(booking, 'meeting_location') and booking.meeting_location:
            event.add('location', booking.meeting_location)
        elif hasattr(booking, 'meeting_url') and booking.meeting_url:
            event.add('location', booking.meeting_url)

        # Add alarm/reminder (15 minutes before)
        alarm = Event()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'Reminder: {booking.title}')
        alarm.add('trigger', timedelta(minutes=-15))
        event.add_component(alarm)

        cal.add_component(event)
        return cal.to_ical().decode('utf-8')

    @staticmethod
    def generate_cancel_ics(
        booking: Booking,
        host: User,
        guest: User
    ) -> str:
        """
        Generate an ICS calendar cancellation.
        """
        cal = Calendar()
        cal.add('prodid', '-//BCal//Calendar Booking//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'CANCEL')

        event = Event()
        event.add('summary', f'CANCELLED: {booking.title}')
        event.add('dtstart', booking.start_time)
        event.add('dtend', booking.end_time)
        event.add('dtstamp', datetime.utcnow())
        event.add('uid', f'bcal-booking-{booking.id}@bcal.com')
        event.add('organizer', f'mailto:{host.email}')
        event.add('attendee', f'mailto:{guest.email}')
        event.add('status', 'CANCELLED')

        cal.add_component(event)
        return cal.to_ical().decode('utf-8')

    @staticmethod
    def generate_update_ics(
        booking: Booking,
        host: User,
        guest: User,
        old_start_time: datetime,
        old_end_time: datetime
    ) -> str:
        """
        Generate an ICS calendar update.
        """
        cal = Calendar()
        cal.add('prodid', '-//BCal//Calendar Booking//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')

        event = Event()
        event.add('summary', f'UPDATED: {booking.title}')
        event.add('dtstart', booking.start_time)
        event.add('dtend', booking.end_time)
        event.add('dtstamp', datetime.utcnow())
        event.add('uid', f'bcal-booking-{booking.id}@bcal.com')
        event.add('organizer', f'mailto:{host.email}')
        event.add('attendee', f'mailto:{guest.email}')
        event.add('description', f'Meeting time updated from {old_start_time.strftime("%Y-%m-%d %H:%M")} to {booking.start_time.strftime("%Y-%m-%d %H:%M")}')

        cal.add_component(event)
        return cal.to_ical().decode('utf-8')
