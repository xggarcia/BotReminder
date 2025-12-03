"""
Google Calendar API integration.
Handles authentication and event fetching.
"""

import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

from .config import GOOGLE_CREDENTIALS_PATH, TOKEN_PATH, SCOPES, TIMEZONE
from .utils.logger import setup_logger

logger = setup_logger('calendar')


class CalendarService:
    """Manages Google Calendar API interactions."""
    
    def __init__(self):
        self.service = None
        self.timezone = pytz.timezone(TIMEZONE)
    
    def authenticate(self):
        """
        Authenticate with Google Calendar API using OAuth 2.0.
        Opens browser for first-time authentication or uses stored token.
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                logger.info("Starting new authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Authentication successful!")
        
        self.service = build('calendar', 'v3', credentials=creds)
        return True
    
    def get_upcoming_events(self, hours_ahead=168):
        """
        Fetch upcoming events from the primary calendar.
        
        Args:
            hours_ahead: How many hours ahead to look for events (default: 7 days)
        
        Returns:
            List of event dictionaries with parsed information
        """
        if not self.service:
            raise RuntimeError("Calendar service not authenticated. Call authenticate() first.")
        
        try:
            # Calculate time range
            now = datetime.now(self.timezone)
            time_max = now + timedelta(hours=hours_ahead)
            
            logger.info(f"Fetching events from {now} to {time_max}")
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} upcoming events")
            
            # Parse and structure event data
            parsed_events = []
            for event in events:
                parsed_event = self._parse_event(event)
                if parsed_event:
                    parsed_events.append(parsed_event)
            
            return parsed_events
        
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []
    
    def _parse_event(self, event):
        """
        Parse a raw calendar event into a structured dictionary.
        
        Args:
            event: Raw event from Google Calendar API
        
        Returns:
            Parsed event dictionary or None if parsing fails
        """
        try:
            event_id = event.get('id')
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Parse start time
            start = event.get('start', {})
            if 'dateTime' in start:
                start_time = datetime.fromisoformat(start['dateTime'])
            elif 'date' in start:
                # All-day event
                start_time = datetime.fromisoformat(start['date'] + 'T00:00:00')
                start_time = self.timezone.localize(start_time)
            else:
                logger.warning(f"Event {event_id} has no valid start time")
                return None
            
            # Parse end time
            end = event.get('end', {})
            if 'dateTime' in end:
                end_time = datetime.fromisoformat(end['dateTime'])
            elif 'date' in end:
                end_time = datetime.fromisoformat(end['date'] + 'T23:59:59')
                end_time = self.timezone.localize(end_time)
            else:
                end_time = start_time + timedelta(hours=1)  # Default 1 hour
            
            # Get attendees
            attendees = event.get('attendees', [])
            attendee_emails = [a.get('email', '') for a in attendees]
            attendee_count = len(attendees)
            
            # Check if all-day event
            is_all_day = 'date' in start
            
            # Calculate duration
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            return {
                'id': event_id,
                'summary': summary,
                'description': description,
                'location': location,
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': duration_minutes,
                'is_all_day': is_all_day,
                'attendees': attendee_emails,
                'attendee_count': attendee_count,
                'html_link': event.get('htmlLink', ''),
                'raw_event': event
            }
        
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None
