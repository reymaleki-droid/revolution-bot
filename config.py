"""
Configuration file for National Revolution 1404 Bot
Persian texts, templates, and settings
"""
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required, use environment variables directly

# Detect Railway environment
RAILWAY_ENVIRONMENT = os.getenv('RAILWAY_ENVIRONMENT')
IS_PRODUCTION = bool(RAILWAY_ENVIRONMENT)

# Default Language
DEFAULT_LANGUAGE = 'fa'

# Bot Settings - Load from environment variables for security
# CRITICAL: Never hardcode tokens - always use environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("CRITICAL: BOT_TOKEN environment variable not set!", file=sys.stderr)
    sys.exit(1)

# Database configuration (PostgreSQL)
DATABASE_URL = os.getenv('DATABASE_URL')
if IS_PRODUCTION and not DATABASE_URL:
    print("CRITICAL: DATABASE_URL not set in Railway environment", file=sys.stderr)
    sys.exit(1)

# SEC: HASH_PEPPER for HMAC-based user hashing (64 hex chars recommended)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
HASH_PEPPER = os.getenv('HASH_PEPPER')
if IS_PRODUCTION and not HASH_PEPPER:
    print("CRITICAL: HASH_PEPPER not set in Railway environment", file=sys.stderr)
    sys.exit(1)

# SEC: USER_HASH_SALT (hex-encoded bytes) for stable hashing across deploys
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
# If not set, falls back to file-based salt (not recommended for production)
USER_HASH_SALT = os.getenv('USER_HASH_SALT')
if IS_PRODUCTION and not USER_HASH_SALT:
    print("CRITICAL: USER_HASH_SALT not set in Railway environment", file=sys.stderr)
    sys.exit(1)

# Data retention policy (days) - action logs older than this are purged
ACTION_LOG_RETENTION_DAYS = int(os.getenv('ACTION_LOG_RETENTION_DAYS', '30'))

WEBAPP_URL = os.getenv('WEBAPP_URL', "")  # Set in .env file when ready

# Security Settings
USE_SECURE_DATABASE = os.getenv('USE_SECURE_DATABASE', 'true').lower() == 'true'
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Warn if no admins configured
import logging as _cfg_logging
_cfg_logger = _cfg_logging.getLogger(__name__)
if not ADMIN_IDS:
    _cfg_logger.warning("⚠️ ADMIN_IDS not configured - admin commands will be disabled")
    _cfg_logger.warning("   Set ADMIN_IDS=your_telegram_id in .env file")

# Feature Flags
ENABLE_VIDEO_PROCESSING = True
ENABLE_OCR_VERIFICATION = os.getenv('ENABLE_OCR_VERIFICATION', 'true').lower() == 'true'
OCR_CONFIDENCE_THRESHOLD = 60
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Points System - Enhanced & Rewarding
POINTS = {
    'email_sent': 20,
    'tweet_shared': 12,
    'media_submitted': 35,
    'video_testimonial': 150,
    'daily_login': 5,
    'protest_attendance': 10,
    'protest_cleanup': 40,
    'protest_media_shared': 18,
    'protest_event_created': 30,
}

# Conduit Data Sharing Tiers (GB -> Points) - More Rewarding
CONDUIT_TIERS = {
    '1-10': {'min': 1, 'max': 10, 'points': 25, 'badge': '🥉 برنز'},
    '11-50': {'min': 11, 'max': 50, 'points': 75, 'badge': '🥈 نقره'},
    '51-100': {'min': 51, 'max': 100, 'points': 150, 'badge': '🥇 طلا'},
    '101-500': {'min': 101, 'max': 500, 'points': 300, 'badge': '💎 الماس'},
    '500+': {'min': 501, 'max': 999999, 'points': 600, 'badge': '👑 افسانه‌ای'},
}

# 12-Level Military Rank Progression - EXPONENTIAL DIFFICULTY
# Early levels: achievable | Mid levels: dedication | High levels: legendary commitment
RANK_THRESHOLDS = {
    '🥉 سرباز': 0,
    '🥉 گروهبان یکم': 50,
    '🥈 ستوان یکم': 120,
    '🥈 ستوان دوم': 220,
    '🥈 سروان': 370,
    '🥇 سرگرد': 600,
    '🥇 سرهنگ': 1000,
    '🎖️ سرتیپ': 1600,
    '⭐ سرتیپ دوم': 2500,
    '💎 سرلشکر': 4000,
    '👑 سپهبد': 6500,
    '👑 مارشال': 10000,
}

# Streak Bonuses
STREAK_BONUSES = {
    7: {'points': 15, 'multiplier': 1.25, 'badge': '🔥'},
    14: {'points': 35, 'multiplier': 1.35, 'badge': '🔥🔥'},
    30: {'points': 100, 'multiplier': 1.5, 'badge': '🔥🔥🔥'},
    100: {'points': 500, 'multiplier': 2.0, 'badge': '💎🔥'},
}

# Daily Combo Bonuses
COMBO_BONUSES = {
    3: {'points': 15, 'badge': '🔥'},
    4: {'points': 30, 'badge': '⚡'},
    5: {'points': 60, 'badge': '💥'},
    7: {'points': 150, 'badge': '🌟'},
}

