import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
import logging
import sys
from PIL import Image
import io
import random
import requests
from dotenv import load_dotenv
from telegram.error import TelegramError

# Load environment variables from the .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Direct credentials loaded from the .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize clients
try:
    openai.api_key = OPENAI_API_KEY
    logger.info("Successfully initialized clients")
except Exception as e:
    logger.error(f"Failed to initialize clients: {str(e)}")
    sys.exit(1)

# Start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info(f"Start command received from user {update.effective_user.id}")
        await update.message.reply_text(":wave: Welcome to the Weekly Coloring Challenge!\n\nSend me a prompt like:\n`A cat riding a bike` :bike::cat:")
    except Exception as e:
        logger.error(f"Error in start handler: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

# Handle prompt messages
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith('/'):
        return  # Ignore commands

    try:
        user = update.effective_user
        prompt = update.message.text
        logger.info(f"Received prompt from user {user.id}: {prompt}")

        # Generate image using DALL·E 3
        dalle_prompt = f"Black and white line art of: {prompt}, suitable for coloring book"
        response = openai.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url

        # Simulate rating for demo purposes (OpenAI does not rate images directly, so we simulate this)
        rating = random.randint(1, 10)  # Random rating (1-10)
        
        # Appreciation message based on rating
        appreciation = ""
        if rating == 10:
            appreciation = "Excellent work! You've nailed it!"
        elif rating >= 8:
            appreciation = "Great job! Really impressive!"
        elif rating >= 6:
            appreciation = "Good effort! Keep it up!"
        else:
            appreciation = "Nice try! Keep practicing!"

        # Send the image with rating and appreciation message
        await update.message.reply_photo(photo=image_url, caption=f":art: Here's your coloring sheet!\nRating: {rating}/10\n{appreciation}")

    except Exception as e:
        logger.error(f"Error in handle_prompt: {str(e)}")
        await update.message.reply_text(f"Sorry, something went wrong: {e}")

# Handle image uploads (colored sheet)
async def handle_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        photo = update.message.photo[-1]  # Get the largest photo
        file = await context.bot.get_file(photo.file_id)
        file_path = f"temp_{photo.file_id}.jpg"
        await file.download_to_drive(file_path)
        logger.info(f"Received submission from user {user.id}")

        # Verify image using PIL
        with Image.open(file_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Save as JPEG
            img.save(file_path, 'JPEG')

        # Simulate rating for demo purposes (OpenAI does not rate images directly, so we simulate this)
        rating = random.randint(1, 10)  # Random rating (1-10)

        # Appreciation message based on rating
        appreciation = ""
        if rating == 10:
            appreciation = "Excellent work! You've nailed it!"
        elif rating >= 8:
            appreciation = "Great job! Really impressive!"
        elif rating >= 6:
            appreciation = "Good effort! Keep it up!"
        else:
            appreciation = "Nice try! Keep practicing!"

        # Send back the rating and appreciation to the user
        await update.message.reply_text(f":white_check_mark: Submission received! Rating: {rating}/10\n{appreciation} Points will be awarded upon approval.")

        # Clean up temporary file
        os.remove(file_path)
        
    except Exception as e:
        logger.error(f"Error in handle_submission: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong while processing your submission. Please try again later.")

async def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Optionally, notify the user

def main():
    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.PHOTO, handle_submission))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))

        # Add error handler
        application.add_error_handler(error_handler)

        # Start the bot
        logger.info("Starting bot...")
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8443)),
            webhook_url=f"https://color-sheet.onrender.com/webhook/{BOT_TOKEN}"
        )
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}")
    finally:
        logger.info("Bot disconnected")

if __name__ == "__main__":
    main()
