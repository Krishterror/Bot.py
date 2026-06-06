import os
import random
import requests
import telebot

# Fetch configurations from Render's Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
# Replace with your shortener's base domain (e.g., shrinkme.io, adf.ly)
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Type /getkey to generate your 48-hour premium key link.")

@bot.message_handler(commands=['getkey'])
def generate_key_link(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Generating your customized link... please wait.")
    
    try:
        # STEP 1: Define the destination page where the key is displayed
        destination_url = f"https://yourlandingpage.com{user_id}"
        
        # STEP 2: Generate your custom alias structure
        # Chooses a random number between 1 and 100
        random_premium_number = random.randint(1, 100) 
        # Appends User ID to keep it unique so the shortener API doesn't throw a "Duplicate Alias" error
        custom_alias = f"premium{random_premium_number}_{user_id}"
        
        # STEP 3: Request a shortened link with the custom alias attached
        # Note: Most shorteners use '&alias=' to handle custom names
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}&alias={custom_alias}"
        
        response = requests.get(api_request_url).json()
        
        # STEP 4: Process the response and give the link to the user
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
            # If the alias fails or is taken, retry automatically without an alias as a fallback
            fallback_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}"
            fallback_resp = requests.get(fallback_url).json()
            short_link = fallback_resp.get("shortenedUrl", fallback_resp.get("shortened", ""))
            
            bot.send_message(
                message.chat.id,
                f"Your 48-hour key is ready (Standard Slot):\n👉 {short_link}"
            )
            
    except Exception as e:
        print(f"Error encountered: {e}")
        bot.send_message(message.chat.id, "⚠️ System busy. Please try requesting your key again in a moment.")

if __name__ == "__main__":
    print("Bot with custom alias support is running...")
    bot.infinity_polling()
