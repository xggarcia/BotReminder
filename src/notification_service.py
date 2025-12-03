"""
Multi-channel notification service supporting Email and Telegram.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import asyncio

from .config import (
    ENABLE_EMAIL, ENABLE_TELEGRAM,
    EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)
from .utils.logger import setup_logger

logger = setup_logger('notifications')


class NotificationService:
    """Handles sending notifications via multiple channels."""
    
    def __init__(self):
        self.email_enabled = ENABLE_EMAIL
        self.telegram_enabled = ENABLE_TELEGRAM
        
        # Initialize Telegram bot if enabled
        if self.telegram_enabled:
            try:
                self.telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
                logger.info("Telegram bot initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.telegram_enabled = False
    
    def send_reminder(self, event, reminder_message, natural_summary):
        """
        Send a reminder notification about an event.
        
        Args:
            event: Event dictionary
            reminder_message: AI-generated reminder message
            natural_summary: AI-generated event summary
        """
        success = False
        
        # Format the notification content
        subject, body = self._format_notification(event, reminder_message, natural_summary)
        
        # Send via enabled channels
        if self.email_enabled:
            if self._send_email(subject, body):
                success = True
                logger.info(f"Email sent for: {event['summary']}")
        
        if self.telegram_enabled:
            if self._send_telegram(body):
                success = True
                logger.info(f"Telegram message sent for: {event['summary']}")
        
        if not success:
            logger.warning(f"Failed to send reminder for: {event['summary']}")
        
        return success
    
    def _format_notification(self, event, reminder_message, natural_summary):
        """Format notification content."""
        time_str = event['start_time'].strftime('%A, %B %d at %I:%M %p')
        
        subject = f"🔔 Reminder: {event['summary']}"
        
        body = f"""
{reminder_message}

📅 Event: {event['summary']}
📝 Summary: {natural_summary}
🕒 Time: {time_str}
"""
        
        if event['location']:
            body += f"📍 Location: {event['location']}\n"
        
        if event['duration_minutes'] > 0:
            hours = event['duration_minutes'] // 60
            minutes = event['duration_minutes'] % 60
            duration_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            body += f"⏱️ Duration: {duration_str}\n"
        
        if event['attendee_count'] > 0:
            body += f"👥 Attendees: {event['attendee_count']}\n"
        
        if event['description']:
            body += f"\n📋 Description:\n{event['description'][:200]}\n"
        
        if event['html_link']:
            body += f"\n🔗 View in Calendar: {event['html_link']}\n"
        
        return subject, body
    
    def _send_email(self, subject, body):
        """Send email notification via SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = EMAIL_ADDRESS
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    def _send_telegram(self, message):
        """Send Telegram notification."""
        try:
            # Run async telegram send in sync context
            asyncio.run(self._send_telegram_async(message))
            return True
        except Exception as e:
            logger.error(f"Telegram sending failed: {e}")
            return False
    
    async def _send_telegram_async(self, message):
        """Async helper for sending Telegram messages."""
        try:
            await self.telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            raise
    
    def send_test_notification(self):
        """Send a test notification to verify configuration."""
        test_event = {
            'summary': 'Test Event',
            'start_time': datetime.now(),
            'location': 'Test Location',
            'duration_minutes': 60,
            'attendee_count': 2,
            'description': 'This is a test notification from your Calendar Reminder Bot.',
            'html_link': ''
        }
        
        reminder_message = "🧪 This is a test reminder!"
        natural_summary = "This is a test to verify your notification channels are working correctly."
        
        return self.send_reminder(test_event, reminder_message, natural_summary)
