# 🇮🇷 Telegram Bot - National Revolution 1404

**ارتش دیجیتال انقلاب ملی ۱۴۰۴**

A comprehensive Telegram bot for the Iranian Diaspora to support the National Revolution through digital advocacy, censorship circumvention, and secure media sharing.

---

## ✨ Features

### 🎯 Core Modules

1. **📧 Email Advocacy (Mini App)**
   - Launch web-based email campaigns
   - Pre-filled templates for UN, parliaments, media
   - Demands: Military Aid, R2P, Recognition of Prince Reza Pahlavi
   - Multi-language support (English, French, German)

2. **🌐 Censorship Circumvention (Conduit)**
   - Psiphon Conduit installation instructions (Persian)
   - Screenshot verification system
   - 50 points reward for helping Iranians bypass censorship

3. **🐦 Twitter Storm**
   - Daily randomized tweets with spintax
   - Automatic hashtags: #NationalRevolution1404, #RezaPahlavi
   - Twitter intent links for easy sharing
   - Anti-spam detection through text variation

4. **🔒 Secure Media Submission**
   - **Automatic metadata stripping** using ffmpeg
   - Removes GPS, EXIF, creation time, device info
   - Critical for user safety when submitting crime evidence
   - Video/image support

5. **🏆 Gamification System**
   - Points (Imtiaz) for every action
   - Military-style ranks: Sarbaz → Farman-deh
   - Leaderboard (Tabloye Eftekhar)
   - User profiles and statistics

### 🌍 Language

- **UI Language**: Persian (Farsi) - All buttons, messages, and menus
- **Email Templates**: English/French/German (for international recipients)
- **Target Audience**: Iranian Diaspora

---

## 📋 Requirements

### System Requirements
- Python 3.8+
- **ffmpeg** (required for video metadata stripping)
- Internet connection
- Telegram account

### Python Dependencies
See [requirements.txt](requirements.txt)

---

## 🚀 Installation & Setup

### Step 1: Install System Dependencies

#### Windows
Download and install ffmpeg:
1. Go to https://ffmpeg.org/download.html
2. Download Windows build
3. Add to PATH environment variable

Or use Chocolatey:
```powershell
choco install ffmpeg
```

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install ffmpeg python3-pip
```

#### macOS
```bash
brew install ffmpeg
```

### Step 2: Clone/Download Project
```bash
cd "C:\Users\Lenovo\Desktop\telegram bot"
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the **Bot Token**

### Step 5: Configure Bot

Open [config.py](config.py) and set:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Paste your token
WEBAPP_URL = "https://yourdomain.com/webapp/index.html"  # See Step 6
```

### Step 6: Host the Mini App (Web App)

The Mini App in `webapp/index.html` needs to be hosted on a public HTTPS URL.

**Option A: GitHub Pages (Free)**
1. Create a GitHub repository
2. Upload `webapp/index.html`
3. Enable GitHub Pages in settings
4. Use URL: `https://yourusername.github.io/reponame/webapp/index.html`

**Option B: Netlify/Vercel (Free)**
1. Create account on Netlify or Vercel
2. Deploy `webapp` folder
3. Get HTTPS URL

**Option C: Self-hosted with Flask**
```bash
cd webapp
python -m http.server 8000
```
Then use ngrok for HTTPS tunnel:
```bash
ngrok http 8000
```

Update `WEBAPP_URL` in [config.py](config.py) with your URL.

### Step 7: Run the Bot

```bash
python bot.py
```

You should see:
```
INFO - Bot started successfully! 🇮🇷
```

---

## 📱 User Guide (Persian)

### راهنمای استفاده برای کاربران

#### شروع کار
1. ربات را در تلگرام باز کنید
2. دکمه `/start` را بزنید
3. با پیام خوشامدگویی مواجه می‌شوید

#### عملیات‌های موجود

**📧 ارسال ایمیل هدفمند**
- یک برنامه وب باز می‌شود
- ایمیل‌های آماده به سازمان ملل، پارلمان‌ها، و رسانه‌ها
- فقط روی دکمه کلیک کنید
- پاداش: 10 امتیاز

**🌐 اشتراک اینترنت (Conduit)**
- Psiphon را نصب کنید
- حداقل 24 ساعت روشن نگه دارید
- اسکرین‌شات از Traffic Stats بگیرید
- ارسال کنید
- پاداش: 50 امتیاز

**🐦 توییت روزانه**
- یک توییت تصادفی تولید می‌شود
- روی دکمه کلیک کنید تا توییتر باز شود
- توییت کنید
- تأیید کنید
- پاداش: 5 امتیاز

**📹 ارسال مستندات**
- ویدیوی جنایات را ارسال کنید
- متادیتا به صورت خودکار حذف می‌شود (امنیت)
- پاداش: 15 امتیاز

**👤 پروفایل من**
- امتیاز، درجه، و رتبه خود را ببینید

**🏆 تابلوی افتخار**
- برترین رزمندگان را ببینید

