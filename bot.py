import os
import telebot
import threading
import time
from flask import Flask
from pymongo import MongoClient

# --- Render Port Fix ---
app = Flask(__name__)
@app.route('/')
def home(): return "MdmKillerPro System is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 1380004832))

client = MongoClient(MONGO_URI)
db = client['MdmKillerProDB']
users_collection = db['users']
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# --- Commands ---
@bot.message_handler(commands=['menu'])
def menu(message):
    bot.send_message(message.chat.id, "🔥 **MdmKillerPro Dashboard Online** 🔥\n\nCommands: /register, /profile, /activate")

@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == ADMIN_ID:
        total = users_collection.count_documents({})
        bot.reply_to(message, f"📊 Total DB Users: {total}")

# --- Execution ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start() # Flask ko alag thread me chalana
    print("Bot is starting...")
    bot.infinity_polling() # Bot ko main thread me chalana

