import telebot
import json
import os
import base64
import time

TOKEN = "8772869279:AAEu5CEhxUGxOcrv_btL1RqNDmnSMbL6U3Y"
ADMIN_ID = 8758830915

bot = telebot.TeleBot(TOKEN)

DB_FILE = "files.json"

CHANNEL_USERNAME = "@Burmese_Anime"
CHANNEL_LINK = "https://t.me/Burmese_Anime"

if os.path.exists(DB_FILE):

    with open(DB_FILE, "r", encoding="utf-8") as f:

        files_db = json.load(f)

else:

    files_db = {}

def save_db():

    with open(DB_FILE, "w", encoding="utf-8") as f:

        json.dump(
            files_db,
            f,
            indent=4,
            ensure_ascii=False
        )

def normalize(text):

    return (
        text.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )

def encode_data(text):

    return base64.urlsafe_b64encode(
        text.encode()
    ).decode()

def decode_data(text):

    return base64.urlsafe_b64decode(
        text.encode()
    ).decode()

def is_joined(user_id):

    try:

        member = bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception as e:

        print(f"Join Check Error: {e}")
        return False

def join_message(chat_id):

    bot.send_message(
        chat_id,
        f"""
❌ Please Join Channel First

📢 {CHANNEL_LINK}

ပြီးမှ Bot ကိုပြန်သုံးပါ။
"""
    )

def fast_send(chat_id, data):

    caption = data.get("caption", "")

    try:

        if data["type"] == "document":

            bot.send_document(
                chat_id,
                data["file_id"],
                caption=caption,
                disable_content_type_detection=True,
                timeout=120
            )

        elif data["type"] == "video":

            bot.send_video(
                chat_id,
                data["file_id"],
                caption=caption,
                supports_streaming=True,
                timeout=120
            )

        elif data["type"] == "audio":

            bot.send_audio(
                chat_id,
                data["file_id"],
                caption=caption,
                timeout=120
            )

        bot.send_message(
            chat_id,
            f"""
✅ File Sent Successfully

🎬 Thank You For Using Our Anime Bot

📢 Channel
{CHANNEL_LINK}
"""
        )

    except Exception as e:

        print(f"❌ Send Error: {e}")

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if not is_joined(user_id):

        join_message(message.chat.id)
        return

    args = message.text.split(maxsplit=1)

    if len(args) > 1:

        try:

            keyword = decode_data(args[1])

        except Exception as e:

            print(e)

            bot.send_message(
                message.chat.id,
                "❌ Invalid Link"
            )

            return

        keyword = normalize(keyword)

        found = False

        for file_id, data in files_db.items():

            anime_name = normalize(data["name"])

            if keyword in anime_name or anime_name in keyword:

                found = True

                fast_send(
                    message.chat.id,
                    data
                )

        if not found:

            bot.send_message(
                message.chat.id,
                "❌ Anime Not Found"
            )

        return

    bot.send_message(
        message.chat.id,
        f"""
🎬 Anime Bot

📢 Join Channel
{CHANNEL_LINK}
"""
    )

@bot.message_handler(
    content_types=['document', 'video', 'audio']
)
def upload_file(message):

    if message.from_user.id != ADMIN_ID:

        bot.reply_to(
            message,
            "❌ Only admin can upload."
        )

        return

    file_unique = str(message.message_id)

    caption_text = (
        message.caption
        if message.caption else ""
    )

    if message.document:

        file_id = message.document.file_id

        file_name = (
            message.caption
            if message.caption else
            message.document.file_name
        )

        file_type = "document"

    elif message.video:

        file_id = message.video.file_id

        file_name = (
            message.caption
            if message.caption else
            "AnimeVideo"
        )

        file_type = "video"

    elif message.audio:

        file_id = message.audio.file_id

        file_name = (
            message.caption
            if message.caption else
            "AnimeAudio"
        )

        file_type = "audio"

    files_db[file_unique] = {

        "file_id": file_id,
        "name": file_name,
        "type": file_type,
        "caption": caption_text

    }

    save_db()

    bot_username = bot.get_me().username

    anime_only = file_name

    if "ep" in anime_only.lower():

        anime_only = (
            anime_only.lower()
            .split("ep")[0]
            .strip()
        )

    encoded = encode_data(
        normalize(anime_only)
    )

    link = (
        f"https://t.me/"
        f"{bot_username}?start={encoded}"
    )

    bot.reply_to(
        message,
        f"""
✅ ANIME SAVED

🎬 {file_name}

🆔 {file_unique}
"""
    )

    bot.send_message(
        message.chat.id,
        link
    )

@bot.message_handler(commands=['delete'])
def delete_file(message):

    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()

    if len(args) < 2:

        bot.reply_to(
            message,
            "Usage:\n/delete ID"
        )

        return

    file_key = args[1]

    if file_key not in files_db:

        bot.reply_to(
            message,
            "❌ File not found."
        )

        return

    del files_db[file_key]

    save_db()

    bot.reply_to(
        message,
        "✅ Deleted"
    )

@bot.message_handler(commands=['deleteall'])
def delete_all(message):

    if message.from_user.id != ADMIN_ID:
        return

    files_db.clear()

    save_db()

    bot.reply_to(
        message,
        "✅ All Files Deleted."
    )

@bot.message_handler(commands=['delname'])
def delete_by_name(message):

    if message.from_user.id != ADMIN_ID:
        return

    anime_name = (
        message.text.replace("/delname ", "")
        .lower()
    )

    if not anime_name:

        bot.reply_to(
            message,
            "Usage:\n/delname anime name"
        )

        return

    deleted = 0

    all_files = list(files_db.items())

    for file_id, data in all_files:

        saved_name = data["name"].lower()

        if anime_name in saved_name:

            del files_db[file_id]

            deleted += 1

    save_db()

    if deleted > 0:

        bot.reply_to(
            message,
            f"✅ Deleted {deleted} Files."
        )

    else:

        bot.reply_to(
            message,
            "❌ File not found."
        )

print("🤖 Anime Bot Running...")

while True:

    try:

        bot.infinity_polling(
            skip_pending=True,
            timeout=60,
            long_polling_timeout=60
        )

    except Exception as e:

        print(f"❌ Error: {e}")

        time.sleep(5)