# Persian UI Texts
TEXTS = {
    'welcome': """سلام {name}! 👋🦁☀️

به *ارتش دیجیتال انقلاب ملی ۱۴۰۴* خوش آمدید!

━━━━━━━━━━━━━━━━━━━━

💡 *چگونه کار می‌کند؟*

هر فعالیت شما = امتیاز 💎
امتیاز بیشتر = ارتقای درجه 🎖️
درجه بالاتر = گواهینامه + پاداش 🏆

━━━━━━━━━━━━━━━━━━━━

🎯 *از کجا شروع کنم؟*

1️⃣ *ساده‌ترین:* 🐦 یک توییت بزن (+12 امتیاز)
2️⃣ *پرامتیاز:* 📧 ایمیل به سازمان‌ها (+500 امتیاز)
3️⃣ *پرتاثیر:* 🌐 اشتراک اینترنت (+25 تا +600)

━━━━━━━━━━━━━━━━━━━━

🔒 *امنیت شما:* اطلاعات شخصی ذخیره نمی‌شود!

💪 هر قدم کوچک، تاثیر بزرگ دارد!""",

    'help': """❓ *راهنمای ارتش دیجیتال*

🦁☀️ *چشم‌انداز ما:*
آزادی ایران از چنگال جمهوری اسلامی — برقراری دموکراسی و آزادی برای ملت ایران.
پرچم ما شیر و خورشید است و رهبر ما شاهزاده رضا پهلوی.

ما برای ایرانی آزاد، دموکراتیک و سکولار مبارزه می‌کنیم. 🦁☀️

━━━━━━━━━━━━━━━━━━━━

⚡ *چه کار کنم؟*
دکمه‌های منوی اصلی را بزنید:

🐦 *توییت عملیاتی* → توییت آماده با هشتگ‌ها (12 امتیاز)
📧 *ایمیل* → ارسال ایمیل به سازمان‌های بین‌المللی (500 امتیاز)
🌐 *Conduit* → اشتراک اینترنت با ایرانیان داخل (25-600 امتیاز)
📋 *گزارش* → گزارش امن به iranopasmigirim.com (100 امتیاز)
🎥 *ویدیو* → ضبط ویدیو به زبان کشورتان (150 امتیاز)

━━━━━━━━━━━━━━━━━━━━

📈 *چطور رشد کنم؟*
• هر روز فعال باشید → *رگه روزانه* = ضریب امتیاز بیشتر!
• چند کار در یک روز → *کمبو* = پاداش اضافی!
• امتیاز جمع کنید → *درجه* بالاتر (سرباز تا مارشال)
• دستاورد کسب کنید → *نشان و گواهینامه* بگیرید

━━━━━━━━━━━━━━━━━━━━

👤 *پروفایل من* — امتیاز و درجه‌ام
🏆 *تابلوی افتخار* — میهن‌پرستان برتر

شما بخشی از تاریخ هستید. برای آزادی! 🦁☀️""",

    'main_menu': '🏠 منوی اصلی',
    
    'email_button': '📧 ارسال ایمیل هدفمند',
    'conduit_button': '🌐 اشتراک اینترنت',
    'tweet_button': '🐦 توییت عملیاتی',
    'media_button': '📋 گزارش میهن‌پرستانه',
    'video_button': '🎬 ویدیوی شهادت جهانی',
    'protests_button': '🦁 تجمعات بین‌المللی',
    'profile_button': '👤 پروفایل من',
    'leaderboard_button': '🏆 تابلوی افتخار',
    'help_button': '❓ راهنما',
    'security_button': '🔒 امنیت و حریم خصوصی',
    
    'security_info': """🔒 امنیت و حریم خصوصی

ـــــــــــــــــــــــــــــــــــــ

1. هویت کاربران
هیچ اطلاعات هویتی از شما ذخیره نمی‌شود. شناسه‌ها یک‌طرفه رمزنگاری شده‌اند.
/security_identity

2. رمزنگاری شناسه
شناسه شما با کلیدهای سمت سرور هش می‌شود. بازگردانی آن ممکن نیست.
/security_hashing

3. داده‌های ذخیره‌شده
فقط امتیاز، نقش و نوع فعالیت ذخیره می‌شود. پیام‌ها و فایل‌ها ذخیره نمی‌شوند.
/security_storage

4. شفافیت کد
کد منبع عمومی و قابل بازبینی است. کلیدها فقط در محیط سرور نگهداری می‌شوند.
/security_code

5. کنترل دسترسی
تغییرات فقط از طریق درخواست رسمی اعمال می‌شوند. ارسال مستقیم به شاخه اصلی مسدود است.
/security_access

ـــــــــــــــــــــــــــــــــــــ
برای حذف داده‌ها: /delete_my_data
کاربران فنی می‌توانند با وارد کردن هر دستور بالا جزئیات بیشتری دریافت کنند.""",

    'security_identity': """🔒 هویت کاربران

ـــــــــــــــــــــــــــــــــــــ

اطلاعات زیر هرگز ذخیره نمی‌شوند:
- نام
- نام کاربری
- شماره تلفن
- موقعیت مکانی

شناسه تلگرام شما به یک مقدار رمزنگاری‌شده یک‌طرفه تبدیل می‌شود. این مقدار تنها شناسه‌ای است که در سیستم وجود دارد.

حتی توسعه‌دهنده سیستم نمی‌تواند از روی این مقدار به هویت واقعی شما برسد.

اگر کسی به داده‌ها دسترسی پیدا کند، فقط یک رشته رمزنگاری‌شده بدون ارتباط با هویت واقعی می‌بیند.

بازگشت به منو: /start""",

    'security_hashing': """🔒 رمزنگاری شناسه

ـــــــــــــــــــــــــــــــــــــ

شناسه شما با استفاده از یک کلید محرمانه و یک مقدار تصادفی سمت سرور هش می‌شود.

نتیجه یک مقدار غیرقابل بازگشت است. یعنی:
- از روی هش نمی‌توان به شناسه اصلی رسید
- حتی با دسترسی کامل به پایگاه داده، بازگردانی ممکن نیست
- کلید محرمانه و مقدار تصادفی فقط در محیط اجرایی سرور وجود دارند، نه در کد

تنها چیزی که در پایگاه داده ذخیره می‌شود همین مقدار هش‌شده است.

بازگشت به منو: /start""",

    'security_storage': """🔒 داده‌های ذخیره‌شده

ـــــــــــــــــــــــــــــــــــــ

آنچه ذخیره می‌شود:
- یک شناسه رمزنگاری‌شده (غیرقابل بازگشت)
- امتیاز عددی
- نقش فعالیتی
- زمان عضویت و آخرین فعالیت
- نوع فعالیت انجام‌شده و امتیاز آن

آنچه ذخیره نمی‌شود:
- پیام‌ها و متن مکالمات
- فایل‌ها، تصاویر و ویدیوها
- اطلاعات جانبی فایل‌ها
- شماره تلفن، نام کاربری یا موقعیت مکانی

سوابق فعالیت پس از یک دوره مشخص به‌صورت خودکار پاک می‌شوند.

برای حذف دستی داده‌ها: /delete_my_data

بازگشت به منو: /start""",

    'security_code': """🔒 شفافیت کد

ـــــــــــــــــــــــــــــــــــــ

کد منبع این ربات به‌صورت عمومی منتشر شده و هر کسی می‌تواند آن را بازبینی کند.

کلیدها و رمزهای سیستم فقط به‌صورت متغیرهای محیطی در سرور وجود دارند. هیچ مقدار محرمانه‌ای در کد منبع یا مخزن عمومی قرار ندارد.

هر تغییر در کد قبل از اعمال، توسط بررسی‌های امنیتی خودکار ارزیابی می‌شود. این بررسی‌ها شامل شناسایی مقادیر محرمانه، تحلیل امنیت کد و بررسی وابستگی‌ها است.

بازگشت به منو: /start""",

    'security_access': """🔒 کنترل دسترسی

ـــــــــــــــــــــــــــــــــــــ

تغییرات کد فقط از طریق درخواست رسمی (Pull Request) اعمال می‌شوند.

ارسال مستقیم کد به شاخه اصلی مسدود است. هیچ تغییری بدون عبور از بررسی‌های خودکار امنیتی پذیرفته نمی‌شود.

سیستم به گونه‌ای طراحی شده که در صورت بروز خطا، به حالت امن بازمی‌گردد. خطاها هرگز اطلاعات حساس را نمایش نمی‌دهند.

دسترسی به مقادیر محرمانه سرور از دسترسی عمومی کاملا جدا است.

بازگشت به منو: /start""",

    'email_intro': """📧 *ارسال ایمیل هدفمند*

یکی از کمپین‌های زیر را انتخاب کنید:

🔹 *سازمان ملل* - درخواست اعمال R2P
🔹 *حمایت بین‌المللی* - از کشورهای دموکراتیک
🔹 *شاهزاده رضا پهلوی* - به رسمیت شناختن

💡 *نکته:* با کلیک روی هر کمپین، متن کامل ایمیل به انگلیسی نمایش داده می‌شود.""",
    
    'email_campaign_un': """*🆘 کمپین سازمان ملل*
    
📌 *موضوع:*
URGENT: Invoke R2P for Iran - Executions Continue

📧 *گیرنده:*
• contact@un.org
• inquiries@ohchr.org

📝 *متن ایمیل:*

Dear UN Officials,

I am writing to urgently request the invocation of the Responsibility to Protect (R2P) doctrine for the people of Iran.

The Iranian regime continues its brutal crackdown on peaceful protesters, with daily executions, torture, and systematic human rights violations. The National Revolution of 1404 represents the Iranian people's legitimate demand for freedom and democracy.

I urge the United Nations to:
1. Invoke R2P to protect Iranian civilians
2. Impose comprehensive sanctions on regime officials
3. Establish a no-fly zone
4. Provide humanitarian aid to protesters

Time is running out. The world cannot remain silent.

Respectfully,
A concerned global citizen supporting the Iranian National Revolution
#NationalRevolution1404

━━━━━━━━━━━━━━━━━━━━━

✅ روی دکمه "ارسال ایمیل" کلیک کنید تا برنامه ایمیل شما باز شود.
✅ پس از ارسال، روی "ایمیل را فرستادم" کلیک کنید.""",

    'email_campaign_military': """*🤝 کمپین حمایت بین‌المللی*

📌 *موضوع:*
Support Iranian National Revolution - International Support Needed

📧 *گیرنده:*
• contact@state.gov
• info@europarl.europa.eu

📝 *متن ایمیل:*

Dear Representatives,

I am writing to request immediate military and logistical support for the Iranian National Revolution of 1404, led by Prince Reza Pahlavi.

The Iranian people are fighting for their freedom against a brutal theocratic regime. They need:
- Intelligence support
- Communication equipment
- Defensive military aid
- Recognition of Prince Reza Pahlavi as the legitimate leader

Supporting this revolution is in the strategic interest of democracy and stability in the Middle East.

Please act now.

Sincerely,
A supporter of Iranian freedom

━━━━━━━━━━━━━━━━━━━━━

✅ روی دکمه "ارسال ایمیل" کلیک کنید تا برنامه ایمیل شما باز شود.
✅ پس از ارسال، روی "ایمیل را فرستادم" کلیک کنید.""",

    'email_campaign_pahlavi': """*👑 کمپین شاهزاده رضا پهلوی*

📌 *موضوع:*
Recognize Prince Reza Pahlavi as Iran's Legitimate Leader

📧 *گیرنده:*
• contact@state.gov
• info@europarl.europa.eu

📝 *متن ایمیل:*

Dear Policy Makers,

I urge you to formally recognize Prince Reza Pahlavi as the legitimate representative of the Iranian people in their struggle for freedom.

Prince Pahlavi has demonstrated:
- Commitment to democratic values
- Support for human rights
- Vision for a free, secular Iran
- International diplomatic experience

Recognizing his leadership will provide legitimacy and structure to the National Revolution of 1404.

The Iranian people deserve your support.

Best regards,
A global advocate for Iranian freedom

━━━━━━━━━━━━━━━━━━━━━

✅ روی دکمه "ارسال ایمیل" کلیک کنید تا برنامه ایمیل شما باز شود.
✅ پس از ارسال، روی "ایمیل را فرستادم" کلیک کنید.""",

    'email_sent_confirmation': """✅ *عالی! ایمیل شما ثبت شد*

🎉 امتیاز دریافتی: +10
📊 مجموع امتیاز: {total}
🏅 درجه: {role}

از مشارکت شما متشکریم! 💪🦁☀️

می‌توانید کمپین‌های دیگر را هم ارسال کنید.""",

    'media_received': """✅ ویدیو دریافت شد!

⏳ *در حال پردازش و پاکسازی متادیتا...*

🔒 اطلاعات GPS و EXIF حذف می‌شود.
لطفاً چند لحظه صبر کنید...""",

    'media_cleaned': """🎉 *ویدیو با موفقیت پردازش شد!*

🔒 تمام اطلاعات شناسایی حذف شد ✓

━━━━━━━━━━━━━━━━━━━━

💎 امتیاز دریافتی: +{points}
📊 مجموع: {total:,} امتیاز
🎖️ درجه: {role}

💪 به کار خود ادامه دهید!""",

    'media_error': """❌ *خطا در پردازش ویدیو*

علل احتمالی:
• فایل ویدیو نیست
• حجم بیش از 50MB است
• فرمت پشتیبانی نمی‌شود

💡 *راه‌حل:*
1. فایل MP4 ارسال کنید
2. حجم را کم کنید
3. دوباره تلاش کنید

مشکل ادامه دارد؟ به منوی اصلی برگردید.""",

    'tweet_generated': """🎯 *توییت عملیاتی آماده است!*

{tweet_text}

━━━━━━━━━━━━━━━━━━━━

👇 *مراحل:*
1️⃣ دکمه "🐦 توییت کن!" را بزنید
2️⃣ در توییتر روی "Tweet" کلیک کنید
3️⃣ برگردید و "✅ توییت کردم" را بزنید

💰 *پاداش:* +12 امتیاز 💎""",

    'tweet_confirmed': """🎉 *عالی! توییت شما ثبت شد!*

+12 امتیاز دریافت کردید! 💎
📊 مجموع امتیاز: {total:,}

💪 به فعالیت ادامه دهید!""",

    'conduit_instructions': """🌐 *عملیات Conduit - اشتراک اینترنت*

این یکی از مهم‌ترین عملیات است! با Psiphon Conduit، شما اینترنت خود را با ایرانیان در داخل کشور به اشتراک می‌گذارید تا بتوانند از سانسور عبور کنند.

⚠️ *توجه مهم: این برنامه فقط برای Windows، Mac و Android است - برای iOS کار نمی‌کند!*

📥 *مراحل نصب:*

1️⃣ به سایت رسمی بروید:
https://conduit.psiphon.ca/en/

2️⃣ دکمه "Download Psiphon Conduit" را کلیک کنید و فایل را دانلود کنید

3️⃣ فایل دانلود شده را نصب کنید:
   • Windows: فایل .exe را اجرا کنید
   • Mac: فایل .dmg را باز کنید
   • Android: فایل .apk را نصب کنید

4️⃣ برنامه را باز کنید - به طور خودکار شروع به اشتراک‌گذاری می‌کند! 🚀

⚙️ *تنظیمات بهینه برای بیشترین تأثیر:*

5️⃣ روی Settings کلیک کنید و این مقادیر را تنظیم کنید:

📊 *Max Peers* → 25 (از 1 تا 25)
این تعداد افرادی است که می‌توانند از شما استفاده کنند

📈 *Max MB/s Per Peer* → 40 (از 8 تا 40)
این سرعت اشتراک‌گذاری برای هر فرد است

6️⃣ دکمه Save را بزنید تا تنظیمات ذخیره شود ✅

7️⃣ برنامه را روشن نگه دارید (حداقل چند ساعت در روز)

📊 *تأیید اعتبار و دریافت امتیاز:*

• بعد از استفاده، یک اسکرین‌شات از برنامه بگیرید
• اسکرین‌شات باید Traffic Stats را نشان دهد (حجم ارسالی)
• اسکرین‌شات را در همین چت ارسال کنید

🏆 *جدول پاداش براساس حجم اشتراک:*

🥉 *1-10 GB* → 25 امتیاز (برنز)
🥈 *11-50 GB* → 75 امتیاز (نقره)
🥇 *51-100 GB* → 150 امتیاز (طلا)
💎 *101-500 GB* → 300 امتیاز (الماس)
👑 *500+ GB* → 600 امتیاز (افسانه‌ای)

این کار واقعاً به ایرانیان کمک می‌کند! 💪🦁☀️

📸 اسکرین‌شات خود را همین‌جا ارسال کنید:""",

    'conduit_screenshot_received': """✅ اسکرین‌شات شما دریافت شد!

🔍 در حال بررسی و تأیید...

این ممکن است چند دقیقه طول بکشد. نتیجه به شما اطلاع داده خواهد شد.""",

    'conduit_data_select': """📊 *چه مقدار اینترنت را به اشتراک گذاشته‌اید؟*

لطفاً میزان حجم اشتراک‌گذاری شده را انتخاب کنید:

هر چه بیشتر به ایرانیان کمک کنید، امتیاز بیشتری دریافت می‌کنید! 🦁☀️""",

    'conduit_verified': """🎉 *تبریک! Conduit تأیید شد!*

شما به ایرانیان کمک کردید! 🦁☀️

━━━━━━━━━━━━━━━━━━━━

{badge}
📦 حجم اشتراک: {data_amount} GB
💎 امتیاز دریافتی: +{points}
📊 مجموع: {total:,} امتیاز
🏅 درجه: {role}

💪 قهرمان واقعی!""",

    'profile_stats': """👤 *پروفایل میهن پرست داوطلب گارد جاویدان*

درجه: {role}
امتیاز: {imtiaz}
رتبه: {rank}
تاریخ عضویت: {joined}

برای ارتقا به درجه بعدی: {next_points} امتیاز دیگر نیاز است

به کارت ادامه بده میهن پرست داوطلب گارد جاویدان! 💪""",

    'leaderboard_header': """🏆 *تابلوی افتخار میهن‌پرستان آزادیخواه*

برترین همراهان ارتش دیجیتال:

""",

    'confirm_button': 'تأیید ✅',
    'back_button': 'بازگشت 🔙',
    
    # Protests Coordination System
    'protests_intro': """🦁☀️ *سامانه هماهنگی تجمعات خارج از کشور*

به بخش تجمعات دیاسپورای ایرانی خوش آمدید!

━━━━━━━━━━━━━━━━━━━━
🔥 *رویداد ویژه: روز جهانی اقدام*
📅 *شنبه ۱۴ فوریه ۲۰۲۶*
🌍 تورنتو • مونیخ • لس‌آنجلس + شهرهای سراسر جهان
✊ همبستگی با انقلاب شیر و خورشید ایران
🔗 RISE IRAN!
━━━━━━━━━━━━━━━━━━━━

*ویژگی‌های این بخش:*

📅 *تقویم تجمعات* - مشاهده و ثبت تجمعات
🧹 *پاکسازی پس از تجمعات* - ما میهمان این کشورها هستیم
📸 *اشتراک‌گذاری رسانه* - عکس و فیلم با پرچم شیر و خورشید
📋 *راهنمای تجمعات* - اصول و آداب شرکت
👥 *ارتباط با هماهنگ‌کنندگان* - دسترسی به سازماندهندگان محلی

🕊️ *ما نماینده ایران آزاد هستیم:*
✅ رفتار مدنی و محترمانه با همه — حتی مخالفان
✅ تقدیم گل به تماشاچیان و مأموران پلیس 🌹
✅ تشکر از نیروهای انتظامی بابت حفاظت از تجمع ما
✅ پاکسازی کامل محل بعد از پایان تجمع
✅ لبخند، مهربانی و عشق به همه مردم کشور میزبان

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:""",

    'protest_calendar_intro': """📅 *تقویم تجمعات جهانی*

تجمعات آینده را مشاهده کنید یا تجمعات جدیدی ثبت کنید.

یک کشور را انتخاب کنید:""",

    'protest_event_details': """📍 *جزئیات تجمعات*

🌍 *کشور:* {country}
🏙️ *شهر:* {city}
📍 *مکان:* {location}
📅 *تاریخ:* {date}
⏰ *ساعت:* {time}
👥 *تعداد شرکت‌کنندگان:* {attendees}
📞 *هماهنگ‌کننده:* {organizer}

💡 *نکات مهم:*
• پرچم شیر و خورشید 🦁☀️، اسرائیل 🇮🇱، آمریکا 🇺🇸 و کشور میزبان
• حفظ نظم و نظافت
• احترام به قوانین محلی

آیا در این تجمعات شرکت خواهید کرد؟""",

    'protest_event_created': """✅ *تجمعات با موفقیت ثبت شد!*

+{points} امتیاز دریافت کردید 🎉

جزئیات تجمعات برای سایر کاربران نمایش داده خواهد شد.

💪 از شما برای سازماندهی متشکریم!""",

    'protest_attendance_confirmed': """✅ *حضور شما ثبت شد!*

+{points} امتیاز دریافت کردید 🎖️

لطفاً فراموش نکنید:
🧹 پس از تجمعات محل را پاکسازی کنید
📸 عکس‌های تجمعات را به اشتراک بگذارید

به امید دیدار در تجمعات! 🦁☀️""",

    'cleanup_campaign_intro': """🧹 *کمپین پاکسازی پس از تجمعات*

ما میهمان این کشورها هستیم. بیایید با پاکسازی محل تجمعات، احترام خود را نشان دهیم.

*چگونه کار می‌کند:*
1️⃣ عکس "قبل" از محل آشفته بگیرید
2️⃣ محل را پاکسازی کنید
3️⃣ عکس "بعد" از محل تمیز بگیرید
4️⃣ هر دو عکس را ارسال کنید

🎁 *پاداش:* 20 امتیاز + نشان ویژه

آیا آماده‌اید؟""",

    'cleanup_photo_before': """📸 *عکس "قبل" را ارسال کنید*

لطفاً عکسی از محل تجمعات قبل از پاکسازی ارسال کنید.

این عکس نشان می‌دهد که محل نیاز به تمیز کردن دارد.""",

    'cleanup_photo_after': """📸 *عالی! حالا عکس "بعد" را ارسال کنید*

عکسی از همان محل بعد از پاکسازی ارسال کنید.

این عکس تلاش شما را نشان خواهد داد! 🧹✨""",

    'cleanup_completed': """🎉 *عالی! پاکسازی تکمیل شد!*

+{points} امتیاز دریافت کردید! 🏆

شما نشان "پاکبان انقلاب" دریافت کردید! 🧹🦁

از شما برای احترام به کشور میزبان متشکریم.
این کار نشان می‌دهد که ما برای آزادی و احترام می‌جنگیم.

به اشتراک‌گذاری با دیگران:""",

    'protest_media_intro': """📸 *اشتراک‌گذاری رسانه تجمعات*

عکس یا ویدیوی خود از تجمعات را ارسال کنید.

*موارد مهم:*
✅ پرچم شیر و خورشید باید مشخص باشد
✅ شعارهای حمایت از شاهزاده رضا پهلوی
✅ رعایت نظم و تمیزی

🎁 *پاداش:* 10 امتیاز به ازای هر رسانه

عکس یا ویدیو خود را ارسال کنید:""",

    'protest_media_received': """✅ *رسانه دریافت شد!*

+{points} امتیاز دریافت کردید! 🎖️

رسانه شما در گالری تجمعات نمایش داده می‌شود.

از شما برای مستندسازی این مبارزه متشکریم! 🦁☀️""",

    'protest_guidelines': """📋 *راهنمای شرکت در تجمعات*

━━━━━━━━━━━━━━━━━━━━
🔥 *رویداد بعدی: ۱۴ فوریه ۲۰۲۶*
روز جهانی اقدام — تورنتو، مونیخ، لس‌آنجلس و شهرهای دیگر
━━━━━━━━━━━━━━━━━━━━

🕊️ *ما صدای صلح و دموکراسی هستیم:*

🌹 *تقدیم گل*
به تماشاچیان، رهگذران و مأموران پلیس گل هدیه دهید. ما نفرت نمی‌آوریم، عشق می‌آوریم.

😊 *لبخند و مهربانی*
با همه مردم کشور میزبان با احترام و لبخند رفتار کنید. از کسانی که می‌ایستند و گوش می‌دهند تشکر کنید.

🤝 *تشکر از پلیس*
با مأموران انتظامی محترمانه برخورد کنید. از آنها بابت حفاظت از حق تجمع ما تشکر کنید. آنها وظیفه‌شان را انجام می‌دهند.

🧹 *پاکسازی کامل*
بعد از هر تجمع، محل را تمیزتر از قبل تحویل دهید. ما میهمان این کشورها هستیم و باید بهترین میهمان باشیم.

📖 *آگاهی‌رسانی مودبانه*
بروشور و اطلاعات درباره وضعیت ایران آماده کنید. با آرامش و منطق با کنجکاوان صحبت کنید.

🦁 *پرچم شیر و خورشید*
از پرچم شیر و خورشید استفاده کنید — نماد وحدت ایرانیان.
پرچم‌های آمریکا، اسرائیل و کشور میزبان نیز خوش‌آمد هستند.

🎵 *سرود و شادی*
با سرود و موسیقی ایرانی فضای مثبت بسازید. کودکان و خانواده‌ها احساس امنیت کنند.

📸 *مستندسازی*
عکس و ویدیو بگیرید تا جهان صدای ما را بشنود.

📢 *شعارها*
\"این آخرین نبرده، پهلوی برمیگرده\"
\"King Reza Pahlavi\"
\"قسم به خون یاران، ایستاده‌ایم تا پایان\"
\"نه غزه، نه لبنان، جانم فدای ایران\"
\"ایران شده آماده، فرمان بده شاهزاده\"

🦁☀️ *ما ایرانیان مغرور و مهربان هستیم*
ما نمایندگان تمدن کهن ایران هستیم، نه طرفدار فلسطین.
ما برای آزادی ایران اینجاییم. تمرکز ما فقط ایران است.

🚫 *ممنوعیت‌ها:*
• خشونت در هر شکل
• تخریب اموال
• پرچم جمهوری اسلامی
• پرچم یا شعار فلسطین
• درگیری با پلیس یا مخالفان
• بی‌احترامی به مردم کشور میزبان

💪 *ما آینده ایران را با عشق و احترام می‌سازیم! 🦁☀️*""",

    'local_organizers_intro': """👥 *هماهنگ‌کنندگان محلی*

برای ارتباط با سازماندهندگان تجمعات در شهر خود:

یک کشور انتخاب کنید:""",

    'organizer_details': """👤 *هماهنگ‌کننده محلی*

🌍 *کشور:* {country}
🏙️ *شهر:* {city}
📱 *تلگرام:* @{telegram_handle}
✅ *تأیید شده:* {verified}
👥 *تعداد داوطلبان:* {volunteers}

برای ارتباط با این هماهنگ‌کننده، روی لینک تلگرام کلیک کنید.

💡 *نکته:* فقط هماهنگ‌کنندگان تأیید شده توسط ادمین نمایش داده می‌شوند.""",

    'countries_list': """🌍 *کشورهای فعال*

کشوری را برای مشاهده تجمعات انتخاب کنید:""",
}

