# 🦁☀️ Telegram Bot - National Revolution 1404

**ارتش دیجیتال انقلاب ملی ۱۴۰۴**

A comprehensive Telegram bot for the Iranian Diaspora to support the National Revolution through digital advocacy, censorship circumvention, and secure media sharing.

---

## 🛡️ Security & Trust

> **This project is designed to fail safely.**

| Trust Signal | Implementation |
|--------------|----------------|
| ✅ Open Source | Full code visibility, forkable |
| ✅ Zero-Knowledge | No PII stored, hashed identifiers only |
| ✅ Signed Commits | Cryptographic author verification |
| ✅ Branch Protection | No solo merges, 2 approvals required |
| ✅ Automated Scanning | CI blocks secrets, vulnerabilities |
| ✅ Security Policy | [SECURITY.md](SECURITY.md) |
| ✅ Threat Model | [THREAT_MODEL.md](THREAT_MODEL.md) |
| ✅ Kill Switch | [KILL_SWITCH.md](KILL_SWITCH.md) |

### What This Bot CANNOT Do

| Guarantee | Explanation |
|-----------|-------------|
| ❌ Cannot identify users | User IDs are HMAC-hashed, irreversible |
| ❌ Cannot read messages | No message storage, ever |
| ❌ Cannot track location | No IP/GPS data collection |
| ❌ Cannot access contacts | No contact permission requested |
| ❌ Cannot share user data | No user data exists to share |
| ❌ Cannot be backdoored silently | All changes require 2 public approvals |

### Transparency Commitments

- 📖 All code changes are public PRs
- 📖 All security decisions are documented
- 📖 No secret admin capabilities
- 📖 No telemetry or analytics
- 📖 No third-party data sharing
- 📖 Fork rights guaranteed forever

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

### Step 5: Configure Environment

⚠️ **NEVER commit secrets to git!**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your values:
   ```bash
   BOT_TOKEN=your_bot_token_here
   HASH_PEPPER=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
   USER_HASH_SALT=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
   ADMIN_IDS=your_telegram_user_id
   ```

3. For production (Railway), set these as environment variables in the Railway dashboard.

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
INFO - Bot started successfully! 🦁☀️
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
├── config.py              # Configuration (env vars only)
├── secure_database_pg.py  # Zero-knowledge PostgreSQL database
├── utils.py               # Utilities (metadata stripping, spintax)
├── verify_db.py           # Security verification script
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── SECURITY.md            # Security policy & vulnerability reporting
├── LICENSE                # MIT License
└── webapp/
    └── index.html         # Email advocacy Mini App
```

---

## 🔒 Security Architecture

### Zero-Knowledge Design

This bot implements a **zero-knowledge architecture** that protects user privacy even in the event of a complete database breach.

#### What We Store
| Data | Storage Method | Reversible? |
|------|----------------|-------------|
| User identifier | HMAC-SHA256 hash | ❌ No |
| Points (Imtiaz) | Plain integer | N/A |
| Rank | Plain text | N/A |
| Action timestamps | UTC datetime | N/A |
| Aggregate stats | Counters only | N/A |

#### What We NEVER Store
- ❌ Telegram user IDs (plaintext)
- ❌ Usernames or display names
- ❌ Phone numbers or email addresses
- ❌ Message content or media files
- ❌ File IDs or Telegram-internal identifiers
- ❌ IP addresses or geolocation
- ❌ OCR text from screenshots
- ❌ Any personally identifiable information (PII)

#### How User Hashing Works
```
user_hash = HMAC-SHA256(HASH_PEPPER, user_id || USER_HASH_SALT)
```
- **Irreversible**: Cannot recover user_id from hash
- **Collision-resistant**: SHA256 provides 128-bit security
- **Unique per deployment**: Different pepper/salt = different hashes

### Media Security

1. **Metadata Stripping**
   - Uses ffmpeg to remove ALL metadata
   - Strips GPS coordinates, EXIF data, creation time
   - Protects users submitting crime evidence
   - Original files are deleted after cleaning

2. **No Persistent Storage**
   - Media processed in memory/temp files
   - Automatic cleanup after processing
   - No file_ids stored in database

### Secret Management

- All secrets loaded from **environment variables only**
- No hardcoded credentials in source code
- Fail-closed design: missing secrets = immediate exit
- Production requires: `BOT_TOKEN`, `DATABASE_URL`, `HASH_PEPPER`, `USER_HASH_SALT`

---

## 🛡️ Threat Model

### Protected Against
| Threat | Mitigation |
|--------|------------|
| Database breach | Only hashed IDs stored, no PII recovery |
| Log analysis | No user identifiers in logs |
| Rainbow tables | Unique salt + pepper per deployment |
| SQL injection | Parameterized queries only |
| Memory dump | Secrets in env vars, not code |

### Out of Scope
- Telegram API/infrastructure security
- Hosting provider security
- DDoS attacks
- Social engineering against admins

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

## 📊 Database Schema (Zero-Knowledge)

### Users Table
```sql
- user_hash TEXT PRIMARY KEY  -- HMAC-SHA256 hash, NOT reversible
- imtiaz INTEGER              -- Points
- role TEXT                   -- Rank title
- joined_at TIMESTAMPTZ       -- When user joined
- last_active TIMESTAMPTZ     -- Last activity
```

### Action Logs Table (30-day retention)
```sql
- id BIGSERIAL PRIMARY KEY
- user_hash TEXT              -- Hashed identifier
- action_type TEXT            -- Type of action
- points INTEGER              -- Points earned
- created_at TIMESTAMPTZ      -- Timestamp (auto-deleted after 30 days)
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

## ⚖️ Legal & Liability

### What This Project Guarantees

| Guarantee | Scope |
|-----------|-------|
| ✅ Open source code | MIT License, perpetual |
| ✅ No intentional backdoors | Verified by public review |
| ✅ Zero PII storage by design | Architectural guarantee |
| ✅ Fork rights | Anyone can fork, modify, deploy |
| ✅ Transparent governance | All changes public |

### What This Project Does NOT Guarantee

| Non-Guarantee | Explanation |
|---------------|-------------|
| ❌ Uptime or availability | Best-effort operation |
| ❌ Protection from Telegram | Telegram can ban any bot |
| ❌ Legal protection | Users assume legal responsibility |
| ❌ Immunity from hosting issues | Railway/infra can fail |
| ❌ Perfect security | No system is 100% secure |
| ❌ Fitness for purpose | Provided "as-is" |

### Jurisdiction

- This software has **no jurisdiction** - it is code, not a legal entity
- Contributors are geographically distributed
- Users deploy at their own discretion
- No central authority can be compelled to act

### Contributor Liability

By contributing, you:
- Grant MIT License to your contributions
- Assume no liability for how code is used
- Are not liable for other contributors' code
- Are not liable for deployment decisions

### User Responsibility

Users are solely responsible for:
- Compliance with local laws
- Secure deployment practices
- Protecting their own credentials
- Backup of their own data

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

## 🦁☀️ For the Freedom of Iran

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
