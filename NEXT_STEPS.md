# 🚀 FINAL SETUP STEPS - Start Here!

## ✅ Current Status

✅ **Python 3.14** - Installed  
✅ **Python packages** - Installed (python-telegram-bot 20.7)  
✅ **Database** - Initialized  
❌ **ffmpeg** - Not installed (requires admin)  
❌ **Bot Token** - Not configured  
❌ **Mini App URL** - Not configured  

---

## 🎯 What You Need to Do Now

### Step 1: Install ffmpeg (CRITICAL for security)

**Option A: Run PowerShell as Administrator**
```powershell
# Right-click PowerShell → Run as Administrator
choco install ffmpeg -y
```

**Option B: Manual Installation**
1. Download from: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
2. Extract to: `C:\ffmpeg`
3. Add to PATH:
   - Press `Win + X` → System → Advanced → Environment Variables
   - Edit PATH → Add: `C:\ffmpeg\bin`
4. Restart PowerShell

**Verify:**
```powershell
ffmpeg -version
```

---

### Step 2: Get Telegram Bot Token

1. Open Telegram
2. Search for: **@BotFather**
3. Send: `/newbot`
4. Choose a name: `Revolution1404Bot` (or your choice)
5. Choose username: `revolution1404_bot` (must end with _bot)
6. **Copy the token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

### Step 3: Configure the Bot

Edit [config.py](config.py) and replace:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

With your actual token:

```python
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Your token here
```

---

### Step 4: Host the Mini App

The file `webapp/index.html` needs to be on a public HTTPS URL.

**🎯 Recommended: GitHub Pages (Free & Easy)**

1. Go to https://github.com
2. Create new repository: `revolution-webapp`
3. Upload `webapp/index.html`
4. Settings → Pages → Enable
5. Your URL will be: `https://yourusername.github.io/revolution-webapp/index.html`

**Update config.py:**
```python
WEBAPP_URL = "https://yourusername.github.io/revolution-webapp/index.html"
```

**Alternative: Quick Test (Temporary)**
```powershell
# Terminal 1
cd "C:\Users\Lenovo\Desktop\telegram bot\webapp"
python -m http.server 8000

# Terminal 2 (download ngrok from https://ngrok.com)
ngrok http 8000
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io/index.html)
```

---

### Step 5: Run the Bot!

```powershell
cd "C:\Users\Lenovo\Desktop\telegram bot"
python bot.py
```

You should see:
```
INFO - Bot started successfully! 🦁☀️
```

---

### Step 6: Test in Telegram

1. Open Telegram
2. Search for your bot username
3. Send: `/start`
4. You should see the Persian welcome message!

---

## 🔧 Quick Reference

### Start the Bot
```powershell
cd "C:\Users\Lenovo\Desktop\telegram bot"
python bot.py
```

### Stop the Bot
Press `Ctrl + C`

### Check Logs
The bot prints logs to the console

### Verify Setup
```powershell
python setup_check.py
```

---

## 📝 What Works Without ffmpeg?

✅ Email campaigns (Mini App)  
✅ Twitter storms  
✅ Conduit instructions  
✅ Gamification/leaderboard  
❌ **Metadata stripping** (video safety feature)

**Note:** For production use, ffmpeg is CRITICAL for user safety!

---

## 🎯 Key Files to Edit

| File | What to Change |
|------|----------------|
| [config.py](config.py) | `BOT_TOKEN` and `WEBAPP_URL` |
| [config.py](config.py) | Points values (optional) |
| [config.py](config.py) | Email templates (optional) |
| [webapp/index.html](webapp/index.html) | Email recipients (optional) |

---

## 🌐 Deployment Options

### Local Machine (Testing)
```powershell
python bot.py
```
Keep PowerShell window open

### VPS/Cloud (Production)

**Option A: DigitalOcean/Linode/Vultr**
1. Create Ubuntu server ($5/month)
2. Upload files via SFTP
3. Install dependencies:
```bash
apt update
apt install python3 python3-pip ffmpeg -y
pip3 install -r requirements.txt
```
4. Run with screen:
```bash
screen -S bot
python3 bot.py
# Press Ctrl+A then D to detach
```

**Option B: Docker**
```powershell
docker build -t revolution-bot .
docker run -d --restart always revolution-bot
```

**Option C: PythonAnywhere (Free)**
1. Upload files
2. Create "Always-on task"
3. Run bot.py

---

## 🐛 Common Issues

### "Token is invalid"
- Check token in config.py
- No spaces before/after
- Token should start with numbers

### "Mini App doesn't open"
- URL must be HTTPS
- File must be publicly accessible
- Test URL in browser first

### "ffmpeg not found"
- Install ffmpeg
- Add to PATH
- Restart PowerShell

### "Module not found"
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version`

---

## 📊 Feature Checklist

- [ ] Python installed ✅
- [ ] Dependencies installed ✅
- [ ] Database created ✅
- [ ] ffmpeg installed (needed for video safety)
- [ ] Bot token obtained
- [ ] Bot token in config.py
- [ ] Mini App hosted
- [ ] Mini App URL in config.py
- [ ] Bot tested with /start
- [ ] All buttons working

---

## 🦁☀️ Ready to Launch!

Once you complete Steps 2-4 above, run:

```powershell
python bot.py
```

Your Persian UI bot will be live! 💪

For detailed documentation, see:
- [README.md](README.md) - Full English docs
- [QUICKSTART_FA.md](QUICKSTART_FA.md) - Persian quick start

---

**Questions?** Check the README or open an issue.

**پیروزی با ماست! 🦁☀️**
