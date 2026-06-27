import asyncio
import re
from pathlib import Path

from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import yt_dlp

router = Router()

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

FFMPEG_PATH  = "/usr/local/bin/ffmpeg"
MAX_SIZE_MB  = 50

# ─── Teks ─────────────────────────────────────────────────────────────────────

TEXTS = {
    "id": {
        "fetching":        "Mengambil informasi video...",
        "invalid_url":     "Tautan yang dikirimkan tidak valid. Kirimkan tautan YouTube yang benar.",
        "fetch_failed":    "Gagal mengambil informasi video. Periksa tautan atau coba beberapa saat lagi.",
        "choose_type":     "Pilih jenis unduhan:",
        "choose_quality":  "Pilih kualitas:",
        "status_download": "Mengunduh video...",
        "status_merge":    "Menggabungkan video dan audio...",
        "status_convert":  "Mengonversi audio...",
        "status_upload":   "Mengunggah file ({size})...",
        "done":            "Selesai.",
        "too_large":       "Ukuran file terlalu besar ({size}). Batas Telegram adalah {limit} MB.\nCoba pilih kualitas yang lebih rendah.",
        "dl_failed":       "Unduhan gagal. Coba format atau kualitas lain.",
        "upload_failed":   "Gagal mengunggah file.",
        "cancelled":       "Dibatalkan.",
    },
    "en": {
        "fetching":        "Fetching video information...",
        "invalid_url":     "Invalid URL. Please send a valid YouTube link.",
        "fetch_failed":    "Failed to fetch video info. Check the link or try again later.",
        "choose_type":     "Choose download type:",
        "choose_quality":  "Choose quality:",
        "status_download": "Downloading video...",
        "status_merge":    "Merging video and audio...",
        "status_convert":  "Converting audio...",
        "status_upload":   "Uploading file ({size})...",
        "done":            "Done.",
        "too_large":       "File is too large ({size}). Telegram limit is {limit} MB.\nTry a lower quality.",
        "dl_failed":       "Download failed. Try another format or quality.",
        "upload_failed":   "Failed to upload file.",
        "cancelled":       "Cancelled.",
    },
}

# ─── FSM ──────────────────────────────────────────────────────────────────────

class DownloadState(StatesGroup):
    waiting_type    = State()
    waiting_quality = State()

# ─── Helpers ──────────────────────────────────────────────────────────────────

YT_REGEX = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/|embed/|live/)|youtu\.be/)[\w\-]+"
)

def is_yt_url(text: str) -> bool:
    return bool(YT_REGEX.search(text))

def get_lang(user_id: int, bot_data: dict) -> str:
    return bot_data.get("lang", {}).get(user_id, "id")

def t(key: str, lang: str, **kwargs) -> str:
    text = TEXTS[lang][key]
    return text.format(**kwargs) if kwargs else text

def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"

# ─── Keyboards ────────────────────────────────────────────────────────────────

def kb_type() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Video (MP4)", callback_data="type:video"),
            InlineKeyboardButton(text="Audio",       callback_data="type:audio"),
        ],
        [InlineKeyboardButton(text="Batal / Cancel", callback_data="type:cancel")],
    ])

def kb_video_quality() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1080p", callback_data="quality:mp4:1080"),
            InlineKeyboardButton(text="720p",  callback_data="quality:mp4:720"),
        ],
        [
            InlineKeyboardButton(text="480p",  callback_data="quality:mp4:480"),
            InlineKeyboardButton(text="360p",  callback_data="quality:mp4:360"),
        ],
        [InlineKeyboardButton(text="Batal / Cancel", callback_data="quality:cancel:0")],
    ])

def kb_audio_quality() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="M4A (kualitas terbaik)", callback_data="quality:m4a:best"),
        ],
        [
            InlineKeyboardButton(text="MP3 320 kbps", callback_data="quality:mp3:320"),
            InlineKeyboardButton(text="MP3 128 kbps", callback_data="quality:mp3:128"),
        ],
        [InlineKeyboardButton(text="Batal / Cancel", callback_data="quality:cancel:0")],
    ])

# ─── yt-dlp ───────────────────────────────────────────────────────────────────

