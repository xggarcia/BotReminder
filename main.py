"""
Main entry point for the Calendar Reminder Bot.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import validate_config, LOG_LEVEL, LOG_FILE, CHECK_INTERVAL_MINUTES
from src.utils.logger import setup_logger
from src.scheduler import ReminderScheduler
from src.notification_service import NotificationService

# Set up main logger
logger = setup_logger('main', log_file=LOG_FILE, level=LOG_LEVEL)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI-Powered Calendar Reminder Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run the bot in continuous mode
  python main.py --test             # Send a test notification
  python main.py --once             # Run one check and exit
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Send a test notification and exit'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run a single reminder check and exit (useful for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    logger.info("🚀 Starting Calendar Reminder Bot")
    logger.info("Validating configuration...")
    
    config_errors = validate_config()
    if config_errors:
        logger.error("❌ Configuration errors found:")
        for error in config_errors:
            logger.error(f"  - {error}")
        logger.error("\nPlease check your .env file and ensure all required settings are configured.")
        logger.error("See .env.example for reference.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated")
    
    # Test mode
    if args.test:
        logger.info("Running in TEST mode - sending test notification...")
        notifier = NotificationService()
        success = notifier.send_test_notification()
        
        if success:
            logger.info("✅ Test notification sent successfully!")
            logger.info("Check your email and/or Telegram to verify it was received.")
        else:
            logger.error("❌ Failed to send test notification")
            logger.error("Please check your notification settings in the .env file")
        
        sys.exit(0 if success else 1)
    
    # Initialize scheduler
    try:
        scheduler = ReminderScheduler()
        scheduler.initialize()
    except Exception as e:
        logger.error(f"❌ Failed to initialize scheduler: {e}")
        logger.error("\nPlease ensure:")
        logger.error("  1. You have set up Google Calendar API credentials")
        logger.error("  2. The credentials file is in the correct location")
        logger.error("  3. Your .env file is configured correctly")
        sys.exit(1)
    
    # Run mode
    if args.once:
        logger.info("Running in ONCE mode - single check...")
        scheduler.run_once()
        logger.info("✅ Single check completed")
    else:
        logger.info("Running in CONTINUOUS mode...")
        logger.info(f"Checking for reminders every {CHECK_INTERVAL_MINUTES} minutes")
        logger.info("Press Ctrl+C to stop")
        
        try:
            scheduler.run(check_interval_minutes=CHECK_INTERVAL_MINUTES)
        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down gracefully...")
            sys.exit(0)


if __name__ == '__main__':
    main()
