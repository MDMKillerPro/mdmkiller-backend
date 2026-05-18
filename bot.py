import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import threading
import time

# --- 🔐 Configuration via Environment Variables ---
# Ye data GitHub par nahi dikhega, ise hum direct Render panel me fill karenge
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_ENV = os.getenv("ADMIN_ID")

# Check ki variables set hain ya nahi (for safety)
if not MONGO_URI or not BOT_TOKEN or not ADMIN_ID_ENV:
    print("❌ ERROR: Environment Variables missing! Render panel me MONGO_URI, BOT_TOKEN, aur ADMIN_ID set karein.")
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
    except Exception as e:
        pass


# 3. /register - Group se hi naya account banana
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
            sent_msg = bot.reply_to(message, "❌ Is email se account pehle se bana hua hai.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        users_collection.insert_one({
            "email": email,
            "password": password,
            "role": "reseller",
            "credits": 0,
            "status": "inactive"
        })
        sent_msg = bot.reply_to(message, f"✅ **Account Created!**\n📧 Email: {email}\nAb isse `/activate` karein.")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=10)
    except Exception as e:
        pass


# 4. /activate - USER/EMAIL ACTIVATION (Deducts 100 credits)
@bot.message_handler(commands=['activate'])
def activate_user_account(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/activate [your_reseller_email] [target_user_email]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=6)
            return
            
        reseller_email = args[1].strip()
        target_email = args[2].strip()
        
        reseller = users_collection.find_one({"email": reseller_email})
        if not reseller:
            sent_msg = bot.reply_to(message, "❌ Reseller account nahi mila.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        reseller_credits = reseller.get('credits', 0)
        if reseller_credits < 100:
            sent_msg = bot.reply_to(message, f"❌ Insufficient Credits! Aapke paas {reseller_credits} credits hain. (Activation cost = 100 Credits)")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=6)
            return
            
        target_user = users_collection.find_one({"email": target_email})
        if not target_user:
            sent_msg = bot.reply_to(message, "❌ Jis User ko activate karna hai, wo registered nahi hai.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        if target_user.get('status') == "active":
            sent_msg = bot.reply_to(message, "ℹ️ Ye user account pehle se hi Active hai.")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return

        users_collection.update_one({"email": reseller_email}, {"$inc": {"credits": -100}})
        users_collection.update_one({"email": target_email}, {"$set": {"status": "active"}})
        
        sent_msg = bot.reply_to(message, f"🎉 **Activation Successful!**\n📧 **Activated Email:** {target_email}\n💰 100 Credits deducted from {reseller_email}.")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=12)
        
    except Exception as e:
        pass


# 5. /checkuser - Check if an email is active or inactive
@bot.message_handler(commands=['checkuser'])
def check_user_status(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/checkuser [email]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        email = args[1].strip()
        user = users_collection.find_one({"email": email})
        
        if user:
            status = user.get('status', 'inactive').upper()
            icon = "🟢" if status == "ACTIVE" else "🔴"
            sent_msg = bot.reply_to(message, f"{icon} **User Status:** {status}\n📧 Email: {email}")
        else:
            sent_msg = bot.reply_to(message, f"❌ Account not found in database.")
            
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=8)
    except Exception as e:
        pass


# 6. /addcredits - ADMIN ONLY
@bot.message_handler(commands=['addcredits'])
def add_credits(message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return
        
    try:
        args = message.text.split()
        if len(args) < 3:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/addcredits [email] [amount]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        email = args[1].strip()
        amount = int(args[2].strip())
        
        result = users_collection.update_one({"email": email}, {"$inc": {"credits": amount}})
        if result.matched_count > 0:
            sent_msg = bot.reply_to(message, f"✅ Added **{amount} credits** to {email}!")
        else:
            sent_msg = bot.reply_to(message, "❌ User nahi mila.")
            
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=8)
    except Exception as e:
        pass


# 7. /setrole - ADMIN ONLY
@bot.message_handler(commands=['setrole'])
def set_role(message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return
        
    try:
        args = message.text.split()
        if len(args) < 3:
            sent_msg = bot.reply_to(message, "⚠️ Format: `/setrole [email] [distributor/reseller]`")
            auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
            return
            
        email = args[1].strip()
        role = args[2].strip().lower()
        
        users_collection.update_one({"email": email}, {"$set": {"role": role}})
        sent_msg = bot.reply_to(message, f"⚙️ {email} ka role badal kar **{role.upper()}** kar diya gaya.")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=8)
    except Exception as e:
        pass


# 8. /stats - ADMIN ONLY
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        return
    
    total_users = users_collection.count_documents({})
    total_active = users_collection.count_documents({"status": "active"})
    
    stats_text = (
        "📊 **MdmKillerPro Database Stats**\n\n"
        f"👥 Total Accounts: {total_users}\n"
        f"🟢 Active Accounts: {total_active}"
    )
    sent_msg = bot.reply_to(message, stats_text)
    auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=15)


# 9. /cleanwelcome - Toggle logic for Welcomes
clean_welcome_status = {}
last_welcome_msg_id = {}

@bot.message_handler(commands=['cleanwelcome'])
def toggle_clean_welcome(message):
    args = message.text.split()
    if len(args) < 2:
        sent_msg = bot.reply_to(message, "⚠️ Use: `/cleanwelcome on` or `off`")
        auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)
        return
        
    status = args[1].strip().lower()
    clean_welcome_status[message.chat.id] = (status == "on")
    
    state = "ON" if clean_welcome_status[message.chat.id] else "OFF"
    sent_msg = bot.reply_to(message, f"🧹 **Clean Welcome is now {state}.**")
    auto_delete_messages(message.chat.id, [message.message_id, sent_msg.message_id], delay=5)


# --- Welcome Message Logic ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    chat_id = message.chat.id
    
    if clean_welcome_status.get(chat_id) and chat_id in last_welcome_msg_id:
        try:
            bot.delete_message(chat_id, last_welcome_msg_id[chat_id])
        except Exception:
            pass
            
    for member in message.new_chat_members:
        welcome_text = f"👋 Hey {member.first_name}, Welcome to **MdmKillerPro Official**!\n\nTool use karne ke liye `/menu` type karein."
        sent_msg = bot.send_message(chat_id, welcome_text)
        last_welcome_msg_id[chat_id] = sent_msg.message_id

print("MdmKillerPro Environment-Ready Bot is running...")
bot.infinity_polling()

