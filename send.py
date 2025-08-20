import json
import os
import time
import schedule
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import TelegramError
from dotenv import load_dotenv
import asyncio
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramScheduler:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.webapp_url = os.getenv('WEBAPP_URL')
        self.users_file = 'users.json'
        
        if not self.bot_token or not self.webapp_url:
            raise ValueError("BOT_TOKEN and WEBAPP_URL must be set in .env file")
        
        self.bot = Bot(token=self.bot_token)
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                users = json.load(f)
            return users
        except FileNotFoundError:
            logger.warning(f"{self.users_file} not found. Creating empty list.")
            return []
        except json.JSONDecodeError:
            logger.error(f"Error decoding {self.users_file}. Creating empty list.")
            return []
    
    def save_users(self, users):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
            logger.info(f"Saved {len(users)} users to {self.users_file}")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def remove_user(self, user_id):
        """Remove a user from the JSON file"""
        users = self.load_users()
        if user_id in users:
            users.remove(user_id)
            self.save_users(users)
            logger.info(f"Removed user {user_id} from database")
    
    async def send_verification_message(self, user_id):
        """Send verification message to a specific user"""
        try:
            # Create inline keyboard with web app button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "☑️ Verify Activity", 
                    web_app=WebAppInfo(url=self.webapp_url)
                )]
            ])
            
            message = "⚙️ Please Verify your activity to receive your reward"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard
            )
            
            logger.info(f"Message sent successfully to user {user_id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            
            # Remove user if they blocked the bot or chat doesn't exist
            error_message = str(e).lower()
            if any(phrase in error_message for phrase in [
                "bot was blocked", 
                "chat not found", 
                "user is deactivated",
                "forbidden"
            ]):
                self.remove_user(user_id)
            
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message to user {user_id}: {e}")
            return False
    
    async def send_messages_to_all_users(self):
        """Send messages to all users in the database"""
        users = self.load_users()
        
        if not users:
            logger.info("No users found in database")
            return
        
        logger.info(f"Starting to send messages to {len(users)} users")
        
        successful_sends = 0
        failed_sends = 0
        
        for user_id in users.copy():  # Use copy to avoid modification during iteration
            success = await self.send_verification_message(user_id)
            if success:
                successful_sends += 1
            else:
                failed_sends += 1
            
            # Small delay between messages to avoid rate limiting
            await asyncio.sleep(0.1)
        
        logger.info(f"Message sending completed. Success: {successful_sends}, Failed: {failed_sends}")
    
    def run_scheduled_task(self):
        """Run the scheduled task (wrapper for async function)"""
        try:
            logger.info("Starting scheduled message sending task")
            asyncio.run(self.send_messages_to_all_users())
        except Exception as e:
            logger.error(f"Error in scheduled task: {e}")

def main():
    """Main function to set up and run the scheduler"""
    try:
        scheduler = TelegramScheduler()
        
        # Schedule the task to run every day at midnight
        schedule.every().day.at("00:00").do(scheduler.run_scheduled_task)
        
        logger.info("Telegram scheduler started. Will send messages every day at midnight.")
        logger.info("Press Ctrl+C to stop the scheduler")
        
        # Run immediately on startup (optional - comment out if you don't want this)
        logger.info("Running initial message send...")
        scheduler.run_scheduled_task()
        
        # Keep the script running and check for scheduled tasks
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()