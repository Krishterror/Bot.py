import os
import random
import asyncio
import requests
import telebot
from telethon import TelegramClient

# Load configurations from Render Settings
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
ORIGINAL_BOT_USERNAME = os.environ.get("ORIGINAL_BOT_USERNAME")
TELETHON_SESSION = os.environ.get("TELETHON_SESSION") # The new secure login key

# Initialize your user-facing Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

async def fetch_key_from_original_bot():
    """Logs in using the secure session string and requests the premium key."""
    from telethon.sessions import StringSession
    
    # Securely log in using the session string instead of trying to trigger a code prompt
    async with TelegramClient(StringSession(TELETHON_SESSION), API_ID, API_HASH) as tg_client:
        await tg_client.send_message(ORIGINAL_BOT_USERNAME, "/getkey")
        await asyncio.sleep(4) # Wait 4 seconds for a response
        
        async for message in tg_client.iter_messages(ORIGINAL_BOT_USERNAME, limit=1):
            return message.text
    return "No key found"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /getkey to generate your 48-hour premium key link.")

@bot.message_handler(commands=['getkey'])
def generate_key_link(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Contacting the key server... please wait a moment.")
    
    try:
        # Run the asynchronous bot-to-bot function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        real_premium_key = loop.run_until_complete(fetch_key_from_original_bot())
        
        # Encode the real premium key into your link destination
        destination_url = f"https://yourlandingpage.com{real_premium_key}"
        
        # Set up custom alias
        random_premium_number = random.randint(1, 100) 
        custom_alias = f"premium{random_premium_number}_{user_id}"
        
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}&alias={custom_alias}"
        response = requests.get(api_request_url).json()
        
        if response.get("status") == "success" or "shortenedUrl" in response:
            short_link = response.get("shortenedUrl", response.get("shortened", ""))
            bot.send_message(
                message.chat.id, 
                f"🎁 Your 48-hour premium key link is ready!\n\n"
                f"Generated Alias Slot: **premium{random_premium_number}**\n\n"
                f"👉 Click here to unlock: {short_link}\n\n"
                "Complete the captcha/ads on the page to view your key."
            )
        else:
            bot.send_message(message.chat.id, "❌ Link shortener error. Please try again.")
            
    except Exception as e:
        print(f"Error details: {e}")
        bot.send_message(message.chat.id, "⚠️ System busy. Please try again in a moment.")

if __name__ == "__main__":
    print("Automated Cloner Bot is initialized...")
    bot.infinity_polling()
