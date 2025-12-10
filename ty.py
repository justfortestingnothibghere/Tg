import telebot
import threading
import os
import shutil
import zipfile
import requests
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup
from pathlib import Path
import time
import logging
from datetime import datetime, date
import json

# ================= CONFIG =================
TOKEN = "7913272382:AAGnvD29s4bu_jmsejNmT5eWbl7HZnGy_OM"
bot = telebot.TeleBot(TOKEN)

# YOUR TELEGRAM ID (ADMIN)
ADMIN_ID = 8163739723  # ← APNA ID YAHAN DAALO!!!

DB_FILE = "users.json"
DEFAULT_DAILY_LIMIT = 2
MAX_SIZE_MB = 45
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}

active_tasks = {}

# =============== JSON DB ===============
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def get_user_data(user_id):
    db = load_db()
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            "accepted_tc": False,
            "daily_used": 0,
            "last_date": None,
            "custom_limit": DEFAULT_DAILY_LIMIT
        }
        save_db(db)
    return db[user_id]

def user_accepted_tc(user_id):
    return get_user_data(user_id).get("accepted_tc", False)

def accept_tc(user_id):
    user_id = str(user_id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {}
    db[user_id]["accepted_tc"] = True
    save_db(db)

def reset_daily_if_needed(user_id):
    user_id = str(user_id)
    data = get_user_data(user_id)
    today = date.today().isoformat()
    
    if data.get("last_date") != today:
        data["daily_used"] = 0
        data["last_date"] = today
        db = load_db()
        db[user_id].update(data)
        save_db(db)
    
    return data

def increment_usage(user_id):
    user_id = str(user_id)
    data = reset_daily_if_needed(user_id)
    data["daily_used"] += 1
    db = load_db()
    db[user_id].update(data)
    save_db(db)

def set_user_limit(user_id, new_limit):
    user_id = str(user_id)
    db = load_db()
    if user_id not in db:
        db[user_id] = {"accepted_tc": True}
    db[user_id]["custom_limit"] = new_limit
    save_db(db)

# =============== T&C MESSAGE ===============
def send_tc_message(chat_id, user_id):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("I Aᴄᴄᴇᴘᴛ T&C & Pʀɪᴠᴀᴄʏ Pᴏʟɪᴄʏ", callback_data="accept_tc"))
    markup.add(telebot.types.InlineKeyboardButton("Cancel", callback_data="cancel_tc"))

    tc_text = (
        "⚜️ T&C | Pʀɪᴠᴀᴄʏ Pᴏʟɪᴄʏ 👮‍♀️\n\n"
        "Bʏ Usɪɴɢ Tʜɪs Bᴏᴛ, Yᴏᴜ Aɢʀᴇᴇ Tᴏ Tʜᴇ Fᴏʟʟᴏᴡɪɴɢ:\n\n"
        "1. Yᴏᴜ Wɪʟʟ Oɴʟʏ Mɪʀʀᴏʀ Pᴜʙʟɪᴄ Wᴇʙsɪᴛᴇs (ɴᴏ ʟᴏɢɪɴ, ɴᴏ ᴘʀɪᴠᴀᴛᴇ ᴅᴀᴛᴀ)\n"
        "2. Yᴏᴜ Wɪʟʟ Nᴏᴛ Usᴇ Tʜɪs Bᴏᴛ Fᴏʀ Iʟʟᴇɢᴀʟ Aᴄᴛɪᴠɪᴛɪᴇs\n"
        "3. Wᴇ Dᴏ Nᴏᴛ Sᴛᴏʀᴇ Aɴʏ Pᴇʀsᴏɴᴀʟ Dᴀᴛᴀ Exᴄᴇᴘᴛ Yᴏᴜʀ Tᴇʟᴇɢʀᴀᴍ ID & Usᴀɢᴇ Cᴏᴜɴᴛ\n"
        "4. Dᴏᴡɴʟᴏᴀᴅᴇᴅ Wᴇʙsɪᴛᴇs Aʀᴇ Tᴇᴍᴘᴏʀᴀʀɪʟʏ Sᴀᴠᴇᴅ Aɴᴅ Dᴇʟᴇᴛᴇᴅ Aғᴛᴇʀ Dᴇʟɪᴠᴇʀʏ\n"
        "5. Mᴀx Fɪʟᴇ Sɪᴢᴇ: 45MB (Tᴇʟᴇɢʀᴀᴍ ʟɪᴍɪᴛ)\n"
        "6. Dᴀɪʟʏ Lɪᴍɪᴛ: 2 Wᴇʙsɪᴛᴇs (ᴄᴀɴ ʙᴇ ɪɴᴄʀᴇᴀsᴇᴅ ʙʏ ᴀᴅᴍɪɴ)\n\n"
        "Yᴏᴜʀ Dᴀᴛᴀ Is Sᴀғᴇ | Nᴏ Lᴏɢs | Fᴜʟʟʏ Pʀɪᴠᴀᴛᴇ\n\n"
        "Made with ❤️ by @MR_ARMAN_08"
    )

    photo = "https://graph.org/file/6bdddbc4b335597a86632-bbfc6792edbf4e2b21.jpg"  # ← YAHAN APNI T&C IMAGE DAALO

    bot.send_photo(
        chat_id,
        photo,
        caption=tc_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

# =============== CALLBACK HANDLER ===============
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "accept_tc":
        accept_tc(call.from_user.id)
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="Aᴄᴄᴇᴘᴛᴇᴅ! Nᴏᴡ Yᴏᴜ Cᴀɴ Usᴇ Tʜᴇ Bᴏᴛ!\n\nSend /start",
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "Accepted! Welcome!")
    
    elif call.data == "cancel_tc":
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="Yoᥙ Dᥱᥴᥣιnᥱd T&C.\nBᴏᴛ Wɪʟʟ Nᴏᴛ Wᴏʀᴋ Uɴᴛɪʟ Yᴏᴜ Aᴄᴄᴇᴘᴛ.",
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id, "Declined")

