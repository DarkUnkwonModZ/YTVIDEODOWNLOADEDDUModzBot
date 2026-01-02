import os
import sys
import time
import asyncio
import yt_dlp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant

# --- CONFIGURATION ---
API_ID = 26490604  # আপনার নিজের API ID দিন (বিকল্প হিসেবে)
API_HASH = "8b63e18a9018e69d0563403f07a7a5a8" # আপনার API Hash
BOT_TOKEN = "8244995736:AAFW6yShu4r4hiSzMRu80PNOIwqZ2MAlgFw"
ADMIN_ID = 8504263842
LOG_CHANNEL = -1002345678901 # @dumodzbotmanager এর চ্যাট আইডি (নিচে অটো ডিটেক্ট করবে)
LOG_USERNAME = "dumodzbotmanager"
REQUIRED_CHANNEL = "DemoTestDUModz"
LOGO_URL = "https://raw.githubusercontent.com/DarkUnkwonModZ/Blogger-DarkUnkownModZ-Appinfo/refs/heads/main/IMG/dumodz-logo-final.png"

app = Client("YT_DL_BOT", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def edit_animation(message, text_list):
    """টেক্সট রিমুভ না হয়ে মোডিফাই হওয়ার এনিমেশন"""
    for text in text_list:
        try:
            await message.edit_text(text)
            await asyncio.sleep(0.5)
        except:
            pass

async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(REQUIRED_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except Exception:
        return True

# --- LOGGING ---
async def send_log(text):
    try:
        await app.send_message(LOG_USERNAME, f"🚀 **SYSTEM LOG:**\n\n{text}")
    except:
        pass

# --- PROGRESS HOOK ---
def progress_bar(current, total, message, start_time):
    # টেলিগ্রাম রেট লিমিট এড়াতে ৩ সেকেন্ড পর পর আপডেট
    now = time.time()
    if now - start_time < 3:
        return
    
    percentage = current * 100 / total
    completed = int(percentage / 10)
    bar = "█" * completed + "░" * (10 - completed)
    
    try:
        message.edit_text(f"📥 Downloading...\n\n`[{bar}]` {percentage:.1f}%")
    except:
        pass

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    user_id = message.from_user.id
    
    # Force Join Check
    if not await is_subscribed(client, user_id):
        buttons = [
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL}")],
            [InlineKeyboardButton("🔄 Joined & Verify", callback_data="check_sub")]
        ]
        return await message.reply_photo(
            photo=LOGO_URL,
            caption="⚠️ **অ্যাক্সেসDenied!**\nবটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Welcome Animation
    msg = await message.reply("⚡ Initializing...")
    await edit_animation(msg, [
        "⌛ Processing System...",
        "💎 Advanced Modules Loading...",
        "✅ System Ready!"
    ])
    
    welcome_text = (
        f"👋 **Welcome {message.from_user.mention}!**\n\n"
        "আমি **Dark Unkwon ModZ** ইউটিউব ডাউনলোডার বট। "
        "যেকোনো ভিডিওর লিঙ্ক দিন আমি সেটি ডাউনলোড করে দিবো।"
    )
    
    buttons = [
        [InlineKeyboardButton("🌐 Website", url="https://darkunkwonmodz.blogspot.com")],
        [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{REQUIRED_CHANNEL}")],
        [InlineKeyboardButton("🛠 Developer", url="https://t.me/DarkUnkwon")]
    ]
    
    await msg.delete()
    await message.reply_photo(
        photo=LOGO_URL,
        caption=welcome_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await send_log(f"👤 User {message.from_user.first_name} started the bot.")

@app.on_callback_query(filters.regex("check_sub"))
async def check_sub_cb(client, callback_query):
    if await is_subscribed(client, callback_query.from_user.id):
        await callback_query.answer("✅ Verification Success!", show_alert=True)
        await start_cmd(client, callback_query.message)
    else:
        await callback_query.answer("❌ আপনি এখনো জয়েন করেননি!", show_alert=True)

@app.on_message(filters.text & filters.private)
async def handle_download(client, message):
    url = message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        return await message.reply("❌ এটি সঠিক ইউটিউব লিঙ্ক নয় বন্ধু!")

    # Check Sub
    if not await is_subscribed(client, message.from_user.id):
        return await message.reply("❌ আগে চ্যানেলে জয়েন করুন!")

    msg = await message.reply("🔍 **ভিডিও তথ্য সংগ্রহ করছি...**")
    
    buttons = [
        [InlineKeyboardButton("🎬 Video (MP4)", callback_data=f"vid_{url}")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"aud_{url}")]
    ]
    
    await msg.edit_text("কিভাবে ডাউনলোড করতে চান বন্ধু?", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^(vid|aud)_"))
async def download_trigger(client, callback_query):
    type, url = callback_query.data.split("_", 1)
    await callback_query.message.edit_text("⏳ **ডাউনলোড শুরু হচ্ছে...**")
    
    file_path = f"download_{time.time()}"
    ydl_opts = {
        'format': 'best' if type == "vid" else 'bestaudio/best',
        'outtmpl': f"{file_path}.%(ext)s",
        'noplaylist': True,
    }

    if type == "aud":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if type == "aud": filename = filename.rsplit('.', 1)[0] + ".mp3"

        await callback_query.message.edit_text("📤 **ফাইল আপলোড হচ্ছে...**")
        
        if type == "vid":
            await client.send_video(callback_query.message.chat.id, video=filename, caption=f"✅ **Title:** {info['title']}\n\n🔥 Powered By @{REQUIRED_CHANNEL}")
        else:
            await client.send_audio(callback_query.message.chat.id, audio=filename, caption=f"✅ **Title:** {info['title']}\n\n🔥 Powered By @{REQUIRED_CHANNEL}")
        
        os.remove(filename)
        await callback_query.message.delete()

    except Exception as e:
        await callback_query.message.edit_text(f"❌ এরর: {str(e)}")

# --- ADMIN COMMANDS ---

@app.on_message(filters.command("restart") & filters.user(ADMIN_ID))
async def restart_bot(client, message):
    await message.reply("🔄 **বট রিস্টার্ট হচ্ছে...**")
    await send_log("🔄 Admin manually restarted the bot.")
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(client, message):
    await message.reply(f"📊 **Bot Status:** Online\n🛡 **Admin:** @DarkUnkwon\n⚙ **Platform:** GitHub Actions")

# --- AUTO RESTART TIMER ---
async def auto_restart():
    await asyncio.sleep(14400) # ৪ ঘণ্টা (৪ * ৩৬০০ সেকেন্ড)
    await send_log("⏰ 4 Hours completed. Auto-restarting system...")
    os.execl(sys.executable, sys.executable, *sys.argv)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(auto_restart())
    print("Bot is running...")
    app.run()
