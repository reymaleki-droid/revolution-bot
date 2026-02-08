"""
Quick Setup Script for National Revolution 1404 Bot
Run this to verify your environment is ready
"""
import sys
import subprocess
import os

def check_python_version():
    """Check Python version"""
    print("🔍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
        return False

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    print("\n🔍 Checking ffmpeg installation...")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ {version_line}")
            return True
        else:
            print("❌ ffmpeg not working properly")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found")
        print("   Install from: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"❌ Error checking ffmpeg: {e}")
        return False

def check_config():
    """Check if config is set up"""
    print("\n🔍 Checking configuration...")
    try:
        from config import BOT_TOKEN, WEBAPP_URL
        
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ BOT_TOKEN not configured")
            print("   Edit config.py and add your bot token from @BotFather")
            return False
        else:
            print("✅ BOT_TOKEN configured: [REDACTED]")
        
        if "yourdomain.com" in WEBAPP_URL:
            print("⚠️  WEBAPP_URL not configured (using placeholder)")
            print("   Update config.py with your hosted Mini App URL")
            return False
        else:
            print(f"✅ WEBAPP_URL configured: {WEBAPP_URL}")
        
        return True
    except ImportError as e:
        print(f"❌ Cannot import config.py: {e}")
        return False

def check_dependencies():
    """Check if Python packages are installed"""
    print("\n🔍 Checking Python dependencies...")
    try:
        import telegram
        print(f"✅ python-telegram-bot {telegram.__version__}")
        
        # Check version
        version = telegram.__version__
        major = int(version.split('.')[0])
        if major >= 20:
            print("   Version 20+ confirmed - OK")
        else:
            print(f"   ⚠️  Version {version} - recommend 20+")
        
        return True
    except ImportError:
        print("❌ python-telegram-bot not installed")
        print("   Run: pip install -r requirements.txt")
        return False

def create_database():
    """Initialize database"""
    print("\n🔍 Checking database...")
    try:
        from database import Database
        db = Database()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🦁☀️ National Revolution 1404 Bot - Setup Verification")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_ffmpeg(),
        check_dependencies(),
        check_config(),
        create_database(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ ALL CHECKS PASSED!")
        print("\n🚀 You're ready to start the bot:")
        print("   python bot.py")
        print("\n📝 Next steps:")
        print("   1. Make sure WEBAPP_URL is hosted (see README.md)")
        print("   2. Test bot in Telegram")
        print("   3. Send /start to begin")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before starting the bot.")
        print("See README.md for detailed instructions.")
    print("=" * 60)

if __name__ == '__main__':
    main()
