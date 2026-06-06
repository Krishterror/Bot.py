import os
import random
import asyncio
import telebot
from telethon import TelegramClient

# 1. Load configurations from Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
ORIGINAL_BOT_USERNAME = os.environ.get("ORIGINAL_BOT_USERNAME")

# 2. Initialize your user-facing Telegram Bot interface
bot = telebot.TeleBot(BOT_TOKEN)

async def fetch_key_from_original_bot():
    """
    Connects to Telegram as a user client, requests a key from the original bot,
    and returns its text response. Uses a safe string name to avoid colon errors.
    """
    # Fixes the colon error by using a strict text string 'user_session' for the session name
    async with TelegramClient('user_session', API_ID, API_HASH) as tg_client:
        # Send the request command to the target bot
        await tg_client.send_message(ORIGINAL_BOT_USERNAME, "/getkey")
        
        # Wait 4 seconds for the original bot to process and reply
        await asyncio.sleep(4) 
        
        # Fetch the very last message received from that bot
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
        import requests
        
        # 1. Fetch the real key from the original bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        real_premium_key = loop.run_until_complete(fetch_key_from_original_bot())
        
        # 2. Pack the fetched key into a destination link
        destination_url = f"https://yourlandingpage.com{real_premium_key}"
        
        # 3. Create a unique custom alias (premium1 to premium100) + User ID to prevent duplicate errors
        random_premium_number = random.randint(1, 100) 
        custom_alias = f"premium{random_premium_number}_{user_id}"
        
        # 4. Request the monetized link from your shortener API
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}&alias={custom_alias}"
        response = requests.get(api_request_url).json()
        
        # 5. Deliver the link to your user
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
            bot.send_message(message.chat.id, "❌ Link shortener service busy. Please try again.")
            
    except Exception as e:
        print(f"Error details: {e}")
        bot.send_message(message.chat.id, "⚠️ System busy. Please try again in a moment.")

if __name__ == "__main__":
    print("Automated Cloner Bot is initialized...")
    bot.infinity_polling()
