<div align="center">

<img src="https://raw.githubusercontent.com/Ren-botdevs/Seal-Fanmade/main/assets/banner.png" alt="Seal Bot" width="600"/>

# Seal
### YouTube Downloader Telegram Bot

A clean, fast, and multilingual Telegram bot for downloading YouTube videos and audio — powered by yt-dlp and aiogram.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.15-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://aiogram.dev)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Channel](https://img.shields.io/badge/Telegram-@Renprjkt-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/Renprjkt)

</div>

---

## Features

- **Video** — MP4 in 360p, 480p, 720p, or 1080p
- **Audio** — M4A (best quality) or MP3 at 320/128 kbps
- **Multilingual** — Indonesian and English, switchable per user via `/lang`
- **Real-time status** — live updates during download, merge, convert, and upload phases
- **Bundled ffmpeg** — no system-wide installation required

---

## Project Structure

```
Seal-Fanmade/
├── bin/
│   └── ffmpeg              # bundled ffmpeg binary
├── modules/
│   ├── start.py            # /start and /lang handlers
│   └── downloader.py       # download flow and yt-dlp logic
├── downloads/              # temporary download directory (auto-created)
├── main.py                 # entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Linux VPS (recommended: Ubuntu 22.04+)

---

### 1. Clone the repository

```bash
git clone https://github.com/Ren-botdevs/Seal-Fanmade.git
cd Seal-Fanmade
```

### 2. Download ffmpeg binary

Seal bundles its own ffmpeg so you do not need a system installation.

```bash
mkdir -p bin && cd bin

wget https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz

tar -xf ffmpeg-master-latest-linux64-gpl.tar.xz
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg .
rm -rf ffmpeg-master-latest-linux64-gpl ffmpeg-master-latest-linux64-gpl.tar.xz

chmod +x ffmpeg
cd ..
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in your values:

```env
BOT_TOKEN=your_bot_token_here
CHANNEL_URL=https://t.me/Renprjkt
SOURCE_URL=https://github.com/Ren-botdevs/Seal-Fanmade
```

### 5. (Optional) Add cookies

To avoid YouTube bot detection, export your browser cookies and place the file in the project root:

```bash
# Export using the "Get cookies.txt LOCALLY" browser extension
# then upload to your VPS:
scp cookies.txt user@your-vps-ip:~/Seal-Fanmade/cookies.txt
```

### 6. Run the bot

```bash
python main.py
```

---

## Running as a Service

To keep Seal running after you close your SSH session, set it up as a systemd service.

```bash
sudo nano /etc/systemd/system/seal-bot.service
```

```ini
[Unit]
Description=Seal Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/Seal-Fanmade
ExecStart=/usr/bin/python3 main.py
EnvironmentFile=/home/YOUR_USER/Seal-Fanmade/.env
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable seal-bot
sudo systemctl start seal-bot

# Check status
sudo systemctl status seal-bot

# View logs
sudo journalctl -u seal-bot -f
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Display bot introduction and available formats |
| `/lang` | Switch language between Indonesian and English |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Sign in to confirm you're not a bot` | Add `cookies.txt` to the project root |
| `No supported JavaScript runtime` | Install Deno: `curl -fsSL https://deno.land/install.sh \| sh` |
| File exceeds 50 MB limit | Choose a lower resolution or use audio format |
| Formats unavailable | Update yt-dlp: `pip install -U yt-dlp` |
| Bot not responding | Check logs: `journalctl -u seal-bot -f` |

---

## Credits

<table>
  <tr>
    <td align="center">
      <b>Ren</b><br/>
      <sub>Developer & Maintainer</sub><br/>
      <a href="https://t.me/Renprjkt">@Renprjkt</a>
    </td>
  </tr>
</table>

**Built with:**

- [aiogram](https://github.com/aiogram/aiogram) — Modern async Telegram Bot API framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Feature-rich YouTube downloader
- [FFmpeg](https://ffmpeg.org) — Audio and video processing

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made with care by [Ren](https://t.me/Renprjkt) · [Update Channel](https://t.me/Renprjkt) · [Source Code](https://github.com/Ren-botdevs/Seal-Fanmade)

</div>
