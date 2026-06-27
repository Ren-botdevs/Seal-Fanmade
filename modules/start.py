import os
from dotenv import load_dotenv

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

load_dotenv()

BOT_TOKEN   = os.getenv("BOT_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/Renprjkt")
SOURCE_URL  = os.getenv("SOURCE_URL",  "https://github.com/Ren-botdevs/Seal-Fanmade")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak ditemukan di file .env")

router = Router()

# ─── Teks ─────────────────────────────────────────────────────────────────────

TEXTS = {
    "id": {
        "start": (
            "<b>Seal — Pengunduh Video YouTube</b>\n\n"
            "Bot ini memungkinkan Anda mengunduh video maupun audio dari YouTube "
            "dalam berbagai format yang tersedia.\n\n"
            "<b>Format yang didukung:</b>\n"
            "- Video: MP4 (360p, 480p, 720p, 1080p)\n"
            "- Audio: M4A (kualitas terbaik), MP3 (320 kbps)\n\n"
            "Cukup kirimkan tautan YouTube untuk memulai."
        ),
        "lang_prompt": "Pilih bahasa yang ingin digunakan:",
        "lang_set":    "Bahasa berhasil diubah ke <b>Indonesia</b>.",
    },
    "en": {
        "start": (
            "<b>Seal — YouTube Video Downloader</b>\n\n"
            "This bot allows you to download videos and audio from YouTube "
            "in various available formats.\n\n"
            "<b>Supported formats:</b>\n"
            "- Video: MP4 (360p, 480p, 720p, 1080p)\n"
            "- Audio: M4A (best quality), MP3 (320 kbps)\n\n"
            "Simply send a YouTube link to get started."
        ),
        "lang_prompt": "Select your preferred language:",
        "lang_set":    "Language has been changed to <b>English</b>.",
    },
}

# ─── Keyboards ────────────────────────────────────────────────────────────────

def kb_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Update Channel", url=CHANNEL_URL),
            InlineKeyboardButton(text="Source Code",    url=SOURCE_URL),
        ]
    ])

def kb_lang() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Indonesia", callback_data="setlang:id"),
            InlineKeyboardButton(text="English",   callback_data="setlang:en"),
        ]
    ])

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_lang(user_id: int, bot_data: dict) -> str:
    return bot_data.get("lang", {}).get(user_id, "id")

def set_lang(user_id: int, bot_data: dict, lang: str):
    bot_data.setdefault("lang", {})[user_id] = lang

# ─── Handlers ─────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, bot_data: dict):
    lang = get_lang(message.from_user.id, bot_data)
    await message.answer(
        text=TEXTS[lang]["start"],
        parse_mode="HTML",
        reply_markup=kb_start(),
    )


@router.message(Command("lang"))
async def cmd_lang(message: Message, bot_data: dict):
    lang = get_lang(message.from_user.id, bot_data)
    await message.answer(
        text=TEXTS[lang]["lang_prompt"],
        reply_markup=kb_lang(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("setlang:"))
async def cb_set_lang(callback: CallbackQuery, bot_data: dict):
    chosen = callback.data.split(":")[1]
    if chosen not in TEXTS:
        await callback.answer("Invalid language.")
        return

    set_lang(callback.from_user.id, bot_data, chosen)

    await callback.message.edit_text(
        text=TEXTS[chosen]["lang_set"],
        parse_mode="HTML",
    )
    await callback.answer()
