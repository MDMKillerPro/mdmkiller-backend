import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import threading
import time
from flask import Flask

# --- 🌐 Flask Server for Render Free Tier ---
# Render Free Web Service ko port 10000 chahiye hota hai, yeh dummy server wahi kaam karega.
app = Flask(__name__)

@app.route('/')
def index():
    return "MdmKillerPro Bot is Live and Running!"

def run_flask():
    # Render se port uthayega, default 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 🔐 Configuration via Environment Variables ---
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_ENV = os.getenv("ADMIN_ID")

if not MONGO_URI or not BOT_TOKEN or not ADMIN_ID_ENV:
    print("❌ ERROR: Variables Missing! Render panel me set karein.")
    exit(1)

ADMIN_TELEGRAM_ID = int(ADMIN_ID_ENV)

# Database Connection
client = MongoClient(MONGO_URI)
db = client['MdmKillerProDB']
users_collection = db['users']

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# --- ⏳ Auto Delete Helper Function ---
def auto_delete_messages(chat_id, message_ids, delay=10):
    def delete():
        time.sleep(delay)
        for msg_id in message_ids:
            try:
                bot.delete_message(chat_id, msg_id)
            except Exception:
                pass 
    threading.Thread(target=delete).start()

# 1. /menu - Interactive Control Panel
@bot.message_handler(commands=['menu'])
def send_menu(message):
    text = (
        "🔥 **Welcome to MdmKillerPro Dashboard** 🔥\n\n"
        "Niche diye gaye buttons ka use karke aap tool download kar sakte hain, "
        "support team se baat kar sakte hain, ya apna panel check kar sakte hain."
    )
    markup = InlineKeyboardMarkup(row_width=2)
    btn_download = InlineKeyboardButton("📥 Download Tool", url="https://aapki-website.com/download")
    btn_panel = InlineKeyboardButton("🌐 Web Panel", url="https://aapki-website.com")
    btn_support = InlineKeyboardButton("💬 Support Chat", url="https://t.me/your_support")
    btn_channel = InlineKeyboardButton("📢 Join Channel", url="https://t.me/your_channel")
    
    markup.add(btn_download, btn_panel, btn_support, btn_channel)
    sent_msg = bot.send_message(message.chat.id, text, reply_markup=markup)
    auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=15)

# 2. /profile - Check Balance & Role
@bot.message_handler(commands=['profile'])
def check_profile(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/profile target_user@gmail.com`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
        
        email = args[1].strip()
        user = users_collection.find_one({"email": email})
        
        if user:
            response = (
                "📋 **MdmKillerPro User Profile**\n\n"
                f"📧 **Email:** {user['email']}\n"
                f"🎖️ **Role:** {user.get('role', 'Reseller').capitalize()}\n"
                f"💰 **Credits:** {user.get('credits', 0)}"
            )
            sent_msg = bot.reply_to(message, response)
        else:
            sent_msg = bot.reply_to(message, "❌ Is email se koi account nahi mila.")
            
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=10)
    except Exception:
        pass

# 3. /register - Group Account Creation
@bot.message_handler(commands=['register'])
def register_user(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/register [email] [password]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
        
        email = args[1].strip()
        password = args[2].strip()
        
        if users_collection.find_one({"email": email}):
            sent_msg = bot.reply_to(message, "❌ Account already exists.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        users_collection.insert_one({"email": email, "password": password, "role": "reseller", "credits": 0, "status": "inactive"})
        sent_msg = bot.reply_to(message, f"✅ **Account Created!**\n📧 Email: {email}\nNow use `/activate`.")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=10)
    except Exception:
        pass

# 4. /activate - Email Activation (100 Credits Cost)
@bot.message_handler(commands=['activate'])
def activate_user_account(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/activate [your_email] [target_email]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=6)
            return
            
        reseller_email, target_email = args[1].strip(), args[2].strip()
        reseller = users_collection.find_one({"email": reseller_email})
        
        if not reseller or reseller.get('credits', 0) < 100:
            sent_msg = bot.reply_to(message, "❌ Credits kam hain ya account nahi mila.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        if users_collection.update_one({"email": target_email}, {"$set": {"status": "active"}}).matched_count > 0:
            users_collection.update_one({"email": reseller_email}, {"$inc": {"credits": -100}})
            sent_msg = bot.reply_to(message, f"🎉 **{target_email} Activated!**")
        else:
            sent_msg = bot.reply_to(message, "❌ Target user nahi mila.")
            
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=12)
    except Exception:
        pass

# 5. /checkuser - Account Status
@bot.message_handler(commands=['checkuser'])
def check_user_status(message):
    try:
        args = message.text.split()
        if len(args) < 2: return
        user = users_collection.find_one({"email": args[1].strip()})
        if user:
            status = user.get('status', 'inactive').upper()
            sent_msg = bot.reply_to(message, f"{'🟢' if status == 'ACTIVE' else '🔴'} Status: {status}")
        else:
            sent_msg = bot.reply_to(message, "❌ Not Found.")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=8)
    except Exception:
        pass

# 6. /addcredits - ADMIN ONLY
@bot.message_handler(commands=['addcredits'])
def add_credits(message):
    if message.from_user.id != ADMIN_TELEGRAM_ID: return
    try:
        args = message.text.split()
        users_collection.update_one({"email": args[1].strip()}, {"$inc": {"credits": int(args[2])}})
        bot.reply_to(message, "✅ Credits Added!")
    except Exception:
        pass

# 7. /stats - ADMIN ONLY
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_TELEGRAM_ID: return
    total = users_collection.count_documents({})
    active = users_collection.count_documents({"status": "active"})
    bot.reply_to(message, f"📊 Total: {total}\n🟢 Active: {active}")

# 8. /cleanwelcome - Clean Welcomes
clean_welcome_status = {}
last_welcome_msg_id = {}

@bot.message_handler(commands=['cleanwelcome'])
def toggle_clean_welcome(message):
    status = message.text.split()[1].lower() if len(message.text.split()) > 1 else "off"
    clean_welcome_status[message.chat.id] = (status == "on")
    bot.reply_to(message, f"🧹 Clean Welcome: {status.upper()}")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    chat_id = message.chat.id
    if clean_welcome_status.get(chat_id) and chat_id in last_welcome_msg_id:
        try: bot.delete_message(chat_id, last_welcome_msg_id[chat_id])
        except Exception: pass
    sent_msg = bot.send_message(chat_id, f"👋 Hey {message.new_chat_members[0].first_name}, Welcome! Type `/menu`.")
    last_welcome_msg_id[chat_id] = sent_msg.message_id

# --- 🚀 Main Execution ---
if __name__ == "__main__":
    # Flask ko thread me chalana takki Render port 10000 check kar sake
    threading.Thread(target=run_flask).start()
    
    print("MdmKillerPro Bot is Starting...")
    bot.infinity_polling()