def _get_info(url: str) -> dict | None:
    opts = {
        "quiet":         True,
        "no_warnings":   True,
        "skip_download": True,
        "cookiefile":    "cookies.txt" if Path("cookies.txt").exists() else None,
        "ffmpeg_location": FFMPEG_PATH,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception:
        return None


def _download(url: str, fmt: str, quality: str, status_cb) -> Path | None:
    """
    Download dengan progress hook.
    status_cb: callable(phase: str) — dipanggil tiap fase berubah.
    phase: 'downloading' | 'merging' | 'converting'
    """
    outtmpl = str(DOWNLOAD_DIR / "%(title).60s.%(ext)s")
    cookie  = "cookies.txt" if Path("cookies.txt").exists() else None

    if fmt == "mp4":
        h = int(quality)
        ydl_opts = {
            "outtmpl":              outtmpl,
            "quiet":                True,
            "no_warnings":          True,
            "cookiefile":           cookie,
            "ffmpeg_location":      FFMPEG_PATH,
            "merge_output_format":  "mp4",
            "format": (
                f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={h}]+bestaudio"
                f"/best[height<={h}]/best"
            ),
        }
    elif fmt == "m4a":
        ydl_opts = {
            "outtmpl":         outtmpl,
            "quiet":           True,
            "no_warnings":     True,
            "cookiefile":      cookie,
            "ffmpeg_location": FFMPEG_PATH,
            "format":          "bestaudio[ext=m4a]/bestaudio",
            "postprocessors":  [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}],
        }
    else:  # mp3
        ydl_opts = {
            "outtmpl":         outtmpl,
            "quiet":           True,
            "no_warnings":     True,
            "cookiefile":      cookie,
            "ffmpeg_location": FFMPEG_PATH,
            "format":          "bestaudio/best",
            "postprocessors":  [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   "mp3",
                "preferredquality": quality,
            }],
        }

    collector   = {"filename": None}
    last_phase  = {"v": None}

    def hook(d: dict):
        status = d.get("status")

        if status == "downloading":
            if last_phase["v"] != "downloading":
                last_phase["v"] = "downloading"
                status_cb("downloading")

        elif status == "finished":
            collector["filename"] = d["filename"]
            # Setelah finished, yt-dlp akan merge/convert
            if fmt == "mp4":
                status_cb("merging")
            else:
                status_cb("converting")

    ydl_opts["progress_hooks"] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        return None

    if collector["filename"]:
        p = Path(collector["filename"])
        if p.exists():
            return p
        for candidate in DOWNLOAD_DIR.iterdir():
            if candidate.stem == p.stem:
                return candidate

    files = sorted(DOWNLOAD_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None

# ─── Handlers ─────────────────────────────────────────────────────────────────

@router.message(lambda m: m.text and is_yt_url(m.text))
async def handle_url(message: Message, state: FSMContext, bot_data: dict):
    lang   = get_lang(message.from_user.id, bot_data)
    url    = message.text.strip()
    status = await message.answer(t("fetching", lang))

    info = await asyncio.get_event_loop().run_in_executor(None, _get_info, url)
    if not info:
        await status.edit_text(t("fetch_failed", lang))
        return

    title    = info.get("title", "Unknown")
    uploader = info.get("uploader", "Unknown")
    mins, secs = divmod(int(info.get("duration", 0)), 60)

    await state.update_data(url=url, title=title)
    await state.set_state(DownloadState.waiting_type)

    await status.edit_text(
        f"<b>{title}</b>\n"
        f"{uploader} — {mins}:{secs:02d}\n\n"
        f"{t('choose_type', lang)}",
        parse_mode="HTML",
        reply_markup=kb_type(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("type:"))
async def cb_type(callback: CallbackQuery, state: FSMContext, bot_data: dict):
    lang   = get_lang(callback.from_user.id, bot_data)
    choice = callback.data.split(":")[1]

    if choice == "cancel":
        await state.clear()
        await callback.message.edit_text(t("cancelled", lang))
        await callback.answer()
        return

    await state.set_state(DownloadState.waiting_quality)

    kb = kb_video_quality() if choice == "video" else kb_audio_quality()
    await callback.message.edit_text(t("choose_quality", lang), reply_markup=kb)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("quality:"))
async def cb_quality(callback: CallbackQuery, state: FSMContext, bot_data: dict):
    lang = get_lang(callback.from_user.id, bot_data)
    _, fmt, quality = callback.data.split(":")

    if fmt == "cancel":
        await state.clear()
        await callback.message.edit_text(t("cancelled", lang))
        await callback.answer()
        return

    data  = await state.get_data()
    url   = data.get("url")
    title = data.get("title", "")
    await state.clear()

    if not url:
        await callback.message.edit_text(t("dl_failed", lang))
        await callback.answer()
        return

    label_map = {
        ("mp4", "1080"): "MP4 1080p",
        ("mp4", "720"):  "MP4 720p",
        ("mp4", "480"):  "MP4 480p",
        ("mp4", "360"):  "MP4 360p",
        ("m4a", "best"): "M4A",
        ("mp3", "320"):  "MP3 320 kbps",
        ("mp3", "128"):  "MP3 128 kbps",
    }
    label = label_map.get((fmt, quality), f"{fmt} {quality}")

    status_msg = await callback.message.edit_text(
        t("status_download", lang),
        parse_mode="HTML",
    )
    await callback.answer()

    # Status update callback — dijalankan dari thread executor ke event loop
    loop = asyncio.get_event_loop()

    phase_texts = {
        "downloading": t("status_download", lang),
        "merging":     t("status_merge", lang),
        "converting":  t("status_convert", lang),
    }

    def on_phase(phase: str):
        text = phase_texts.get(phase, "")
        asyncio.run_coroutine_threadsafe(
            status_msg.edit_text(text, parse_mode="HTML"),
            loop,
        )

    file_path = await asyncio.get_event_loop().run_in_executor(
        None, _download, url, fmt, quality, on_phase
    )

    if not file_path or not file_path.exists():
        await status_msg.edit_text(t("dl_failed", lang))
        return

    size_bytes = file_path.stat().st_size
    size_mb    = size_bytes / (1024 * 1024)

    if size_mb > MAX_SIZE_MB:
        file_path.unlink(missing_ok=True)
        await status_msg.edit_text(
            t("too_large", lang, size=human_size(size_bytes), limit=MAX_SIZE_MB)
        )
        return

    await status_msg.edit_text(
        t("status_upload", lang, size=human_size(size_bytes)),
        parse_mode="HTML",
    )

    try:
        with open(file_path, "rb") as f:
            caption = f"<b>{title}</b>\n{label}"
            if fmt == "mp4":
                await callback.message.answer_video(
                    video=f,
                    caption=caption,
                    parse_mode="HTML",
                    supports_streaming=True,
                )
            else:
                await callback.message.answer_audio(
                    audio=f,
                    caption=caption,
                    parse_mode="HTML",
                )
        await status_msg.edit_text(t("done", lang))
    except Exception:
        await status_msg.edit_text(t("upload_failed", lang))
    finally:
        file_path.unlink(missing_ok=True)