# Email Templates (in English/French/German for international recipients)
EMAIL_TEMPLATES = {
    'un_r2p': {
        'subject': 'URGENT: Invoke R2P for Iran - Executions Continue',
        'recipients': ['contact@un.org', 'inquiries@ohchr.org'],
        'body': """Dear UN Officials,

I am writing to urgently request the invocation of the Responsibility to Protect (R2P) doctrine for the people of Iran.

The Iranian regime continues its brutal crackdown on peaceful protesters, with daily executions, torture, and systematic human rights violations. The National Revolution of 1404 represents the Iranian people's legitimate demand for freedom and democracy.

I urge the United Nations to:
1. Invoke R2P to protect Iranian civilians
2. Impose comprehensive sanctions on regime officials
3. Establish a no-fly zone
4. Provide humanitarian aid to protesters

Time is running out. The world cannot remain silent.

Respectfully,
A concerned global citizen supporting the Iranian National Revolution
#NationalRevolution1404"""
    },
    
    'military_aid': {
        'subject': 'Support Iranian National Revolution - Military Aid Needed',
        'recipients': ['contact@state.gov', 'info@europarl.europa.eu'],
        'body': """Dear Representatives,

I am writing to request immediate military and logistical support for the Iranian National Revolution of 1404, led by Prince Reza Pahlavi.

The Iranian people are fighting for their freedom against a brutal theocratic regime. They need:
- Intelligence support
- Communication equipment
- Defensive military aid
- Recognition of Prince Reza Pahlavi as the legitimate leader

Supporting this revolution is in the strategic interest of democracy and stability in the Middle East.

Please act now.

Sincerely,
A supporter of Iranian freedom"""
    },
    
    'recognize_pahlavi': {
        'subject': 'Recognize Prince Reza Pahlavi as Iran\'s Legitimate Leader',
        'recipients': ['contact@state.gov', 'info@europarl.europa.eu'],
        'body': """Dear Policy Makers,

I urge you to formally recognize Prince Reza Pahlavi as the legitimate representative of the Iranian people in their struggle for freedom.

Prince Pahlavi has demonstrated:
- Commitment to democratic values
- Support for human rights
- Vision for a free, secular Iran
- International diplomatic experience

Recognizing his leadership will provide legitimacy and structure to the National Revolution of 1404.

The Iranian people deserve your support.

Best regards,
A global advocate for Iranian freedom"""
    }
}

