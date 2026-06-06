import os
import requests
import telebot

# 1. Fetching configurations from Render's Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHORTENER_API_KEY = os.environ.get("SHORTENER_API")
# Replace 'YOUR_SHORTENER_DOMAIN' with your actual shortener site (e.g., shrinkme.io, adfly.com)
SHORTENER_URL = "https://YOUR_SHORTENER_DOMAIN/api?api=" 

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Type /getkey to generate your 48-hour premium key link.")

@bot.message_handler(commands=['getkey'])
def generate_key_link(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Generating your link... please wait.")
    
    try:
        # STEP A: Define the destination page where the user gets the final key
        # In a fully automated setup, you would fetch this from your original bot, 
        # but as a start, this points to your key destination page.
        destination_url = f"https://yourlandingpage.com{user_id}"
        
        # STEP B: Request a shortened, monetized link from your shortener API
        api_request_url = f"{SHORTENER_URL}{SHORTENER_API_KEY}&url={destination_url}"
        response = requests.get(api_request_url).json()
        
        # STEP C: Send the link to the user
        if response.get("status") == "success" or "shortenedUrl" in response:
            # Note: Adjust 'shortenedUrl' based on your exact shortener's JSON response template
            short_link = response.get("shortenedUrl", response.get("shortened", ""))
            
            bot.send_message(
                message.chat.id, 
                f"Your 48-hour key is ready!\n\n👉 Click here to unlock it: {short_link}\n\n"
                "Complete the captcha/ads on the page to view your premium key."
            )
        else:
            bot.send_message(message.chat.id, "❌ Error generating your link. Please try again later.")
            
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "⚠️ An error occurred while talking to the shortener service.")

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

