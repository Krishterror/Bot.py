import os
import time
import random
import asyncio
import threading
import requests
import telebot
from telethon import TelegramClient
from sqlitedict import SqliteDict

# Load configurations from Render
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
ORIGINAL_BOT_USERNAME = os.environ.get("ORIGINAL_BOT_USERNAME")

# Initialize database to track users and cache fetched keys
db = SqliteDict('./bot_data.db', autocommit=True)

bot = telebot.TeleBot(BOT_TOKEN)

async def fetch_key_from_source(product_name):
    """Connects to the original bot, clicks 'Get Trial Key', then clicks the requested product."""
    async with TelegramClient('user_session', API_ID, API_HASH) as tg_client:
        # Step A: Send /start to load the main menu
        await tg_client.send_message(ORIGINAL_BOT_USERNAME, "/start")
        await asyncio.sleep(3)
        
        # Step B: Look for and click the "Get Trial Key" button
        clicked_first = False
        async for message in tg_client.iter_messages(ORIGINAL_BOT_USERNAME, limit=1):
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        if "Get Trial Key" in button.text:
                            await button.click()
                            clicked_first = True
                            break
        
        if not clicked_first:
            return "Error: Main menu button not found."
            
        await asyncio.sleep(3) # Wait for product menu to load
        
        # Step C: Look for the specific product button (e.g., BR MODS, HEX BLADE)
        async for message in tg_client.iter_messages(ORIGINAL_BOT_USERNAME, limit=1):
            if message.buttons:
                for row in message.buttons:
                    for button in row:
                        # Case-insensitive match for the product name
                        if product_name.lower() in button.text.lower():
                            await button.click()
                            await asyncio.sleep(4) # Wait for the final key text response
                            
                            # Grab the final text containing the premium key
                            async for final_msg in tg_client.iter_messages(ORIGINAL_BOT_USERNAME, limit=1):
                                return final_msg.text
                                
        return "Error: Product button not found or limit reached."

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "Welcome! To get a customized 48-hour premium key link, "
        "use the command followed by the product name.\n\n"
        "Example:\n`/getkey BR MODS`\n`/getkey HEX BLADE`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['getkey'])
def generate_key_link(message):
    user_id = str(message.from_user.id)
    current_time = time.time()
    
    # Extract the product name from the user's command
    command_parts = message.text.split(" ", 1)
    if len(command_parts) < 2:
        bot.reply_to(message, "❌ Please specify a product. Example: `/getkey BR MODS`", parse_mode="Markdown")
        return
        
    product_target = command_parts[1].strip()
    product_key_db = f"cache_{product_target.lower()}"

    # 1. 48-HOUR USER LOCK CHECK
    user_cooldown_key = f"user_{user_id}_{product_target.lower()}"
    if user_cooldown_key in db:
        time_passed = current_time - db[user_cooldown_key]
        if time_passed < 172800: # 48 hours in seconds
            remaining_hours = int((172800 - time_passed) // 3600)
            bot.reply_to(message, f"⏳ You have already claimed a key for {product_target}. Please wait {remaining_hours} hours to get a new one.")
            return

    bot.reply_to(message, f"Searching and encoding your link for {product_target}... please wait.")

    try:
        # 2. CACHE SYSTEM (Allows multiple users to share a key within the time limit safely)
        real_premium_key = ""
        if product_key_db in db and (current_time - db[product_key_db]['timestamp'] < 86400):
            # If a key was fetched in the last 24 hours, reuse it so we don't hit the target bot's limit
            real_premium_key = db[product_key_db]['key']
        else:
            # Fetch a fresh key if cache is old or empty
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            fetched_text = loop.run_until_complete(fetch_key_from_source(product_target))
            
            if "Error" in fetched_text or "already" in fetched_text.lower():
                # Fallback: Use the last known saved key if the original bot blocks the script
                if product_key_db in db:
                    real_premium_key = db[product_key_db]['key']
                else:
                    bot.send_message(message.chat.id, "⚠️ Target server limit reached. Try a different product name.")
                    return
            else:
                real_premium_key = fetched_text
                db[product_key_db] = {'key': real_premium_key, 'timestamp': current_time}

        # 3. SHORTEN URL LOGIC WITH CUSTOM ALIAS
        destination_url = f"https://google.com{real_premium_key}"
        random_premium_number = random.randint(1, 100) 
        custom_alias = f"premium{random_premium_number}_{user_id}"
        
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}&alias={custom_alias}"
        response = requests.get(api_request_url).json()
        
        if response.get("status") == "success" or "shortenedUrl" in response:
            short_link = response.get("shortenedUrl", response.get("shortened", ""))
            
            # Start user's personal 48-hour timer restriction now that link is ready
            db[user_cooldown_key] = current_time
            
            bot.send_message(
                message.chat.id, 
                f"🎁 Your 48-hour {product_target} key link is ready!\n\n"
                f"Slot: **premium{random_premium_number}**\n\n"
                f"👉 Click here to unlock: {short_link}\n\n"
                "Complete the captcha verification steps on the page to view your premium key."
            )
        else:
            bot.send_message(message.chat.id, "❌ Link shortener error. Try again.")
            
    except Exception as e:
        print(f"Error handling request: {e}")
        bot.send_message(message.chat.id, "⚠️ System busy. Please verify your command spelling and try again.")

# FAKE SERVER ROUTINE FOR RENDER COMPATIBILITY
if __name__ == "__main__":
    import http.server
    import socketserver
    PORT = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    def run_fake_server():
        try:
            with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
                httpd.serve_forever()
        except Exception: pass
    threading.Thread(target=run_fake_server, daemon=True).start()

    print("Automated Cloner Bot with caching and item routing is running...")
    bot.infinity_polling()
