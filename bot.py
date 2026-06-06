import os
import random
import asyncio
import requests
import telebot
from telethon import TelegramClient, events

# Load all configurations from Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

# New variables for bot-to-bot communication
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
ORIGINAL_BOT_USERNAME = os.environ.get("ORIGINAL_BOT_USERNAME") # e.g., @TheRealKeyBot

# Initialize your Telegram Bot interface
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize Telethon Client to talk to the original bot on your behalf
client = TelegramClient('bot_session', API_ID, API_HASH)

async def fetch_key_from_original_bot():
    """This function sends a command to the original bot and captures its response."""
    async with TelegramClient('bot_session', API_ID, API_HASH) as tg_client:
        # Send the command to the original bot to get a key
        await tg_client.send_message(ORIGINAL_BOT_USERNAME, "/getkey")
        
        # Wait up to 10 seconds for the original bot to reply
        await asyncio.sleep(3) 
        
        # Grab the last message sent by the original bot
        async for message in tg_client.iter_messages(ORIGINAL_BOT_USERNAME, limit=1):
            return message.text
    return "No key found"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Type /getkey to generate your 48-hour premium key link.")

@bot.message_handler(commands=['getkey'])
def generate_key_link(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Connecting to the key server... please wait a moment.")
    
    try:
        # 1. RUN THE BOT-TO-BOT FETCH
        # Run the asynchronous function inside our normal bot thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        real_premium_key = loop.run_until_complete(fetch_key_from_original_bot())
        
        # 2. ENCODE THE KEY INTO A DESTINATION LINK
        # Your shortener requires a web URL, so we pass the key inside a display page link
        destination_url = f"https://yourlandingpage.com{real_premium_key}"
        
        # 3. CREATE ALIAS & SHORTEN
        random_premium_number = random.randint(1, 100) 
        custom_alias = f"premium{random_premium_number}_{user_id}"
        
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}&alias={custom_alias}"
        response = requests.get(api_request_url).json()
        
        # 4. SEND MONETIZED LINK TO USER
        if response.get("status") == "success" or "shortenedUrl" in response:
            short_link = response.get("shortenedUrl", response.get("shortened", ""))
            bot.send_message(
                message.chat.id, 
                f"🎁 Your 48-hour premium key link is ready!\n\n"
                f"Generated Alias Slot: **premium{random_premium_number}**\n\n"
                f"👉 Click here to unlock: {short_link}\n\n"
                "Complete the step on the page to view your key."
            )
        else:
            bot.send_message(message.chat.id, "❌ Shortener error. Try again.")
            
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "⚠️ System busy. Please try again.")

if __name__ == "__main__":
    print("Automated Cloner Bot is running...")
    bot.infinity_polling()