# Twitter hashtags
TWITTER_HASHTAGS = ['#IranMassacre', '#IranRevolution2026', '#KingRezaPahlavi', '#FreeIran', '#Iran']

# Email Recipients Database (multiple options for each campaign)
EMAIL_RECIPIENTS = {
    'un_r2p': [
        'contact@un.org',
        'inquiries@ohchr.org',
        'spokesperson@ohchr.org',
        'InfoDesk@ohchr.org',
        'civilsociety@ohchr.org',
        'registry@icj-cij.org',
        'ungeneva@un.org',
        'newyork@un.org',
        'contact@icc-cpi.int',
        'otp.informationdesk@icc-cpi.int',
        'unitednations@unog.ch',
        'press@un.org',
        'humanrights@un.org'
    ],
    'military_aid': [
        'contact@state.gov',
        'info@europarl.europa.eu',
        'secretary@mod.uk',
        'info@diplomatie.gouv.fr',
        'poststelle@auswaertiges-amt.de',
        'info@defense.gov',
        'public@nato.int',
        'info@whitehouse.gov',
        'contact@senate.gov',
        'info@parliament.uk',
        'bundestag@bundestag.de',
        'contact@elysee.fr'
    ],
    'recognize_pahlavi': [
        'contact@state.gov',
        'info@europarl.europa.eu',
        'info@whitehouse.gov',
        'public.enquiries@fco.gov.uk',
        'info@bundestag.de',
        'correspondence@pm.gc.ca',
        'info@premier.gov.au',
        'contact@mfa.gov.il',
        'info@parlamento.it',
        'info@rijksoverheid.nl',
        'kontakt@regjeringen.no',
        'info@government.se'
    ],
    'media': [
        'newstips@bbc.com',
        'tips@cnn.com',
        'tips@reuters.com',
        'contact@france24.com',
        'info@dw.com',
        'news@sky.com',
        'news@foxnews.com',
        'news@aljazeera.net',
        'tips@theguardian.com',
        'news@nytimes.com',
        'news@washingtonpost.com',
        'tips@wsj.com',
        'news@ft.com',
        'contact@economist.com'
    ]
}

