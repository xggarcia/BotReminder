"""
AI-powered service for intelligent event analysis and reminder scheduling.
Uses Google Gemini to understand events and determine optimal reminder timings.
"""

import json
from datetime import datetime, timedelta
import google.generativeai as genai

from .config import GEMINI_API_KEY
from .utils.logger import setup_logger

logger = setup_logger('ai')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class AIService:
    """Provides AI-powered event analysis and reminder generation."""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_event_and_generate_reminders(self, event):
        """
        Analyze an event and determine optimal reminder timings.
        
        Args:
            event: Parsed event dictionary from CalendarService
        
        Returns:
            Dictionary containing:
            - natural_summary: AI-generated friendly description
            - importance_score: 1-10 rating
            - reminder_times: List of datetime objects when reminders should be sent
            - reminder_messages: List of message strings for each reminder
        """
        try:
            # Prepare event context for AI
            event_context = self._prepare_event_context(event)
            
            # Generate AI analysis
            prompt = self._create_analysis_prompt(event_context)
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            analysis = self._parse_ai_response(response.text, event)
            
            logger.info(f"AI analysis for '{event['summary']}': {len(analysis['reminder_times'])} reminders scheduled")
            return analysis
        
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Fallback to default behavior
            return self._fallback_analysis(event)
    
    def _prepare_event_context(self, event):
        """Prepare event information for AI prompt."""
        now = datetime.now(event['start_time'].tzinfo)
        time_until_event = event['start_time'] - now
        
        context = {
            'title': event['summary'],
            'description': event['description'],
            'location': event['location'],
            'start_time': event['start_time'].strftime('%Y-%m-%d %H:%M'),
            'duration_minutes': event['duration_minutes'],
            'is_all_day': event['is_all_day'],
            'attendee_count': event['attendee_count'],
            'hours_until_event': time_until_event.total_seconds() / 3600,
            'has_location': bool(event['location']),
        }
        return context
    
    def _create_analysis_prompt(self, context):
        """Create the AI prompt for event analysis."""
        prompt = f"""You are an intelligent calendar assistant. Analyze this upcoming event and determine the optimal reminder strategy.

Event Details:
- Title: {context['title']}
- Description: {context['description'] or 'None'}
- Location: {context['location'] or 'None'}
- Start Time: {context['start_time']}
- Duration: {context['duration_minutes']} minutes
- All-day event: {context['is_all_day']}
- Number of attendees: {context['attendee_count']}
- Hours until event: {context['hours_until_event']:.1f}

Your task:
1. Generate a natural, friendly summary of this event (1-2 sentences)
2. Rate the event's importance from 1-10 based on:
   - Number of attendees (more = higher importance)
   - Duration (longer = more important)
   - Keywords in title/description (meeting with CEO, interview, deadline, etc.)
3. Determine optimal reminder times based on:
   - Event location (if it requires travel, remind earlier for commute planning)
   - Event type (important meetings need more reminders)
   - Duration (longer events need advance preparation)
   - Time until event (don't remind too early if event is far away)
4. For each reminder, provide a contextual message

Rules:
- If location is specified, assume 30-60 minutes travel time and remind accordingly
- For very important events (8+), provide 3-4 reminders
- For normal events (5-7), provide 2-3 reminders  
- For low importance (1-4), provide 1-2 reminders
- First reminder should be at least 12-24 hours before (for awareness)
- Always have a final reminder 10-15 minutes before
- If event is within 1 hour, only send one immediate reminder
- Reminder times must be in the future (not in the past)

Respond ONLY with valid JSON in this exact format:
{{
  "natural_summary": "friendly event description",
  "importance_score": 7,
  "reminder_schedule": [
    {{
      "hours_before": 24,
      "message": "Reminder message for this timing"
    }},
    {{
      "hours_before": 2,
      "message": "Another reminder message"
    }}
  ]
}}"""
        return prompt
    
    def _parse_ai_response(self, response_text, event):
        """Parse the AI's JSON response and convert to reminder times."""
        try:
            # Extract JSON from response (remove markdown code blocks if present)
            json_text = response_text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:]
            if json_text.startswith('```'):
                json_text = json_text[3:]
            if json_text.endswith('```'):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            # Parse JSON
            ai_data = json.loads(json_text)
            
            # Calculate actual reminder datetimes
            reminder_times = []
            reminder_messages = []
            now = datetime.now(event['start_time'].tzinfo)
            
            for reminder in ai_data.get('reminder_schedule', []):
                hours_before = reminder.get('hours_before', 1)
                reminder_time = event['start_time'] - timedelta(hours=hours_before)
                
                # Only include reminders that are in the future
                if reminder_time > now:
                    reminder_times.append(reminder_time)
                    reminder_messages.append(reminder.get('message', 'Upcoming event reminder'))
            
            # If no valid reminders, add at least one
            if not reminder_times:
                reminder_time = now + timedelta(minutes=5)
                if reminder_time < event['start_time']:
                    reminder_times.append(reminder_time)
                    reminder_messages.append(f"Immediate reminder: {event['summary']} is coming up soon!")
            
            return {
                'natural_summary': ai_data.get('natural_summary', event['summary']),
                'importance_score': ai_data.get('importance_score', 5),
                'reminder_times': reminder_times,
                'reminder_messages': reminder_messages
            }
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI JSON response: {e}. Using fallback.")
            return self._fallback_analysis(event)
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            return self._fallback_analysis(event)
    
    def _fallback_analysis(self, event):
        """Provide default analysis if AI fails."""
        now = datetime.now(event['start_time'].tzinfo)
        time_until = event['start_time'] - now
        hours_until = time_until.total_seconds() / 3600
        
        reminder_times = []
        reminder_messages = []
        
        # Default reminder schedule based on time until event
        if hours_until > 24:
            # Add 24-hour reminder
            reminder_times.append(event['start_time'] - timedelta(hours=24))
            reminder_messages.append(f"Tomorrow: {event['summary']}")
        
        if hours_until > 2:
            # Add 2-hour reminder
            reminder_times.append(event['start_time'] - timedelta(hours=2))
            reminder_messages.append(f"In 2 hours: {event['summary']}")
        
        if hours_until > 0.25:  # 15 minutes
            # Add 15-minute reminder
            reminder_times.append(event['start_time'] - timedelta(minutes=15))
            reminder_messages.append(f"Starting soon: {event['summary']}")
        
        # Filter out past reminders
        valid_reminders = [(t, m) for t, m in zip(reminder_times, reminder_messages) if t > now]
        
        if valid_reminders:
            reminder_times, reminder_messages = zip(*valid_reminders)
            reminder_times = list(reminder_times)
            reminder_messages = list(reminder_messages)
        else:
            # At least one immediate reminder
            reminder_times = [now + timedelta(minutes=5)]
            reminder_messages = [f"Reminder: {event['summary']} is coming up!"]
        
        return {
            'natural_summary': event['summary'],
            'importance_score': 5,
            'reminder_times': reminder_times,
            'reminder_messages': reminder_messages
        }
