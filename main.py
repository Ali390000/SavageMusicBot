
import os
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DB_FILE = "songs.db"

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


def init_db():
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                code TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                title TEXT NOT NULL
            )
        """)


def save_song(code, file_id, title):
    with sqlite3.connect(DB_FILE) as db:
        db.execute(
            "INSERT OR REPLACE INTO songs (code, file_id, title) VALUES (?, ?, ?)",
            (code, file_id, title),
        )


def get_song(code):
    with sqlite3.connect(DB_FILE) as db:
        return db.execute(
            "SELECT file_id, title FROM songs WHERE code = ?", (code,)
        ).fetchone()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        code = context.args[0]
        song = get_song(code)
        if song:
            await update.message.reply_audio(
                audio=song[0],
                caption=f"🎧 {song[1]}\nSavage MUSIC",
            )
        else:
            await update.message.reply_text(
                "❌ این آهنگ پیدا نشد."
            )
    else:
        await update.message.reply_text(
            "🎧 به Savage MUSIC خوش اومدی!\n"
            "برای دریافت آهنگ، از دکمه دانلود کانال استفاده کن."
        )


async def add_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or OWNER_ID == 0:
        await update.message.reply_text("⛔ این دستور فقط برای مدیر رباته.")
        return

    if not update.message or not update.message.audio:
        await update.message.reply_text(
            "اول آهنگ رو به صورت فایل Audio بفرست، "
            "بعد با دستور /save کد آهنگ و نامش رو وارد کن."
        )
        return

    await update.message.reply_text(
        "برای ذخیره آهنگ، فایل را با دستور /save ارسال کن.\n"
        "روش درست: /save track1 نام آهنگ\n"
        "برای استفاده از این روش، دستور را به فایل صوتی Reply کن."
    )


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or OWNER_ID == 0:
        await update.message.reply_text("⛔ اجازه دسترسی نداری.")
        return

    replied = update.message.reply_to_message
    if not replied or not replied.audio:
        await update.message.reply_text(
            "به پیام فایل صوتی Reply کن و بنویس:\n"
            "/save track1 نام آهنگ"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "نمونه: /save track1 My Song"
        )
        return

    code = context.args[0].strip()
    title = " ".join(context.args[1:]).strip() or code
    save_song(code, replied.audio.file_id, title)

    await update.message.reply_text(
        f"✅ آهنگ ذخیره شد!\n"
        f"کد: {code}\n"
        f"نام: {title}\n"
        f"لینک دانلود:\n"
        f"https://t.me/{context.bot.username}?start={code}"
    )


async def channel_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID or OWNER_ID == 0:
        await update.message.reply_text("⛔ اجازه دسترسی نداری.")
        return

    if not context.args:
        await update.message.reply_text(
            "نمونه: /button track1"
        )
        return

    code = context.args[0]
    song = get_song(code)
    if not song:
        await update.message.reply_text("❌ اول آهنگ را با /save ذخیره کن.")
        return

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📥 دانلود کامل",
            url=f"https://t.me/{context.bot.username}?start={code}",
        )
    ]])

    await update.message.reply_text(
        f"🎧 {song[1]}\nبرای دریافت آهنگ کامل روی دکمه بزن.",
        reply_markup=keyboard,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 راهنما:\n"
        "/start — شروع ربات\n"
        "/save track1 نام آهنگ — ذخیره آهنگ (با Reply به فایل صوتی)\n"
        "/button track1 — ساخت دکمه دانلود برای کانال"
    )


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN در Secrets تنظیم نشده است.")
    if OWNER_ID == 0:
        raise RuntimeError("OWNER_ID را در Secrets تنظیم کن.")

    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("button", channel_button))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()


if __name__ == "__main__":
    main()
