import os
import time
import yt_dlp
import telebot
from telebot import types
import threading

# --- CONFIGURATION ---
TOKEN = "8244995736:AAFW6yShu4r4hiSzMRu80PNOIwqZ2MAlgFw"
ADMIN_ID = 8504263842
LOG_CHANNEL = "@dumodzbotmanager"
REQUIRED_CHANNEL = "@DemoTestDUModz" # @ চিহ্ন সহ চ্যানেলের ইউজারনেম
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN)

# --- UI ANIMATION HELPER ---
def edit_msg(message, text, reply_markup=None):
    try:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=reply_markup, parse_mode="Markdown")
    except:
        pass

def animated_loader(message, final_text):
    frames = ["🔍 Scanning Link...", "⚡ Connecting Server...", "📥 Fetching Media...", "🚀 Ready to Process!"]
    for frame in frames:
        edit_msg(message, f"*{frame}*")
        time.sleep(0.8)
    edit_msg(message, final_text)

# --- CHECK JOIN ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- PROGRESS HOOK FOR TELEGRAM ---
class ProgressHook:
    def __init__(self, message):
        self.message = message
        self.last_update = 0

    def hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            s = d.get('_speed_str', '0KB/s')
            t = d.get('_total_bytes_str', 'Unknown')
            
            # ৪ সেকেন্ড পর পর মেসেজ আপডেট হবে (Telegram Flood Limit এড়াতে)
            if time.time() - self.last_update > 4:
                try:
                    edit_msg(self.message, f"*📥 Downloading...*\n\n📊 Progress: `{p}`\n⚡ Speed: `{s}`\n📦 Size: `{t}`")
                    self.last_update = time.time()
                except: pass

# --- HANDLERS ---

@bot.message_status_handler()
def log_activity(msg, action):
    log_text = f"#LOG\n👤 User: {msg.from_user.first_name}\n🆔 ID: {msg.chat.id}\n⚡ Action: {action}"
    bot.send_message(LOG_CHANNEL, log_text)

@bot.message_handler(commands=['start'])
def start(message):
    if not is_subscribed(message.chat.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption=f"👋 Hello {message.from_user.first_name}!\n\nYou must join our channel to use this bot.", reply_markup=markup)
        return

    welcome_msg = bot.send_message(message.chat.id, "♻️ *Initializing System...*")
    time.sleep(1)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌐 Website", url=WEBSITE_URL),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    
    final_text = (
        f"🔥 *WELCOME TO DARK UNKWON MODZ v2.0*\n\n"
        f"I can download YouTube videos and audio in high quality.\n\n"
        f"🔗 *Just send me any YouTube link!*"
    )
    edit_msg(welcome_msg, final_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    if is_subscribed(call.message.chat.id):
        bot.answer_callback_query(call.id, "✅ Verified! Welcome.")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Please join first!", show_alert=True)

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_link(message):
    if not is_subscribed(message.chat.id): return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{message.text}"),
        types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{message.text}")
    )
    bot.reply_to(message, "🎞 *Select Download Format:*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("vid|", "aud|")))
def download_process(call):
    type, url = call.data.split("|")
    msg = bot.edit_message_text("⚙️ *Processing Your Request...*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    
    log_activity(call.message, f"Downloading {type} from {url}")

    # File paths
    out_tmpl = f"downloads/{call.message.chat.id}_{int(time.time())}.%(ext)s"
    if not os.path.exists('downloads'): os.makedirs('downloads')

    ydl_opts = {
        'progress_hooks': [ProgressHook(msg).hook],
        'outtmpl': out_tmpl,
        'quiet': True
    }

    if type == "aud":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        })
    else:
        ydl_opts.update({'format': 'best[ext=mp4]'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == "aud": filename = filename.rsplit(".", 1)[0] + ".mp3"

        edit_msg(msg, "📤 *Uploading to Telegram...*")
        with open(filename, 'rb') as f:
            if type == "vid":
                bot.send_video(call.message.chat.id, f, caption=f"✅ *Success:* {info['title']}\n@DarkUnkwonModZ", parse_mode="Markdown")
            else:
                bot.send_audio(call.message.chat.id, f, caption=f"✅ *Success:* {info['title']}\n@DarkUnkwonModZ", parse_mode="Markdown")
        
        os.remove(filename)
        bot.delete_message(call.message.chat.id, msg.message_id)

    except Exception as e:
        edit_msg(msg, f"❌ *Error:* {str(e)}")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID: return
    bot.reply_to(message, "👑 *Welcome Admin Dark Unknown*\n\n/stats - Check Stats\n/broadcast - Send message to all users\n/restart - Restart Bot")

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    if message.chat.id == ADMIN_ID:
        bot.reply_to(message, "🔄 *Restarting...*")
        bot.send_message(LOG_CHANNEL, "⚠️ Bot is restarting manually by Admin.")
        os._exit(0)

# --- KEEP ALIVE ---
bot.send_message(LOG_CHANNEL, "🚀 **Bot is Online & 24/7 Monitoring Active**")
print("Bot is running...")
bot.infinity_polling()
