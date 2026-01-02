import os
import time
import yt_dlp
import telebot
from telebot import types

# --- CONFIGURATION ---
TOKEN = "8244995736:AAFW6yShu4r4hiSzMRu80PNOIwqZ2MAlgFw"
ADMIN_ID = 8504263842
LOG_CHANNEL = "@dumodzbotmanager"
REQUIRED_CHANNEL = "@DemoTestDUModz" 
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN)

# --- LOGGING FUNCTION ---
def log_to_channel(user, action):
    try:
        log_text = (
            f"🔔 #LOG_UPDATE\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"⚡ **Action:** {action}\n"
            f"🕒 **Time:** {time.ctime()}"
        )
        bot.send_message(LOG_CHANNEL, log_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Log Error: {e}")

# --- UI ANIMATION HELPER ---
def edit_msg(chat_id, message_id, text, reply_markup=None):
    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        pass

# --- CHECK JOIN ---
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(REQUIRED_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return True # যদি বট চ্যানেলে এডমিন না থাকে তবে সমস্যা এড়াতে True

# --- PROGRESS HOOK ---
class ProgressHook:
    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_update = 0

    def hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            s = d.get('_speed_str', '0KB/s')
            # প্রতি ৫ সেকেন্ড পর পর আপডেট দিবে ফ্লাড এড়াতে
            if time.time() - self.last_update > 5:
                edit_msg(self.chat_id, self.message_id, f"📥 **Downloading Media...**\n\n📊 **Progress:** `{p}`\n⚡ **Speed:** `{s}`")
                self.last_update = time.time()

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    if not is_subscribed(user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify & Start", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, 
                       caption=f"👋 **Hello {user.first_name}!**\n\nYou must join our channel to use this premium tool.", 
                       reply_markup=markup)
        return

    # Welcome Animation Effect
    sent = bot.send_message(message.chat.id, "⚡")
    frames = ["🔍 *Checking System...*", "🚀 *System Ready!*", f"🔥 *WELCOME TO DARK UNKWON MODZ v2.0*"]
    for f in frames:
        edit_msg(message.chat.id, sent.message_id, f)
        time.sleep(0.5)

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌐 Website", url=WEBSITE_URL),
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@','')}")
    )
    
    welcome_text = (
        f"👤 **Name:** {user.first_name}\n"
        f"🆔 **Your ID:** `{user.id}`\n\n"
        f"📥 **Send me a YouTube Link to start downloading!**"
    )
    edit_msg(message.chat.id, sent.message_id, welcome_text, reply_markup=markup)
    log_to_channel(user, "Started the Bot")

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified Successfully!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def link_handler(message):
    if not is_subscribed(message.from_user.id):
        start(message)
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"mp4|{message.text}"),
        types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"mp3|{message.text}")
    )
    bot.reply_to(message, "⚙️ **Choose Download Format:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("mp4|", "mp3|")))
def download_logic(call):
    mode, url = call.data.split("|")
    chat_id = call.message.chat.id
    
    msg = bot.edit_message_text("🔄 **Processing... Please Wait.**", chat_id, call.message.message_id, parse_mode="Markdown")
    
    log_to_channel(call.from_user, f"Requested {mode} download")

    if not os.path.exists('downloads'): os.makedirs('downloads')
    file_path = f"downloads/{chat_id}_{int(time.time())}.%(ext)s"

    ydl_opts = {
        'progress_hooks': [ProgressHook(chat_id, msg.message_id).hook],
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True
    }

    if mode == "mp3":
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
            if mode == "mp3": filename = filename.rsplit(".", 1)[0] + ".mp3"

        edit_msg(chat_id, msg.message_id, "📤 **Uploading to Telegram...**")
        
        with open(filename, 'rb') as f:
            if mode == "mp4":
                bot.send_video(chat_id, f, caption=f"✅ **Downloaded:** {info['title']}\n\n🚀 @DarkUnkwonModZ")
            else:
                bot.send_audio(chat_id, f, caption=f"✅ **Converted:** {info['title']}\n\n🚀 @DarkUnkwonModZ")
        
        os.remove(filename)
        bot.delete_message(chat_id, msg.message_id)
        log_to_channel(call.from_user, f"Successfully downloaded: {info['title']}")

    except Exception as e:
        edit_msg(chat_id, msg.message_id, f"❌ **Error:** `{str(e)[:100]}`")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['restart'])
def restart(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "🔄 **Restarting Bot...**")
        log_to_channel(message.from_user, "Bot Manual Restart Triggered")
        os._exit(0)

print("Bot is running...")
bot.infinity_polling()
