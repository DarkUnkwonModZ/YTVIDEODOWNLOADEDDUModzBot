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
FORCE_CHANNEL = "@DemoTestDUModz"
WEBSITE_URL = "https://darkunkwonmodz.blogspot.com"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

bot = telebot.TeleBot(TOKEN)

# --- HELPER FUNCTIONS ---

def send_log(message_text):
    """লগ চ্যানেলে বিস্তারিত তথ্য পাঠায়"""
    try:
        log_msg = f"🛰 **[SYSTEM LOG UPDATE]**\n" + message_text
        bot.send_message(LOG_CHANNEL, log_msg, parse_mode="Markdown")
    except:
        pass

def check_subscription(user_id):
    """ইউজার চ্যানেলে সাবস্ক্রাইব করা কি না চেক করে"""
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return False

def animated_edit(chat_id, message_id, text_list, final_markup=None):
    """মেসেজ এডিট করে এনিমেশন তৈরি করে"""
    for text in text_list:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=final_markup)
            time.sleep(0.6)
        except:
            continue

# --- PROGRESS BAR HOOK ---

class ProgressHook:
    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_update_time = 0

    def hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%')
            s = d.get('_speed_str', '0KB/s')
            t = d.get('_total_bytes_str', 'Unknown')
            
            # ৪ সেকেন্ড পর পর এডিট (ফ্লাড লিমিট এড়াতে)
            if time.time() - self.last_update_time > 4:
                try:
                    bar_val = p.replace('%', '').strip()
                    filled = int(float(bar_val) // 10)
                    bar = "█" * filled + "░" * (10 - filled)
                    text = f"⚡ **Downloading Premium Content**\n\n`[{bar}]` {p}\n🚀 Speed: `{s}`\n📦 Size: `{t}`"
                    bot.edit_message_text(text, self.chat_id, self.message_id, parse_mode="Markdown")
                    self.last_update_time = time.time()
                except: pass

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user = message.from_user
    chat_id = message.chat.id
    
    send_log(f"👤 **User:** {user.first_name}\n🆔 **ID:** `{user.id}`\n🌐 **Action:** /start")

    if not check_subscription(user.id):
        # Verification Screen
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("✅ Verify Joining", callback_data="verify_join"))
        
        bot.send_photo(chat_id, LOGO_URL, caption=f"⚠️ **Access Restricted!**\n\n👋 Hello {user.first_name}!\n\nTo use **Dark Unkwon ModZ** premium features, you must join our channel first.", reply_markup=markup)
        return

    # If already verified
    show_welcome(chat_id, user.first_name)

def show_welcome(chat_id, name):
    msg = bot.send_message(chat_id, "🔍 `System Checking...`", parse_mode="Markdown")
    
    # Animation frames
    frames = [
        "🌐 `Connecting to Server...`",
        "🔓 `Accessing Premium Database...`",
        "✅ `Verification Successful!`"
    ]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 Channel", url=f"https://t.me/{FORCE_CHANNEL.replace('@','')}"),
        types.InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)
    )
    
    animated_edit(chat_id, msg.message_id, frames)
    
    welcome_text = (
        f"🔥 **WELCOME TO DARK UNKWON MODZ** 🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {name}\n"
        f"🛠 **Status:** `Premium Active`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"আমি আপনাকে ইউটিউব ভিডিও এবং অডিও সর্বোচ্চ কোয়ালিটিতে ডাউনলোড করে দিতে পারি।\n\n"
        f"👇 **Send me a YouTube URL to start!**"
    )
    bot.edit_message_text(welcome_text, chat_id, msg.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_btn(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified! Welcome to the premium club.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_welcome(call.message.chat.id, call.from_user.first_name)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_youtube_link(message):
    if not check_subscription(message.from_user.id):
        start_cmd(message)
        return
    
    url = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid|{url}"),
        types.InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud|{url}")
    )
    bot.reply_to(message, "🎞 **Choose your desired format:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: "|" in call.data)
def download_process(call):
    mode, url = call.data.split("|")
    chat_id = call.message.chat.id
    
    msg = bot.edit_message_text("🔄 `Initializing Download Engine...`", chat_id, call.message.message_id, parse_mode="Markdown")
    
    send_log(f"🎬 **Download Request**\n👤 **From:** {call.from_user.first_name}\n📂 **Type:** {mode}\n🔗 **Link:** {url}")

    if not os.path.exists('downloads'): os.makedirs('downloads')
    filename_format = f"downloads/%(title)s_{int(time.time())}.%(ext)s"

    ydl_opts = {
        'progress_hooks': [ProgressHook(chat_id, msg.message_id).hook],
        'outtmpl': filename_format,
        'quiet': True,
        'no_warnings': True
    }

    if mode == "aud":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })
    else:
        ydl_opts.update({'format': 'best[ext=mp4]'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if mode == "aud": file_path = file_path.rsplit(".", 1)[0] + ".mp3"

        bot.edit_message_text("📤 `Uploading to Telegram...`", chat_id, msg.message_id, parse_mode="Markdown")
        
        with open(file_path, 'rb') as f:
            if mode == "vid":
                bot.send_video(chat_id, f, caption=f"✅ **Success:** {info['title']}\n🚀 @DarkUnkwonModZ")
            else:
                bot.send_audio(chat_id, f, caption=f"✅ **Success:** {info['title']}\n🚀 @DarkUnkwonModZ")
        
        os.remove(file_path)
        bot.delete_message(chat_id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Error:** `{str(e)[:100]}`", chat_id, msg.message_id)

# --- ADMIN PANEL ---

@bot.message_handler(commands=['admin'], func=lambda m: m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Stats", "🔄 Restart Bot", "📢 Broadcast")
    bot.reply_to(message, "👑 **Welcome Admin Dark Unknown!**\nControl panel activated.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔄 Restart Bot" and m.from_user.id == ADMIN_ID)
def manual_restart(message):
    bot.reply_to(message, "⚙️ `System Rebooting... Process will resume in GitHub Actions.`")
    send_log("⚠️ **Bot Restarted Manually by Admin**")
    os._exit(0)

# --- KEEP ALIVE ---
if __name__ == "__main__":
    send_log(f"✅ **Bot Online & 24/7 Service Started**\n🤖 **Token:** `{TOKEN[:15]}...`\n👑 **Admin:** @DarkUnkwon")
    print("Bot is running...")
    bot.infinity_polling()