#### سیستم درجه‌بندی
- سرباز (0 امتیاز)
- گروهبان (50 امتیاز)
- ستوان (100 امتیاز)
- سرگرد (200 امتیاز)
- فرمانده (500 امتیاز)
- فرمانده کل (1000 امتیاز)

---

## 🏗️ Project Structure

```
telegram bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration and Persian texts
├── database.py            # SQLite database management
├── utils.py               # Utilities (metadata stripping, spintax)
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── webapp/
│   └── index.html         # Email advocacy Mini App
└── revolution_bot.db      # SQLite database (auto-created)
```

---

## 🔒 Security Features

### Critical Security Implementations

1. **Metadata Stripping**
   - Uses ffmpeg to remove ALL metadata
   - Strips GPS coordinates, EXIF data, creation time
   - Protects users submitting crime evidence
   - Original files are deleted after cleaning

2. **Safe File Handling**
   - Temporary file storage
   - Automatic cleanup
   - No persistent storage of sensitive media

3. **Anti-Detection**
   - Spintax for tweet randomization
   - Avoids spam detection
   - Multiple template variations

---

## 🎯 Points System

| Action | Points | Description |
|--------|--------|-------------|
| Daily Login | 2 | Just for showing up |
| Email Sent | 10 | Each advocacy email |
| Tweet Shared | 5 | Daily Twitter campaign |
| Media Submitted | 15 | Secure video/image upload |
| Conduit Verified | 50 | 24h+ Psiphon sharing |

---

## 🛠️ Advanced Configuration

### Using PostgreSQL (Production)

For production deployment, replace SQLite with PostgreSQL:

1. Uncomment in [requirements.txt](requirements.txt):
```python
psycopg2-binary==2.9.9
```

2. Modify [database.py](database.py) connection:
```python
def get_connection(self):
    return psycopg2.connect(
        host="localhost",
        database="revolution_bot",
        user="postgres",
        password="your_password"
    )
```

### OCR Verification (Conduit Screenshots)

To implement automatic OCR verification:

1. Install Tesseract OCR
2. Update `ConduitHelper.verify_screenshot()` in [utils.py](utils.py)
3. Use pytesseract to extract text from screenshots
4. Check for traffic indicators (MB/GB transferred)

---

## 📊 Database Schema

### Users Table
```sql
- user_id (PRIMARY KEY)
- username
- first_name
- imtiaz (points)
- role (rank)
- joined_date
- last_active
```

### Actions Table
```sql
- id (AUTO INCREMENT)
- user_id (FOREIGN KEY)
- action_type
- points
- timestamp
- details
```

### Conduit Verifications Table
```sql
- id (AUTO INCREMENT)
- user_id (FOREIGN KEY)
- screenshot_file_id
- verified (BOOLEAN)
- timestamp
```

---

## 🌐 Deployment

### Option 1: Local Machine
Run directly on your computer:
```bash
python bot.py
```

### Option 2: VPS/Cloud Server
Deploy on DigitalOcean, AWS, Google Cloud, etc.

1. Upload files to server
2. Install dependencies
3. Use systemd or supervisor to keep running
4. Set up logging and monitoring

Example systemd service:
```ini
[Unit]
Description=National Revolution 1404 Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/telegram bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 3: Docker (Recommended)
Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build and run:
```bash
docker build -t revolution-bot .
docker run -d --name revolution-bot revolution-bot
```

---

## 🐛 Troubleshooting

### Bot doesn't start
- Check BOT_TOKEN in [config.py](config.py)
- Verify internet connection
- Check Python version: `python --version` (needs 3.8+)

### Metadata stripping fails
- Verify ffmpeg is installed: `ffmpeg -version`
- Check ffmpeg is in PATH
- Ensure file format is supported

### Mini App doesn't load
- Check WEBAPP_URL is correct HTTPS URL
- Verify HTML file is publicly accessible
- Test URL in browser

### Database errors
- Check file permissions
- Ensure SQLite is installed (built-in with Python)
- Delete `revolution_bot.db` and restart (resets database)

---

## 📞 Support

For issues or questions:
- Create GitHub issue
- Contact bot administrator
- Check logs: `bot.py` outputs to console

---

## ⚖️ Legal Disclaimer

This software is provided for educational and advocacy purposes. Users are responsible for complying with local laws and regulations. The developers assume no liability for misuse.

---

## 🙏 Contributing

Contributions welcome! Please:
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🇮🇷 For the Freedom of Iran

**انقلاب ملی ۱۴۰۴**

Together, we fight for a free, democratic Iran. Every email, every tweet, every action matters.

💪 **پیروزی با ماست** 💪

---

## Version History

- **v1.0.0** (2026-01-27) - Initial release
  - Email advocacy Mini App
  - Conduit verification system
  - Metadata stripping for videos/images
  - Twitter campaign with spintax
  - Gamification and leaderboard
  - Full Persian UI

---

*Built with ❤️ for Iranian freedom fighters worldwide*