# Email Subject Templates with Spintax
EMAIL_SUBJECTS = {
    'un_r2p': [
        "URGENT: {Invoke|Implement|Activate} R2P for Iran - {Executions Continue|Lives at Risk|Crisis Escalating}",
        "{Immediate|Emergency|Urgent} Request: R2P Doctrine for Iranian {Citizens|People|Civilians}",
        "Iran Crisis: {Time to Act|World Must Respond|R2P Needed Now}"
    ],
    'military_aid': [
        "{Support|Aid|Assist} Iranian {National Revolution|Freedom Movement|Democracy Movement}",
        "{Military|Defense|Strategic} Support Needed for Iran's {Liberation|Freedom|Revolution}",
        "{Help|Support|Stand With} Prince Reza Pahlavi and Iranian {Revolution|Freedom Fighters|People}"
    ],
    'recognize_pahlavi': [
        "Recognize Prince Reza Pahlavi as Iran's {Legitimate Leader|True Representative|Democratic Leader}",
        "{Formal Recognition|Official Support|Endorsement} for Prince Reza Pahlavi",
        "Iran's {Future Leader|Democratic Hope|Legitimate Representative}: Prince Reza Pahlavi"
    ],
    'media': [
        "{Interview Request|Story Pitch|Coverage Request}: Prince Reza Pahlavi and Iran's {National Revolution|Freedom Movement|Democracy Movement}",
        "{Major Story|Breaking News|Exclusive}: Iran's {Legitimate Leader|Future|Democratic Hope} - Prince Reza Pahlavi",
        "Media {Coverage|Interview|Feature} Request: The Iranian {Revolution|National Movement|Freedom Struggle} of 1404"
    ]
}

