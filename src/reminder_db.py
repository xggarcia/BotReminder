"""
Database module for tracking sent reminders.
Uses SQLite to prevent duplicate notifications.
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

from .config import DB_PATH
from .utils.logger import setup_logger

logger = setup_logger('database')


class ReminderDatabase:
    """Manages the SQLite database for tracking sent reminders."""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_database()
    
    def _init_database(self):
        """Create the database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table for tracking sent reminders
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    event_title TEXT NOT NULL,
                    event_start_time TEXT NOT NULL,
                    reminder_time TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_reminder 
                ON sent_reminders(event_id, reminder_time)
            ''')
            
            conn.commit()
            logger.info("Database initialized")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def reminder_already_sent(self, event_id, reminder_time):
        """
        Check if a reminder has already been sent for this event at this time.
        
        Args:
            event_id: Event ID from Google Calendar
            reminder_time: Datetime when the reminder should be sent
        
        Returns:
            True if reminder was already sent, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM sent_reminders
                WHERE event_id = ? AND reminder_time = ?
            ''', (event_id, reminder_time.isoformat()))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def mark_reminder_sent(self, event_id, event_title, event_start_time, reminder_time):
        """
        Mark a reminder as sent in the database.
        
        Args:
            event_id: Event ID from Google Calendar
            event_title: Event title/summary
            event_start_time: When the event starts
            reminder_time: When the reminder was scheduled for
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sent_reminders 
                (event_id, event_title, event_start_time, reminder_time, sent_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                event_id,
                event_title,
                event_start_time.isoformat(),
                reminder_time.isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.debug(f"Marked reminder as sent: {event_title} at {reminder_time}")
    
    def cleanup_old_reminders(self, days_old=30):
        """
        Remove old reminder records to keep database size manageable.
        
        Args:
            days_old: Remove records older than this many days
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            cursor.execute('''
                DELETE FROM sent_reminders
                WHERE event_start_time < ?
            ''', (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old reminder records")
    
    def get_reminder_stats(self):
        """Get statistics about sent reminders."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total reminders sent
            cursor.execute('SELECT COUNT(*) FROM sent_reminders')
            total = cursor.fetchone()[0]
            
            # Reminders in the last 7 days
            week_ago = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            week_ago = week_ago.replace(day=week_ago.day - 7)
            
            cursor.execute('''
                SELECT COUNT(*) FROM sent_reminders
                WHERE sent_at >= ?
            ''', (week_ago.isoformat(),))
            last_week = cursor.fetchone()[0]
            
            return {
                'total_reminders_sent': total,
                'reminders_last_7_days': last_week
            }
