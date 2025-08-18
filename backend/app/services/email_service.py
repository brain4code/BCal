from typing import Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from ..core.config import settings
from ..models.user import User
from ..models.booking import Booking
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.fastmail = None
        if settings.email_enabled:
            self._setup_email()
    
    def _setup_email(self):
        """Setup email configuration"""
        try:
            conf = ConnectionConfig(
                MAIL_USERNAME=settings.email_username,
                MAIL_PASSWORD=settings.email_password,
                MAIL_FROM=settings.email_from,
                MAIL_PORT=settings.email_port,
                MAIL_SERVER=settings.email_host,
                MAIL_TLS=settings.email_use_tls,
                MAIL_SSL=False,
                USE_CREDENTIALS=True
            )
            self.fastmail = FastMail(conf)
        except Exception as e:
            logger.error(f"Failed to setup email service: {e}")
    
    async def send_booking_confirmation(self, booking: Booking, host: User, guest: User):
        """Send booking confirmation email to guest"""
        if not self.fastmail:
            return
        
        try:
            message = MessageSchema(
                subject=f"Booking Confirmed: {booking.title}",
                recipients=[guest.email],
                body=self._get_booking_confirmation_template(booking, host, guest),
                subtype="html"
            )
            await self.fastmail.send_message(message)
            logger.info(f"Booking confirmation sent to {guest.email}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation: {e}")
    
    async def send_booking_reminder(self, booking: Booking, host: User, guest: User):
        """Send booking reminder email"""
        if not self.fastmail:
            return
        
        try:
            message = MessageSchema(
                subject=f"Reminder: {booking.title}",
                recipients=[guest.email],
                body=self._get_booking_reminder_template(booking, host, guest),
                subtype="html"
            )
            await self.fastmail.send_message(message)
            logger.info(f"Booking reminder sent to {guest.email}")
        except Exception as e:
            logger.error(f"Failed to send booking reminder: {e}")
    
    async def send_booking_cancellation(self, booking: Booking, host: User, guest: User):
        """Send booking cancellation email"""
        if not self.fastmail:
            return
        
        try:
            message = MessageSchema(
                subject=f"Booking Cancelled: {booking.title}",
                recipients=[guest.email],
                body=self._get_booking_cancellation_template(booking, host, guest),
                subtype="html"
            )
            await self.fastmail.send_message(message)
            logger.info(f"Booking cancellation sent to {guest.email}")
        except Exception as e:
            logger.error(f"Failed to send booking cancellation: {e}")
    
    async def send_host_notification(self, booking: Booking, host: User, guest: User):
        """Send notification to host about new booking"""
        if not self.fastmail:
            return
        
        try:
            message = MessageSchema(
                subject=f"New Booking: {booking.title}",
                recipients=[host.email],
                body=self._get_host_notification_template(booking, host, guest),
                subtype="html"
            )
            await self.fastmail.send_message(message)
            logger.info(f"Host notification sent to {host.email}")
        except Exception as e:
            logger.error(f"Failed to send host notification: {e}")
    
    def _get_booking_confirmation_template(self, booking: Booking, host: User, guest: User) -> str:
        """Generate booking confirmation email template"""
        return f"""
        <html>
            <body>
                <h2>Booking Confirmed!</h2>
                <p>Hello {guest.full_name},</p>
                <p>Your booking with {host.full_name} has been confirmed.</p>
                <h3>Meeting Details:</h3>
                <ul>
                    <li><strong>Title:</strong> {booking.title}</li>
                    <li><strong>Date:</strong> {booking.start_time.strftime('%B %d, %Y')}</li>
                    <li><strong>Time:</strong> {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</li>
                    <li><strong>Host:</strong> {host.full_name}</li>
                </ul>
                {f'<p><strong>Description:</strong> {booking.description}</p>' if booking.description else ''}
                {f'<p><strong>Meeting URL:</strong> <a href="{booking.meeting_url}">{booking.meeting_url}</a></p>' if booking.meeting_url else ''}
                <p>Thank you for using BCal!</p>
            </body>
        </html>
        """
    
    def _get_booking_reminder_template(self, booking: Booking, host: User, guest: User) -> str:
        """Generate booking reminder email template"""
        return f"""
        <html>
            <body>
                <h2>Meeting Reminder</h2>
                <p>Hello {guest.full_name},</p>
                <p>This is a reminder about your upcoming meeting with {host.full_name}.</p>
                <h3>Meeting Details:</h3>
                <ul>
                    <li><strong>Title:</strong> {booking.title}</li>
                    <li><strong>Date:</strong> {booking.start_time.strftime('%B %d, %Y')}</li>
                    <li><strong>Time:</strong> {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</li>
                </ul>
                {f'<p><strong>Meeting URL:</strong> <a href="{booking.meeting_url}">{booking.meeting_url}</a></p>' if booking.meeting_url else ''}
                <p>See you soon!</p>
            </body>
        </html>
        """
    
    def _get_booking_cancellation_template(self, booking: Booking, host: User, guest: User) -> str:
        """Generate booking cancellation email template"""
        return f"""
        <html>
            <body>
                <h2>Booking Cancelled</h2>
                <p>Hello {guest.full_name},</p>
                <p>Your booking with {host.full_name} has been cancelled.</p>
                <h3>Cancelled Meeting:</h3>
                <ul>
                    <li><strong>Title:</strong> {booking.title}</li>
                    <li><strong>Date:</strong> {booking.start_time.strftime('%B %d, %Y')}</li>
                    <li><strong>Time:</strong> {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</li>
                </ul>
                <p>If you have any questions, please contact {host.full_name}.</p>
            </body>
        </html>
        """
    
    def _get_host_notification_template(self, booking: Booking, host: User, guest: User) -> str:
        """Generate host notification email template"""
        return f"""
        <html>
            <body>
                <h2>New Booking Received</h2>
                <p>Hello {host.full_name},</p>
                <p>You have received a new booking request.</p>
                <h3>Booking Details:</h3>
                <ul>
                    <li><strong>Title:</strong> {booking.title}</li>
                    <li><strong>Guest:</strong> {guest.full_name} ({guest.email})</li>
                    <li><strong>Date:</strong> {booking.start_time.strftime('%B %d, %Y')}</li>
                    <li><strong>Time:</strong> {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}</li>
                </ul>
                {f'<p><strong>Description:</strong> {booking.description}</p>' if booking.description else ''}
                <p>Please log in to your dashboard to manage this booking.</p>
            </body>
        </html>
        """


email_service = EmailService()