# Email Body Templates with Spintax
EMAIL_BODY_TEMPLATES = {
    'un_r2p': """Dear {UN Officials|Representatives|Distinguished Members},

I am writing to {urgently request|strongly urge|demand} the invocation of the Responsibility to Protect (R2P) doctrine for the {people|citizens|civilians} of Iran.

The Iranian regime {continues|persists with|maintains} its {brutal|violent|savage} crackdown on peaceful protesters, with {daily|ongoing|systematic} {executions|killings|murders}, {torture|abuse|violence}, and systematic human rights violations. The National Revolution of 1404 represents the Iranian people's {legitimate|rightful|just} demand for {freedom|liberty|democracy} and democracy.

I {urge|call upon|request} the United Nations to:
1. {Invoke|Activate|Implement} R2P to protect Iranian civilians
2. Impose {comprehensive|severe|strict} sanctions on regime officials
3. {Establish|Create|Implement} a no-fly zone
4. Provide {humanitarian|emergency|critical} aid to protesters

{Time is running out|The situation is critical|Action is needed now}. The world cannot {remain silent|stay inactive|ignore this crisis}.

{Respectfully|Sincerely|With urgent concern},
A {concerned|dedicated|committed} global citizen supporting the Iranian National Revolution

#NationalRevolution1404 #RezaPahlavi #FreeIran""",

    'military_aid': """Dear {Representatives|Officials|Policy Makers},

I am writing to {request|urge|demand} {immediate|urgent|swift} military and logistical support for the Iranian National Revolution of 1404, {led by|under the leadership of|guided by} Prince Reza Pahlavi.

The Iranian people are {fighting|struggling|battling} for their freedom against a {brutal|oppressive|tyrannical} theocratic regime. They {need|require|desperately need}:
- {Intelligence|Strategic|Tactical} support
- {Communication|Technology|Digital} equipment
- {Defensive|Military|Security} aid
- {Recognition|Official support|Endorsement} of Prince Reza Pahlavi as the legitimate leader

{Supporting|Aiding|Backing} this revolution is in the strategic interest of {democracy|freedom|stability} and stability in the Middle East.

Please {act now|take action|respond urgently}.

{Sincerely|Respectfully|With determination},
A {supporter|advocate|champion} of Iranian freedom

#NationalRevolution1404 #RezaPahlavi""",

    'recognize_pahlavi': """Dear {Policy Makers|Leaders|Distinguished Officials},

I {urge|call upon|request} you to formally recognize Prince Reza Pahlavi as the {legitimate|rightful|true} representative of the Iranian people in their struggle for freedom.

Prince Pahlavi has {demonstrated|shown|proven}:
- {Strong|Unwavering|Deep} commitment to democratic values
- {Dedication|Devotion|Support} for human rights
- {Clear|Compelling|Inspiring} vision for a free, secular Iran
- {Extensive|Significant|Valuable} international diplomatic experience

{Recognizing|Supporting|Endorsing} his leadership will provide {legitimacy|structure|direction} and structure to the National Revolution of 1404.

The Iranian people {deserve|need|require} your support.

{Best regards|Respectfully|Sincerely},
A global {advocate|supporter|champion} for Iranian freedom

#NationalRevolution1404 #RezaPahlavi #FreeIran""",

    'media': """Dear {Editorial Team|News Desk|Producers|Journalists},

I am writing to {request|propose|suggest} a {story|feature|interview|coverage} on Prince Reza Pahlavi and the Iranian National Revolution of 1404.

Prince Reza Pahlavi represents the {legitimate|democratic|rightful} voice of the Iranian people in their {struggle|fight|quest} for freedom from the {oppressive|brutal|tyrannical} theocratic regime. He is the {son|heir|descendant} of the late Shah Mohammad Reza Pahlavi and advocates for a {secular|democratic|free}, democratic Iran based on {human rights|freedom|justice} and the rule of law.

{Key|Important|Newsworthy} story angles:
- {Growing|Massive|Widespread} support among Iranian diaspora and inside Iran
- His {vision|plan|roadmap} for post-regime Iran
- The {ongoing|historic|unprecedented} National Revolution of 1404
- {Strategic|Regional|Geopolitical} implications for Middle East stability
- His {international|diplomatic|global} advocacy and engagement with world leaders

This is a {crucial|critical|historic} moment in Iranian history. The world {needs|deserves|must see} to hear from Iran's {future|next|legitimate} leader.

I {strongly|highly|greatly} encourage you to consider {interviewing|featuring|covering} Prince Reza Pahlavi.

{Thank you|Respectfully|Sincerely},
A {concerned|engaged|dedicated} advocate for {Iranian freedom|democracy|human rights}

#NationalRevolution1404 #RezaPahlavi #FreeIran"""
}

