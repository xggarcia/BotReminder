"""
Scheduler for checking calendar and sending reminders.
"""

import schedule
import time
from datetime import datetime, timedelta

from .calendar_service import CalendarService
from .ai_service import AIService
from .notification_service import NotificationService
from .reminder_db import ReminderDatabase
from .utils.logger import setup_logger

logger = setup_logger('scheduler')


class ReminderScheduler:
    """Manages the reminder checking and sending schedule."""
    
    def __init__(self):
        self.calendar = CalendarService()
        self.ai = AIService()
        self.notifier = NotificationService()
        self.db = ReminderDatabase()
        
        # Track processed events to avoid re-analyzing
        self.processed_events = {}
    
    def initialize(self):
        """Initialize services (authenticate, etc.)."""
        logger.info("Initializing reminder scheduler...")
        
        # Authenticate with Google Calendar
        if not self.calendar.authenticate():
            raise RuntimeError("Failed to authenticate with Google Calendar")
        
        logger.info("Scheduler initialized successfully")
    
    def check_and_send_reminders(self):
        """
        Main job: Check calendar for upcoming events and send due reminders.
        This is called periodically by the scheduler.
        """
        try:
            logger.info("Checking for events and due reminders...")
            
            # Fetch upcoming events (next 7 days)
            events = self.calendar.get_upcoming_events(hours_ahead=168)
            
            if not events:
                logger.info("No upcoming events found")
                return
            
            now = datetime.now(events[0]['start_time'].tzinfo)
            reminders_sent = 0
            
            for event in events:
                # Check if we've already processed this event
                event_id = event['id']
                event_hash = self._get_event_hash(event)
                
                if event_id not in self.processed_events or self.processed_events[event_id] != event_hash:
                    # New or updated event - analyze it
                    logger.info(f"Analyzing event: {event['summary']}")
                    analysis = self.ai.analyze_event_and_generate_reminders(event)
                    
                    # Store the analysis
                    self.processed_events[event_id] = {
                        'hash': event_hash,
                        'analysis': analysis
                    }
                else:
                    # Use cached analysis
                    analysis = self.processed_events[event_id]['analysis']
                
                # Check if any reminders are due
                reminder_times = analysis['reminder_times']
                reminder_messages = analysis['reminder_messages']
                
                for reminder_time, reminder_msg in zip(reminder_times, reminder_messages):
                    # Check if reminder is due (within the next check interval)
                    time_until_reminder = (reminder_time - now).total_seconds()
                    
                    # Send if reminder is due (past or within next 20 minutes)
                    if time_until_reminder <= 1200:  # 20 minutes buffer
                        # Check if already sent
                        if not self.db.reminder_already_sent(event_id, reminder_time):
                            # Send the reminder
                            success = self.notifier.send_reminder(
                                event,
                                reminder_msg,
                                analysis['natural_summary']
                            )
                            
                            if success:
                                # Mark as sent
                                self.db.mark_reminder_sent(
                                    event_id,
                                    event['summary'],
                                    event['start_time'],
                                    reminder_time
                                )
                                reminders_sent += 1
            
            if reminders_sent > 0:
                logger.info(f"✅ Sent {reminders_sent} reminder(s)")
            else:
                logger.info("No reminders due at this time")
            
            # Periodic cleanup (once per check)
            self.db.cleanup_old_reminders(days_old=30)
        
        except Exception as e:
            logger.error(f"Error in reminder check: {e}", exc_info=True)
    
    def _get_event_hash(self, event):
        """Generate a hash for an event to detect changes."""
        # Simple hash based on key fields
        return f"{event['summary']}_{event['start_time']}_{event['location']}"
    
    def run(self, check_interval_minutes=15):
        """
        Start the scheduler to run periodically.
        
        Args:
            check_interval_minutes: How often to check for reminders
        """
        logger.info(f"Starting scheduler (checking every {check_interval_minutes} minutes)")
        
        # Schedule the job
        schedule.every(check_interval_minutes).minutes.do(self.check_and_send_reminders)
        
        # Run once immediately on startup
        self.check_and_send_reminders()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute if jobs are due
    
    def run_once(self):
        """Run a single check (useful for testing)."""
        logger.info("Running single reminder check...")
        self.check_and_send_reminders()
        
        # Show stats
        stats = self.db.get_reminder_stats()
        logger.info(f"Stats: {stats}")
