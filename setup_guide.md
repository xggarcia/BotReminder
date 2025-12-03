# Calendar Reminder Bot - Setup Guide

This guide will walk you through setting up the AI-Powered Calendar Reminder Bot from scratch.

## Prerequisites

- Python 3.8 or higher
- A Google account with Google Calendar
- (Optional) A Gmail account for email notifications
- (Optional) A Telegram account for Telegram notifications

## Step 1: Install Python Dependencies

Navigate to the project directory and install required packages:

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Google Cloud Platform & Calendar API

### 2.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "Calendar Reminder Bot")
4. Click "Create"

### 2.2 Enable Google Calendar API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Calendar API"
3. Click on it and click "Enable"

### 2.3 Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: "External" (or "Internal" if using Google Workspace)
   - App name: "Calendar Reminder Bot"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip this for now
   - Test users: Add your email
   - Click "Save and Continue"
4. Back to creating OAuth client ID:
   - Application type: "Desktop app"
   - Name: "Calendar Bot Desktop Client"
   - Click "Create"
5. Download the JSON file
6. Create a `credentials` folder in your project directory
7. Rename the downloaded file to `credentials.json` and move it to `credentials/credentials.json`

## Step 3: Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key (you'll need it in the next step)

## Step 4: Configure Email (Optional)

If you want email notifications:

### For Gmail:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click "2-Step Verification"
   - Scroll down to "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Enter "Calendar Bot" and click "Generate"
   - Copy the 16-character password (you'll need it in the next step)

### For Other Email Providers:

Check your provider's SMTP settings and credentials.

## Step 5: Set Up Telegram Bot (Optional)

If you want Telegram notifications:

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow the prompts to create your bot
4. Copy the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
5. Get your Chat ID:
   - Send a message to your new bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response (under `message.chat.id`)

## Step 6: Create Configuration File

1. Copy the example configuration:

   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and fill in your settings:

```env
# Google Calendar API (required)
GOOGLE_CREDENTIALS_PATH=credentials/credentials.json

# Google Gemini AI API (required)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Notification Channels (at least one required)
ENABLE_EMAIL=true
ENABLE_TELEGRAM=true

# Email Configuration (if ENABLE_EMAIL=true)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Telegram Configuration (if ENABLE_TELEGRAM=true)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=your_chat_id_here

# Bot Settings
CHECK_INTERVAL_MINUTES=15
TIMEZONE=Europe/Madrid

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

## Step 7: First Run & Authentication

1. Run the test command to verify your setup:

   ```bash
   python main.py --test
   ```

2. On first run, a browser window will open asking you to:

   - Sign in to your Google account
   - Grant the bot permission to read your calendar
   - This creates a `token.json` file for future use

3. Check if you received the test notification via email and/or Telegram

## Step 8: Run the Bot

### Continuous Mode (Normal Usage)

Run the bot to continuously monitor your calendar:

```bash
python main.py
```

The bot will:

- Check your calendar every 15 minutes (configurable)
- Analyze upcoming events with AI
- Send reminders at optimal times
- Keep running until you stop it (Ctrl+C)

### Single Check Mode (Testing)

Run a single check and exit:

```bash
python main.py --once
```

Useful for testing or running via scheduled tasks.

## Troubleshooting

### "Configuration errors found"

- Ensure your `.env` file has all required fields filled
- Check that API keys are valid
- Verify file paths are correct

### "Failed to authenticate with Google Calendar"

- Make sure `credentials.json` is in the `credentials/` folder
- Delete `token.json` and try again to re-authenticate
- Check that Google Calendar API is enabled in your project

### "Email sending failed"

- For Gmail, ensure you're using an App Password, not your regular password
- Check SMTP server and port settings
- Verify your email and password are correct

### "Telegram sending failed"

- Verify bot token is correct
- Make sure you've sent at least one message to your bot
- Check that chat ID is correct

### No reminders being sent

- Check that you have upcoming events in your calendar
- Run with `--once` to see immediate results
- Check `bot.log` for error messages
- Verify your timezone is set correctly in `.env`

## Running as a Background Service

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "When computer starts")
4. Action: "Start a program"
5. Program: `python.exe`
6. Arguments: `main.py`
7. Start in: `D:\My Projects\BotReminder`

### Linux/Mac (systemd or cron)

Create a systemd service or add a cron job:

```bash
@reboot cd /path/to/BotReminder && python main.py
```

## Next Steps

- Add events to your Google Calendar and watch the bot send smart reminders!
- Adjust `CHECK_INTERVAL_MINUTES` in `.env` to change how often it checks
- Monitor `bot.log` to see what the bot is doing
- Customize reminder messages by modifying the AI prompts in `src/ai_service.py`

For more information, see the main [README.md](file:///d:/My%20Projects/BotReminder/README.md).