# =============== KEYBOARDS ===============
def start_keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("Group", url="https://t.me/team_x_og"),
        telebot.types.InlineKeyboardButton("Website", url="https://teamdev.sbs")
    )
    return markup

# =============== COMMANDS ===============
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not user_accepted_tc(user_id):
        send_tc_message(message.chat.id, user_id)
        return

    photo = "https://graph.org/file/6bdddbc4b335597a86632-bbfc6792edbf4e2b21.jpg"  # ← MAIN BOT IMAGE

    caption = (
        "Wᴇʙsɪᴛᴇ Mɪʀʀᴏʀ Bᴏᴛ - LIVE!\n\n"
        "Mᴀɪɴ Kɪsɪ Bʜɪ Pᴜʙʟɪᴄ Wᴇʙsɪᴛᴇ Kᴏ Pᴏᴏʀᴀ Cʟᴏɴᴇ Kᴀʀᴋᴇ ZIP Dᴇᴛᴀ Hᴏᴏɴ\n"
        "Bʜᴇᴊᴏ URL → ZIP Mɪʟ Jᴀᴀʏᴇɢᴀ\n"
        "Example: `https://httpbin.org`\n\n"
        f"Dᴀɪʟʏ Lɪᴍɪᴛ: 2 sɪᴛᴇs (Aᴅᴍɪɴ Bᴀᴅʜᴀ Sᴀᴋᴛᴀ Gᴀɪ)\n\n"
        "Made by @MR_ARMAN_08"
    )

    bot.send_photo(
        message.chat.id,
        photo,
        caption=caption,
        parse_mode='Markdown',
        reply_markup=start_keyboard()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    if not user_accepted_tc(message.from_user.id):
        bot.reply_to(message, "Pehle T&C Accept Karo!")
        send_tc_message(message.chat.id, message.from_user.id)
        return

    bot.reply_to(message, (
        "*Help*\n\n"
        "/start - Bot start\n"
        "/help - Yeh message\n"
        "/cancel - Task cancel\n\n"
        "Bas URL bhejo → ZIP milega!\n"
        "Support: @team_x_og"
    ), parse_mode='Markdown')

@bot.message_handler(commands=['limit'])
def set_limit(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Sirf admin use kar sakta hai")
        return
    
    try:
        args = message.text.split()
        target_id = int(args[1])
        limit = int(args[2])
        if 1 <= limit <= 100:
            set_user_limit(target_id, limit)
            bot.reply_to(message, f"User {target_id} → {limit}/day")
        else:
            bot.reply_to(message, "Limit 1-100 ke beech")
    except:
        bot.reply_to(message, "Usage: /limit user_id limit")

@bot.message_handler(commands=['cancel'])
def cancel(message):
    if not user_accepted_tc(message.from_user.id):
        bot.reply_to(message, "T&C accept karo pehle!")
        return
    
    user_id = message.from_user.id
    if user_id in active_tasks and not active_tasks[user_id]['cancelled']:
        active_tasks[user_id]['cancelled'] = True
        bot.reply_to(message, "Task cancelled!")
    else:
        bot.reply_to(message, "Koi task nahi chal raha")

# =============== BLOCK IF NOT ACCEPTED ===============
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    user_id = message.from_user.id

    # Block if not accepted T&C
    if not user_accepted_tc(user_id):
        send_tc_message(message.chat.id, user_id)
        bot.reply_to(message, "T&C accept karo pehle! Bot tabhi kaam karega")
        return

    # If accepted, then process URL
    url = message.text.strip()
    if not url.startswith(('http://', 'https://')):
        bot.reply_to(message, "Valid URL bhejo:\nhttps://example.com")
        return

    if user_id in active_tasks:
        bot.reply_to(message, "Ek time pe ek hi site!")
        return

    # Daily Limit Check
    data = reset_daily_if_needed(user_id)
    current_limit = data.get("custom_limit", DEFAULT_DAILY_LIMIT)
    if data["daily_used"] >= current_limit:
        bot.reply_to(message, f"Daily limit khatam! ({data['daily_used']}/{current_limit})\nKal try karo ya admin se badhwa lo")
        return

    progress_msg = bot.reply_to(message, "Starting mirror...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"mirrors/user_{user_id}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)

    mirror = WebsiteMirror(url, output_dir, message.chat.id, progress_msg.message_id, user_id)
    active_tasks[user_id] = {'cancelled': False}

    def run():
        try:
            mirror.cancelled = active_tasks[user_id]['cancelled']
            mirror.mirror()
            if not mirror.cancelled:
                increment_usage(user_id)
        finally:
            active_tasks.pop(user_id, None)

    threading.Thread(target=run, daemon=True).start()

# =============== MIRROR CLASS (Same as before) ===============
class WebsiteMirror:
    def __init__(self, url, output_dir, chat_id, msg_id, user_id):
        self.url = url.rstrip("/") + "/"
        self.domain = urlparse(url).netloc
        self.base_dir = Path(output_dir)
        self.output_dir = self.base_dir / self.domain
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.visited = set()
        self.file_count = 0
        self.chat_id = chat_id
        self.msg_id = msg_id
        self.user_id = user_id
        self.cancelled = False

    def normalize_path(self, url):
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if not path or path.endswith('/'):
            path = path + 'index.html' if path else 'index.html'
        elif '.' not in Path(path).name:
            path = path + '/index.html' if path.endswith('/') else path + '.html'
        return path.lstrip('/')

    def save_file(self, content, file_path):
        if self.cancelled: return False
        full_path = self.output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)
        self.file_count += 1
        return True

    def update_progress(self, text):
        if self.cancelled: return
        try:
            bot.edit_message_text(text, self.chat_id, self.msg_id, parse_mode='HTML')
        except:
            pass

    def download(self, url):
        if self.cancelled or url in self.visited: return
        self.visited.add(url)
        if urlparse(url).scheme not in ['http', 'https']: return

        try:
            time.sleep(0.3)
            r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            r.raise_for_status()
            final_url = r.url
            path = self.normalize_path(final_url)

            if self.file_count % 10 == 0 and self.file_count > 0:
                self.update_progress(f"Downloading...\n<b>{self.file_count}</b> files\nLast: {urlparse(final_url).path[:50]}...")

            ctype = r.headers.get('Content-Type', '') or ''
            if 'text/html' in ctype or not Path(path).suffix:
                if not path.endswith(('.html', '.htm')):
                    path = path.rstrip('/') + '/index.html' if '/' in path else path + '.html'
                if not self.save_file(r.content, path): return
                soup = BeautifulSoup(r.text, 'html.parser')
                for tag in soup.find_all(['a', 'link', 'script', 'img', 'source']):
                    link = tag.get('href') or tag.get('src')
                    if link and not link.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                        abs_url = urljoin(final_url, link.split('#')[0].split('?')[0])
                        if urlparse(abs_url).netloc in [self.domain, '']:
                            if abs_url not in self.visited:
                                self.download(abs_url)
            else:
                self.save_file(r.content, path)
        except:
            pass

    def mirror(self):
        try:
            self.update_progress("Starting mirror... (2-15 min)")
            self.download(self.url)
            if self.cancelled:
                self.update_progress("Cancelled")
                return

            self.update_progress("Zipping...")
            zip_path = f"{self.base_dir}_{self.domain}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(self.output_dir):
                    for file in files:
                        if self.cancelled: break
                        fp = os.path.join(root, file)
                        zf.write(fp, os.path.relpath(fp, self.base_dir))

            if self.cancelled or not os.path.exists(zip_path): return

            size_mb = os.path.getsize(zip_path) / (1024*1024)
            if size_mb > MAX_SIZE_MB:
                self.update_progress(f"ZIP bada hai ({size_mb:.1f} MB)\nChhoti site daal!")
                return

            self.update_progress("Uploading...")
            with open(zip_path, 'rb') as f:
                bot.send_document(self.chat_id, f,
                    caption=f"Cloned!\nFiles: {self.file_count}\nURL: {self.url}\nOffline Ready!")

            bot.send_message(self.chat_id, "Done! Website offline chalegi")

        except Exception as e:
            bot.send_message(self.chat_id, "Error ho gaya. Chhoti site try karo.")
        finally:
            shutil.rmtree(self.base_dir, ignore_errors=True)
            for f in os.listdir('.'):
                if f.endswith('.zip') and self.domain in f:
                    try: os.remove(f)
                    except: pass

# =============== START ===============
if not os.path.exists("mirrors"):
    os.makedirs("mirrors")

print("Professional Mirror Bot with T&C - Running!")
bot.infinity_polling()
