import os
import time
import yt_dlp
import telebot
from telebot import types
import sys

# --- CONFIGURATION ---
TOKEN = "8244995736:AAFW6yShu4r4hiSzMRu80PNOIwqZ2MAlgFw"
ADMIN_ID = 8504263842
LOG_CHANNEL = "-1002345678901" # @dumodzbotmanager এর Chat ID দিন অথবা ইউজারনেম
FORCE_CHANNEL = "@DemoTestDUModz"
CHANNEL_URL = "https://t.me/DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN)

# --- HELPER FUNCTIONS ---

def send_log(text):
    """লগ চ্যানেলে আপডেট পাঠানোর ফাংশন"""
    try:
        bot.send_message("@dumodzbotmanager", f"🚀 **[SYSTEM LOG]**\n\n{text}", parse_mode="Markdown")
    except: pass

def check_join(user_id):
    """ইউজার চ্যানেলে আছে কি না চেক করার ফাংশন"""
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def animated_edit(chat_id, message_id, text_list, final_markup=None):
    """টেক্সট মোডিফাই বা এডিট এনিমেশন ফাংশন"""
    for text in text_list:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=final_markup, disable_web_page_preview=True)
            time.sleep(0.7)
        except: continue

# --- PROGRESS HOOK ---
class ProgressTracker:
    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_update = 0

    def hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            s = d.get('_speed_str', '0KB/s')
            t = d.get('_total_bytes_str', 'Unknown')
            
            if time.time() - self.last_update > 4:
                bar = p.replace('%', '')
                try:
                    fill = int(float(bar) // 10)
                    progress_bar = "█" * fill + "░" * (10 - fill)
                    bot.edit_message_text(
                        f"⚡ **Downloading File...**\n\n`[{progress_bar}]` {p}\n🚀 Speed: `{s}`\n📦 Total: `{t}`",
                        self.chat_id, self.message_id, parse_mode="Markdown"
                    )
                    self.last_update = time.time()
                except: pass

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user = message.from_user
    if not check_join(user.id):
        # Force Join Screen
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        markup.add(types.InlineKeyboardButton("✅ Verify Joining", callback_data="verify"))
        
        bot.send_photo(message.chat.id, LOGO, caption=f"⚠️ **Access Denied!**\n\nHey {user.first_name}, you must join our channel to use this premium tool.", reply_markup=markup)
        return

    # Welcome Sequence with Animation
    msg = bot.send_message(message.chat.id, "🔍 `Checking status...`", parse_mode="Markdown")
    
    text_frames = [
        "⚡ `Bypassing Restrictions...`",
        "✅ `Access Granted!`",
        "🔥 **WELCOME TO DARK UNKWON MODZ**"
    ]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Channel", url=CHANNEL_URL),
        types.InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)
    )
    
    animated_edit(message.chat.id, msg.message_id, text_frames, final_markup=markup)
    send_log(f"👤 User: {user.first_name} (@{user.username})\n🆔 ID: `{user.id}`\n✅ Started the bot.")

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_user(call):
    if check_join(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified! You can use the bot now.", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Join the channel first!", show_alert=True)

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_yt(message):
    if not check_join(message.from_user.id): return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{message.text}"),
        types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{message.text}")
    )
    bot.reply_to(message, "✨ **Select Quality Format:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: "|" in call.data)
def download_now(call):
    type, url = call.data.split("|")
    chat_id = call.message.chat.id
    msg = bot.edit_message_text("🔄 **Processing Request...**", chat_id, call.message.message_id, parse_mode="Markdown")
    
    if not os.path.exists('downloads'): os.makedirs('downloads')
    output_path = f"downloads/{chat_id}_{int(time.time())}.%(ext)s"

    ydl_opts = {
        'progress_hooks': [ProgressTracker(chat_id, msg.message_id).hook],
        'outtmpl': output_path,
        'quiet': True
    }

    if type == "aud":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        ydl_opts.update({'format': 'best[ext=mp4]'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == "aud": filename = filename.rsplit(".", 1)[0] + ".mp3"

        bot.edit_message_text("📤 **Uploading to Telegram...**", chat_id, msg.message_id, parse_mode="Markdown")
        
        with open(filename, 'rb') as f:
            if type == "vid":
                bot.send_video(chat_id, f, caption=f"✅ **Downloaded:** {info['title']}\n🚀 @DarkUnkwonModZ")
            else:
                bot.send_audio(chat_id, f, caption=f"✅ **Converted:** {info['title']}\n🚀 @DarkUnkwonModZ")
        
        os.remove(filename)
        bot.delete_message(chat_id, msg.message_id)
        send_log(f"🎬 **Download Success**\nUser: {call.from_user.first_name}\nTitle: {info['title']}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Error:** `{str(e)}`", chat_id, msg.message_id)

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID: return
    bot.reply_to(message, "👑 **Admin Panel**\n\n/restart - Manual Reboot\n/stats - Bot Status\n/broadcast - Message Users")

@bot.message_handler(commands=['restart'])
def reboot(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🔄 `System Rebooting...`")
        send_log("⚠️ Bot is restarting...")
        os._exit(0)

# --- INITIALIZE ---
if __name__ == "__main__":
    send_log("✅ Bot is now Online and Monitoring 24/7.")
    print("Bot Running...")
    bot.infinity_polling()
