"""
Configuration management for the Calendar Reminder Bot.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Google Calendar API
GOOGLE_CREDENTIALS_PATH = os.getenv(
    'GOOGLE_CREDENTIALS_PATH', 
    str(BASE_DIR / 'credentials' / 'credentials.json')
)
TOKEN_PATH = str(BASE_DIR / 'credentials' / 'token.json')
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Google Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Notification Channels
ENABLE_EMAIL = os.getenv('ENABLE_EMAIL', 'false').lower() == 'true'
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'

# Email Configuration
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Bot Settings
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Madrid')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', str(BASE_DIR / 'bot.log'))

# Database
DB_PATH = str(BASE_DIR / 'reminders.db')

# Validation
def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is required for AI features")
    
    if not ENABLE_EMAIL and not ENABLE_TELEGRAM:
        errors.append("At least one notification channel (EMAIL or TELEGRAM) must be enabled")
    
    if ENABLE_EMAIL:
        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            errors.append("EMAIL_ADDRESS and EMAIL_PASSWORD are required when email is enabled")
    
    if ENABLE_TELEGRAM:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required when Telegram is enabled")
    
    if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
        errors.append(f"Google credentials file not found at {GOOGLE_CREDENTIALS_PATH}")
    
    return errors
