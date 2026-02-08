"""
Main Bot Application for National Revolution 1404
Telegram Bot for Iranian Diaspora to support the revolution
"""
import asyncio
import logging
import os
import random
import tempfile
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from urllib.parse import quote

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from concurrent.futures import ThreadPoolExecutor

from secure_database_pg import SecureDatabase, get_database
from utils import MediaSecurity, Spintax, ConduitHelper, TextFormatter, validate_environment
from config import (
    BOT_TOKEN,
    WEBAPP_URL,
    TEXTS,
    POINTS,
    EMAIL_TEMPLATES,
    TWITTER_HASHTAGS,
    ENABLE_VIDEO_PROCESSING,
    EMAIL_RECIPIENTS,
    EMAIL_SUBJECTS,
    EMAIL_BODY_TEMPLATES,
    CONDUIT_TIERS,
    USE_SECURE_DATABASE,
    ACTION_LOG_RETENTION_DAYS,
    ADMIN_IDS,
    MEDIA_CHANNEL_ID,
)

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def check_media_cooldown(user_id, action_type, cooldown_minutes=10):
    """SEC-007: Rate limit media uploads to prevent point farming.
    Returns (allowed: bool, remaining_minutes: int)"""
    user_hash = db.get_user_hash(user_id)
    last_action = await db.get_last_action(user_hash, action_type)
    if last_action:
        now = datetime.now(timezone.utc)
        time_since = now - last_action
        if time_since < timedelta(minutes=cooldown_minutes):
            remaining = timedelta(minutes=cooldown_minutes) - time_since
            return False, int(remaining.total_seconds() // 60) + 1
    return True, 0


async def set_media_cooldown(user_id, action_type):
    """Set media cooldown after successful upload"""
    user_hash = db.get_user_hash(user_id)
    await db.set_last_action(user_hash, action_type)


async def forward_to_archive(context, media_type, file_id, caption=""):
    """Forward media to archive channel for documentation"""
    if not MEDIA_CHANNEL_ID:
        return
    try:
        channel_id = int(MEDIA_CHANNEL_ID)
        if media_type == 'photo':
            await context.bot.send_photo(chat_id=channel_id, photo=file_id, caption=caption)
        elif media_type == 'video':
            await context.bot.send_video(chat_id=channel_id, video=file_id, caption=caption)
    except Exception as e:
        logger.error(f"Failed to forward media to archive channel: {e}")

# SEC: Concurrency limiters for resource-intensive operations
SEC_OCR_SEM = asyncio.Semaphore(2)      # Max 2 concurrent OCR jobs
SEC_FFMPEG_SEM = asyncio.Semaphore(1)   # Max 1 concurrent ffmpeg job

# SEC: File size limits (enforce BEFORE download)
MAX_PHOTO_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024   # 50 MB

# SEC: OCR timeout executor
_ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr")

# SEC-001: Fail-closed - require secure database in production
if not USE_SECURE_DATABASE:
    raise RuntimeError(
        "CRITICAL: USE_SECURE_DATABASE must be 'true' in production.\n"
        "Legacy database stores PII and is not permitted."
    )

# Database singleton - initialized via post_init
db: SecureDatabase = get_database()


async def post_init(application: Application) -> None:
    """Post-initialization hook for async database setup."""
    await db.initialize()
    
    if not await db.health_check():
        raise RuntimeError("Database health check failed")
    
    logger.info("✅ Database initialized and healthy")


async def retention_cleanup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback for daily retention cleanup."""
    try:
        deleted = await db.cleanup_old_action_logs()
        if deleted > 0:
            logger.info(f"Retention job: cleaned up {deleted} old action logs")
    except Exception as e:
        logger.error(f"Retention cleanup error: {e}")


async def send_certificate_notification(update: Update, certificate_data: Dict):
    """Send certificate notification to user after rank up"""
    if not certificate_data:
        return
    
    try:
        # Check if physical reward included
        has_physical_reward = 'physical_reward' in certificate_data
        
        message = "🎉 **تبریک! رتبه شما ارتقا یافت!** 🎉\n\n"
        message += "📜 یک گواهینامه دیجیتال برای شما صادر شد!\n\n"
        message += f"🆔 شناسه: `{certificate_data['certificate_id']}`\n\n"
        message += "✅ این گواهینامه:\n"
        message += "• با QR Code قابل تایید است\n"
        message += "• دارای Hash امنیتی بلاکچین است\n"
        message += "• توسط 500+ فعال تایید شده\n"
        message += "• برای همیشه در سیستم ثبت شده\n\n"
        
        # Add physical reward notification
        if has_physical_reward:
            reward = certificate_data['physical_reward']
            message += "🏅 **پاداش فیزیکی ویژه!**\n\n"
            message += "شما برای دریافت پاداش فیزیکی در روز آزادی ایران ثبت‌نام شدید:\n\n"
            message += f"🎖️ نوع: **{reward['reward_type'].replace('_', ' ')}**\n"
            message += f"🔢 شماره سریال: `{reward['serial_number']}`\n"
            message += f"🔐 کد هولوگرام: `{reward['hologram_code']}`\n\n"
            message += "⚠️ این پاداش **غیرقابل تکرار** و **غیرقابل جعل** است!\n"
            message += "✨ در روز پیروزی، این مدال/لوح را دریافت خواهید کرد\n\n"
            message += "📋 بررسی وضعیت: `/my_physical_reward`\n\n"
        
        message += "📥 برای دریافت گواهی: `/get_certificate " + certificate_data['certificate_id'] + "`\n"
        message += "🔍 برای تایید: `/verify_certificate " + certificate_data['certificate_id'] + "`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        # Also send the certificate image
        from certificate_generator import get_certificate_generator
        generator = get_certificate_generator()
        
        # Get the image path (already generated)
        cert_path = certificate_data['image_path']
        
        with open(cert_path, 'rb') as photo:
            caption = "🏆 گواهینامه رسمی شما\nبرای همیشه در تاریخ انقلاب ثبت شد! ✊"
            if has_physical_reward:
                caption += "\n\n🏅 شما واجد شرایط پاداش فیزیکی هستید!"
            
            await update.message.reply_photo(
                photo=photo,
                caption=caption
            )
        
        logger.info("Certificate notification sent" + (" with physical reward" if has_physical_reward else ""))
        
    except Exception as e:
        logger.error(f"Failed to send certificate notification: {e}")


def get_main_keyboard():
    """Get main menu keyboard with Persian buttons"""
    keyboard = [
        [
            KeyboardButton(TEXTS['email_button']),
            KeyboardButton(TEXTS['conduit_button'])
        ],
        [
            KeyboardButton(TEXTS['tweet_button']),
            KeyboardButton(TEXTS['media_button'])
        ],
        [
            KeyboardButton(TEXTS['video_button']),
            KeyboardButton(TEXTS['protests_button'])
        ],
        [
            KeyboardButton(TEXTS['profile_button']),
            KeyboardButton(TEXTS['leaderboard_button'])
        ],
        [
            KeyboardButton(TEXTS['help_button']),
            KeyboardButton(TEXTS['security_button'])
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome new users"""
    user = update.effective_user

    # Add user to database (secure DB only needs user_id)
    await db.add_user(user.id)
    cert_data = await db.add_points(user.id, POINTS['daily_login'], 'daily_login')
    # Send certificate if rank changed
    if cert_data:
        await send_certificate_notification(update, cert_data)

    welcome_text = TEXTS['welcome'].format(
        name=user.first_name or user.username or 'میهن پرست داوطلب گارد جاویدان')

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command - uses TEXTS from config"""
    
    try:
        await update.message.reply_text(
            TEXTS['help'],
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending help message: {e}")
        # Fallback: send without markdown
        await update.message.reply_text(
            "❓ راهنمای ارتش دیجیتال\n\n"
            "از منوی اصلی می‌توانید عملیات‌های مختلف را انجام دهید.\n"
            "برای جزئیات بیشتر به @IRAN_EMAIL_BOT مراجعه کنید.",
            reply_markup=get_main_keyboard()
        )


async def handle_email_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Handle email advocacy button - redirect to @IRAN_EMAIL_BOT with reward"""
    user = update.effective_user

    # Create buttons for confirmation
    keyboard = [
        [InlineKeyboardButton("✅ همه ایمیل‌ها را فرستادم (+500 امتیاز)", callback_data="email_completed")],
        [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    guide_message = """📧 <b>راهنمای کمپین ایمیلی</b>

🎯 <b>مراحل انجام کار:</b>

1️⃣ روی این لینک کلیک کنید و به ربات بروید:
   🤖 <a href='https://t.me/IRAN_EMAIL_BOT'>@IRAN_EMAIL_BOT</a>

2️⃣ دستور /start را بزنید و تمام ایمیل‌های موجود را ارسال کنید

3️⃣ بعد از اتمام ارسال همه ایمیل‌ها، به این ربات برگردید

4️⃣ دکمه "✅ همه ایمیل‌ها را فرستادم" را بزنید

💎 <b>پاداش:</b> 500 امتیاز!

⚠️ توجه: فقط بعد از ارسال همه ایمیل‌ها دکمه تایید را بزنید."""

    await update.message.reply_text(
        guide_message,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def handle_conduit_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Handle Conduit/Psiphon instructions"""
    user = update.effective_user

    await update.message.reply_text(
        TEXTS['conduit_instructions'],
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

    # Set state to expect screenshot
    context.user_data['awaiting_conduit_screenshot'] = True


async def handle_tweet_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Generate randomized tweet with intent link"""
    user = update.effective_user

    # Generate spintax tweet
    tweet_text = Spintax.generate_tweet()

    # Create Twitter intent URL
    encoded_tweet = quote(tweet_text)
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_tweet}"

    keyboard = [
        [InlineKeyboardButton("🐦 توییت کن!", url=twitter_url)],
        [InlineKeyboardButton("✅ توییت کردم - امتیاز بده", callback_data="tweet_confirm")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    formatted_text = TEXTS['tweet_generated'].format(tweet_text=tweet_text)

    await update.message.reply_text(
        formatted_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_media_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Handle patriotic reports button - redirect to Prince Reza Pahlavi's website"""
    
    keyboard = [
        [InlineKeyboardButton("📋 رفتن به صفحه گزارش‌ها", url="https://iranopasmigirim.com/fa/patriotic-reports")],
        [InlineKeyboardButton("✅ گزارش خود را ارسال کردم (+100 امتیاز)", callback_data="report_completed")],
        [InlineKeyboardButton("🔙 بازگشت به منو اصلی", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    guide_message = """📋 <b>گزارش‌های میهن‌پرستانه</b>

🎯 <b>ارسال امن گزارش به شاهزاده رضا پهلوی</b>

🔴 <b>هشدار امنیتی فوری - الزامی است!</b>

⚠️ <b>قبل از کلیک روی لینک حتماً این کارها را انجام دهید:</b>

🔒 <b>الزامی 1:</b> حتماً از حالت ناشناس (Incognito/Private) مرورگر استفاده کنید
   - Chrome: Ctrl+Shift+N
   - Firefox: Ctrl+Shift+P
   - Safari: Cmd+Shift+N

🔒 <b>الزامی 2:</b> VPN معتبر و امن خود را روشن کنید

🔒 <b>الزامی 3:</b> یک ایمیل جدید و مخصوص بسازید

🔒 <b>الزامی 4:</b> از دستگاه شخصی در مکان امن استفاده کنید

━━━━━━━━━━━━━━━━━━━━

<b>مراحل انجام کار:</b>

1️⃣ ابتدا مرورگر را در حالت ناشناس باز کنید (الزامی!)

2️⃣ روی دکمه "📋 رفتن به صفحه گزارش‌ها" کلیک کنید

3️⃣ در سایت رسمی شاهزاده رضا پهلوی:
   • فرم گزارش را پر کنید
   • مستندات و عکس‌های خود را آپلود کنید
   • گزارش خود را ارسال کنید

4️⃣ بعد از ارسال موفق گزارش، به این ربات برگردید

5️⃣ دکمه "✅ گزارش خود را ارسال کردم" را بزنید

💎 <b>پاداش:</b> 100 امتیاز

� <b>پیام شاهزاده رضا پهلوی:</b>

"هر گزارش، هر سند، هر اطلاعات می‌تواند تغییری بزرگ ایجاد کند.

نام قاتلان و جنایتکاران را ثبت کنید! آن‌ها که این دریای خون را در ایران به راه انداختند، بهای سنگینی خواهند پرداخت."

🌐 <b>لینک:</b> iranopasmigirim.com"""

    await update.message.reply_text(
        guide_message,
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


async def handle_video_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Handle video testimonial button"""
    
    msg1 = """🎥 <b>ارتش جهانی ایران آزاد</b>

🌍 جهانیان! وقت اقدام است!

━━━━━━━━━━━━━━━━━━━━

<b>🔥 ماموریت: سلفی ویدیویی</b>

📸 چهره واقعی خود را نشان دهید
🗣️ با صدای بلند از ایران دفاع کنید
🌐 هر زبانی که برای جهانیان صحبت می‌کنید

━━━━━━━━━━━━━━━━━━━━

<b>📱 راهنما</b>

1️⃣ <b>مدت:</b> 30-120 ثانیه
2️⃣ <b>زبان:</b> هر زبانی که بلدید (حتی اگر کامل نباشد!)
3️⃣ <b>پلتفرم:</b> Instagram Reels | TikTok | YouTube Shorts
4️⃣ <b>هشتگ:</b> #RezaPahlavi #IranRevolution #FreeIran #IranNationalRevolution

━━━━━━━━━━━━━━━━━━━━

<b>💡 مثال‌ها (ایرانیان در سراسر جهان)</b>

⚠️ نیازی به حرفه‌ای بودن نیست! هرچقدر بلدید صحبت کنید، خیلی کمک می‌کند!

🇺🇸 "Hello, my name Reza from Iran. I support freedom"
🇩🇪 "Ich bin Ali. Ich komme aus Iran. Freiheit!"
🇫🇷 "Bonjour, je m'appelle Maryam. Vive l'Iran libre!"
🇪🇸 "Hola, soy Amir de Irán. Libertad para mi país"
🇸🇦 "أنا فاطمة من إيران. أدعم الحرية"
🇹🇷 "Benim adım Hossein. İranlıyım. Özgürlük!"
🇮🇹 "Sono Nazanin dall'Iran. Libertà!"
🇵🇹 "Eu sou Kaveh do Irã. Liberdade!"

💪 <b>یادتان باشد:</b> حتی با لهجه، حتی با اشتباه، صدای شما مهم است!
"""

    await update.message.reply_text(msg1, parse_mode='HTML', disable_web_page_preview=True)
    
    msg2 = """━━━━━━━━━━━━━━━━━━━━

💰 <b>سیستم پاداش چند پلتفرمی</b>

📱 <b>پایه:</b>
• 1 پلتفرم: 150 امتیاز
• 2 پلتفرم: 300 امتیاز 
• 3 پلتفرم: 500 امتیاز
• 4+ پلتفرم: 750 امتیاز

🌟 <b>بونوس ویروسی:</b>
• 1K بازدید: +50 امتیاز
• 10K بازدید: +200 امتیاز
• 100K بازدید: +1000 امتیاز
• 1M بازدید: +5000 امتیاز

🎯 <b>اقدامات اضافی:</b>
• استوری: +30 امتیاز
• کامنت پین: +40 امتیاز
• کالاب با اینفلوئنسر: +500 امتیاز
• ریپست سلبریتی: +1000 امتیاز

━━━━━━━━━━━━━━━━━━━━

🎬 <b>5 سناریوی پیشنهادی</b>

1️⃣ <b>خیابانی:</b> در میدان شهر | نام خود + کشور | "Free Iran!"
   مثال: Times Square, Piccadilly, Brandenburger Tor

2️⃣ <b>دانشگاهی:</b> کمپوس | جلوی دانشکده | "Students support Iran"
   مثال: Harvard Yard, Oxford, Sorbonne

3️⃣ <b>ورزشی:</b> لباس تیم ملی | استادیوم | "Sport = Freedom"
   مثال: Bayern jersey, Barca shirt, Lakers gear

4️⃣ <b>فرهنگی:</b> موزه | کتابخانه | اثر تاریخی
   مثال: Louvre, British Museum, Colosseum

5️⃣ <b>خانوادگی:</b> چند نسل | دست‌در‌دست | "Together for Iran"
   مثال: Grandparent + Parent + You

━━━━━━━━━━━━━━━━━━━━

🏆 <b>چالش ویژه: 7 روز</b>

📅 یک ویدیو روزانه = 7x امتیاز
🎁 اتمام چالش: +500 بونوس
💎 پلتفرم‌های مختلف: +1000 بونوس

━━━━━━━━━━━━━━━━━━━━

<b>🦁 انتخاب کنید:</b>"""

    keyboard = [
        [InlineKeyboardButton("✅ 1 پلتفرم (+150)", callback_data="video_1platform")],
        [InlineKeyboardButton("🥈 2 پلتفرم (+300)", callback_data="video_2platform")],
        [InlineKeyboardButton("🥇 3 پلتفرم (+500)", callback_data="video_3platform")],
        [InlineKeyboardButton("💎 4+ پلتفرم (+750)", callback_data="video_4platform")],
        [InlineKeyboardButton("🎯 بازدید بالا (+50-5000)", callback_data="video_viral")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    await update.message.reply_text(msg2, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)


async def handle_profile_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Show user profile with advanced gamification"""
    user = update.effective_user

    stats = await db.get_user_stats(user.id)
    rank = await db.get_user_rank(user.id)

    if stats:
        # Secure database returns dict with keys: imtiaz, role, joined_date
        imtiaz = stats['imtiaz']
        role = stats['role']
        joined_date = stats['joined_date']
        name = "میهن‌پرست"  # No name stored in secure DB

        # Calculate points needed for next rank (12-level system)
        from config import RANK_THRESHOLDS
        rank_list = list(RANK_THRESHOLDS.items())
        
        # Find current and next rank
        next_rank_name = role
        next_points_needed = 0
        progress_percentage = 100
        
        for i, (rank_name, threshold) in enumerate(rank_list):
            if imtiaz < threshold:
                next_rank_name = rank_name
                next_points_needed = threshold - imtiaz
                
                # Calculate progress bar
                if i > 0:
                    prev_threshold = rank_list[i-1][1]
                    rank_range = threshold - prev_threshold
                    progress_in_range = imtiaz - prev_threshold
                    progress_percentage = int((progress_in_range / rank_range) * 100) if rank_range > 0 else 0
                break
        
        # Create progress bar
        filled = int(progress_percentage / 10)
        progress_bar = '█' * filled + '░' * (10 - filled)
        
        # Get streaks
        streaks = await db.get_user_streaks(user.id)
        streak_text = ""
        if streaks:
            top_streak = streaks[0]
            streak_text = f"\n🔥 رگه فعلی: {top_streak.get('current_streak', 0)} روز (بهترین: {top_streak.get('longest_streak', 0)})"
        
        # Get achievements
        achievements = await db.get_user_achievements(user.id)
        achievement_text = ""
        if achievements:
            badges = ' '.join([ach['badge'] for ach in achievements[:5]])  # Show top 5
            achievement_text = f"\n🏆 دستاوردها: {badges} ({len(achievements)} کل)"
        
        # Get daily combo
        combo_info = await db.check_daily_combo(user.id)
        combo_text = ""
        if combo_info['unique_actions'] >= 3:
            combo_text = f"\n{combo_info['badge']} کمبو امروز: {combo_info['unique_actions']}x فعالیت!"
        
        profile_text = f"""👤 پروفایل {name}

🎖️ درجه: {role}
💎 امتیاز: {imtiaz:,}
📊 رتبه جهانی: #{rank}
📅 تاریخ عضویت: {joined_date[:10]}

📈 پیشرفت به {next_rank_name}:
{progress_bar} {progress_percentage}%
{next_points_needed} امتیاز تا ارتقا{streak_text}{achievement_text}{combo_text}

برای پیروزی! 🦁☀️"""

        # Create inline buttons for certificates and badges
        keyboard = [
            [
                InlineKeyboardButton("📜 گواهینامه‌های من", callback_data="my_certificates"),
                InlineKeyboardButton("🎴 کارت درجه من", callback_data="my_rank_card")
            ],
            [
                InlineKeyboardButton("🏆 دستاوردهای من", callback_data="my_achievements")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            profile_text,
            reply_markup=reply_markup
        )


async def handle_leaderboard_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard"""
    leaderboard = await db.get_leaderboard(10)

    if leaderboard:
        formatted = TextFormatter.format_leaderboard(leaderboard)
        await update.message.reply_text(
            formatted,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "هنوز کسی در تابلوی افتخار نیست. اولین نفر باش! 💪",
            reply_markup=get_main_keyboard()
        )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video uploads - strip metadata for security"""
    user = update.effective_user

    # Check for flower gifting video upload
    if context.user_data.get('awaiting_flower_photo', False):
        video = update.message.video
        # SEC-007: Rate limit to prevent point farming
        allowed, remaining = await check_media_cooldown(user.id, 'flower_media')
        if not allowed:
            await update.message.reply_text(
                f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_flower_photo'] = False
            return
        await db.add_protest_media(
            user.id,
            country="Unknown",
            city="Unknown",
            media_type='video',
            file_id=video.file_id,
            caption="flower_gifting"
        )

        cert_data = await db.add_points(user.id, 15, 'flower_gifting')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        await update.message.reply_text(
            "🌹 *عالی! ویدیوی تقدیم گل ثبت شد!*\n\n"
            "+۱۵ امتیاز دریافت کردید! 🏆\n\n"
            "ممنون که با مهربانی و عشق پیام ایران آزاد را منتقل می‌کنید.\n\n"
            "💪 *ما نفرت نمی‌آوریم، عشق می‌آوریم!* 🦁☀️",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Forward to archive channel
        await forward_to_archive(context, 'video', video.file_id, "🌹 تقدیم گل - Flower Gifting")
        await set_media_cooldown(user.id, 'flower_media')

        if cert_data:
            await send_certificate_notification(update, cert_data)

        context.user_data['awaiting_flower_photo'] = False
        return

    # Check for cleanup video upload
    if context.user_data.get('awaiting_cleanup_photo', False):
        video = update.message.video
        cleanup_step = context.user_data.get('cleanup_step')

        if cleanup_step == 'before_photo':
            context.user_data['cleanup_before_photo'] = video.file_id
            context.user_data['cleanup_step'] = 'after_photo'

            await update.message.reply_text(
                TEXTS['cleanup_photo_after'],
                parse_mode='Markdown'
            )
            return

        elif cleanup_step == 'after_photo':
            # SEC-007: Rate limit cleanup uploads
            allowed, remaining = await check_media_cooldown(user.id, 'cleanup_media')
            if not allowed:
                await update.message.reply_text(
                    f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                    reply_markup=get_main_keyboard()
                )
                context.user_data['awaiting_cleanup_photo'] = False
                context.user_data['cleanup_step'] = None
                return
            await db.add_cleanup_action(
                user.id,
                country="Unknown",
                city="Unknown",
                media_type='video',
                file_id=video.file_id,
                caption=None
            )

            cert_data = await db.add_points(user.id, POINTS['protest_cleanup'], 'protest_cleanup')
            stats = await db.get_user_stats(user.id)
            new_score = stats['imtiaz']
            new_role = stats['role']

            await update.message.reply_text(
                TEXTS['cleanup_completed'].format(points=POINTS['protest_cleanup']),
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )

            # Forward both before and after to archive
            before_id = context.user_data.get('cleanup_before_photo')
            if before_id:
                await forward_to_archive(context, 'video', before_id, "🧹 پاکسازی - قبل / Cleanup Before")
            await forward_to_archive(context, 'video', video.file_id, "🧹 پاکسازی - بعد / Cleanup After")
            await set_media_cooldown(user.id, 'cleanup_media')

            if cert_data:
                await send_certificate_notification(update, cert_data)

            context.user_data['awaiting_cleanup_photo'] = False
            context.user_data['cleanup_step'] = None
            context.user_data['cleanup_before_photo'] = None
            return

    # Check for protest media video upload
    if context.user_data.get('awaiting_protest_media', False):
        video = update.message.video
        # SEC-007: Rate limit to prevent point farming
        allowed, remaining = await check_media_cooldown(user.id, 'protest_media')
        if not allowed:
            await update.message.reply_text(
                f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_protest_media'] = False
            return
        await db.add_protest_media(
            user.id,
            country="Unknown",
            city="Unknown",
            media_type='video',
            file_id=video.file_id,
            caption=update.message.caption
        )

        cert_data = await db.add_points(user.id, POINTS['protest_media_shared'], 'protest_media_shared')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        await update.message.reply_text(
            TEXTS['protest_media_received'].format(points=POINTS['protest_media_shared']),
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Forward to archive channel
        await forward_to_archive(context, 'video', video.file_id, "📸 مستندات تجمع - Protest Media")
        await set_media_cooldown(user.id, 'protest_media')

        if cert_data:
            await send_certificate_notification(update, cert_data)

        context.user_data['awaiting_protest_media'] = False
        return

    # Check if user is in media submission flow
    if not context.user_data.get('awaiting_media', False):
        await update.message.reply_text(
            "لطفاً ابتدا دکمه 'ارسال مستندات جنایات' را بزنید.",
            reply_markup=get_main_keyboard()
        )
        return

    await update.message.reply_text(TEXTS['media_received'])

    # Check if video processing is enabled
    if not ENABLE_VIDEO_PROCESSING:
        logger.warning("Video processing disabled - ffmpeg not available")
        await update.message.reply_text(
            "⚠️ **حالت آزمایشی**\n\n"
            "پردازش ویدیو فعلاً غیرفعال است (ffmpeg نصب نیست).\n"
            "ویدیو شما دریافت شد اما متادیتا حذف نشد.\n\n"
            "برای استفاده کامل، ffmpeg را نصب کنید.\n"
            "راهنما: NEXT_STEPS.md",
            parse_mode='Markdown'
        )
        # Award points anyway for testing
        cert_data = await db.add_points(user.id, POINTS['media_submitted'], 'media_submitted_test')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']
        await update.message.reply_text(
            f"✅ امتیاز شما: +{POINTS['media_submitted']}\n"
            f"مجموع: {new_score}\n"
            f"درجه: {new_role}",
            reply_markup=get_main_keyboard()
        )
        
        # Send certificate if rank changed
        if cert_data:
            await send_certificate_notification(update, cert_data)
        context.user_data['awaiting_media'] = False
        return

    # SEC-003: Initialize paths before try for cleanup in finally
    input_path = None
    output_path = None
    try:
        # Download video
        video = update.message.video
        
        # SEC-005: Check file size BEFORE download
        if video.file_size and video.file_size > MAX_VIDEO_SIZE:
            await update.message.reply_text(
                f"❌ حجم ویدیو بیش از حد مجاز است ({MAX_VIDEO_SIZE // (1024*1024)} MB)",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_media'] = False
            return
        
        file = await context.bot.get_file(video.file_id)

        # Create temp files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_input:
            input_path = tmp_input.name
            await file.download_to_drive(input_path)

        # Strip metadata with concurrency limit
        output_path = input_path.replace('.mp4', '_clean.mp4')
        async with SEC_FFMPEG_SEM:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, MediaSecurity.strip_metadata, input_path, output_path)

        # Award points
        cert_data = await db.add_points(user.id, POINTS['media_submitted'], 'media_submitted')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        # Send cleaned video back
        with open(output_path, 'rb') as clean_video:
            await update.message.reply_video(
                clean_video,
                caption=TEXTS['media_cleaned'].format(
                    points=POINTS['media_submitted'],
                    total=new_score,
                    role=new_role
                ),
                parse_mode='Markdown'
            )

        context.user_data['awaiting_media'] = False

    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        await update.message.reply_text(
            TEXTS['media_error'],
            parse_mode='Markdown'
        )
    finally:
        # SEC-003: Always clean up temp files
        for path in (input_path, output_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
        # Fail-safe: always reset awaiting_media state
        context.user_data['awaiting_media'] = False


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads - check if Conduit screenshot or cleanup photos or protest media"""
    user = update.effective_user
    photo = update.message.photo[-1]  # Get highest resolution

    # Check for flower gifting photo upload
    if context.user_data.get('awaiting_flower_photo', False):
        # SEC-007: Rate limit to prevent point farming
        allowed, remaining = await check_media_cooldown(user.id, 'flower_media')
        if not allowed:
            await update.message.reply_text(
                f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_flower_photo'] = False
            return
        await db.add_protest_media(
            user.id,
            country="Unknown",
            city="Unknown",
            media_type='photo',
            file_id=photo.file_id,
            caption="flower_gifting"
        )

        cert_data = await db.add_points(user.id, 15, 'flower_gifting')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        await update.message.reply_text(
            "🌹 *عالی! عکس تقدیم گل ثبت شد!*\n\n"
            "+۱۵ امتیاز دریافت کردید! 🏆\n\n"
            "ممنون که با مهربانی و عشق پیام ایران آزاد را منتقل می‌کنید.\n\n"
            "💪 *ما نفرت نمی‌آوریم، عشق می‌آوریم!* 🦁☀️",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Forward to archive channel
        await forward_to_archive(context, 'photo', photo.file_id, "🌹 تقدیم گل - Flower Gifting")
        await set_media_cooldown(user.id, 'flower_media')

        if cert_data:
            await send_certificate_notification(update, cert_data)

        context.user_data['awaiting_flower_photo'] = False
        return

    # Check for cleanup photo upload
    elif context.user_data.get('awaiting_cleanup_photo', False):
        cleanup_step = context.user_data.get('cleanup_step')

        if cleanup_step == 'before_photo':
            context.user_data['cleanup_before_photo'] = photo.file_id
            context.user_data['cleanup_step'] = 'after_photo'

            await update.message.reply_text(
                TEXTS['cleanup_photo_after'],
                parse_mode='Markdown'
            )

        elif cleanup_step == 'after_photo':
            before_photo_id = context.user_data.get('cleanup_before_photo')
            after_photo_id = photo.file_id

            # SEC-007: Rate limit cleanup uploads
            allowed, remaining = await check_media_cooldown(user.id, 'cleanup_media')
            if not allowed:
                await update.message.reply_text(
                    f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                    reply_markup=get_main_keyboard()
                )
                context.user_data['awaiting_cleanup_photo'] = False
                context.user_data['cleanup_step'] = None
                return

            # Save to database (user will provide location later)
            await db.add_cleanup_action(
                user.id,
                country="Unknown",
                city="Unknown",
                media_type='photo',
                file_id=after_photo_id,
                caption=None
            )

            # Award points
            cert_data = await db.add_points(user.id, POINTS['protest_cleanup'], 'protest_cleanup')
            stats = await db.get_user_stats(user.id)
            new_score = stats['imtiaz']
            new_role = stats['role']

            await update.message.reply_text(
                TEXTS['cleanup_completed'].format(points=POINTS['protest_cleanup']),
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )

            # Forward both before and after to archive
            if before_photo_id:
                await forward_to_archive(context, 'photo', before_photo_id, "🧹 پاکسازی - قبل / Cleanup Before")
            await forward_to_archive(context, 'photo', after_photo_id, "🧹 پاکسازی - بعد / Cleanup After")
            await set_media_cooldown(user.id, 'cleanup_media')
            
            # Send certificate if rank changed
            if cert_data:
                await send_certificate_notification(update, cert_data)

            # Clear state
            context.user_data['awaiting_cleanup_photo'] = False
            context.user_data['cleanup_step'] = None
            context.user_data['cleanup_before_photo'] = None

    # Check for protest media upload
    elif context.user_data.get('awaiting_protest_media', False):
        # SEC-007: Rate limit to prevent point farming
        allowed, remaining = await check_media_cooldown(user.id, 'protest_media')
        if not allowed:
            await update.message.reply_text(
                f"⏰ لطفاً {remaining} دقیقه دیگر صبر کنید.",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_protest_media'] = False
            return
        await db.add_protest_media(
            user.id,
            country="Unknown",
            city="Unknown",
            media_type='photo',
            file_id=photo.file_id,
            caption=update.message.caption
        )

        cert_data = await db.add_points(user.id, POINTS['protest_media_shared'], 'protest_media_shared')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        await update.message.reply_text(
            TEXTS['protest_media_received'].format(points=POINTS['protest_media_shared']),
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Forward to archive channel
        await forward_to_archive(context, 'photo', photo.file_id, "📸 مستندات تجمع - Protest Media")
        await set_media_cooldown(user.id, 'protest_media')
        
        # Send certificate if rank changed
        if cert_data:
            await send_certificate_notification(update, cert_data)

        context.user_data['awaiting_protest_media'] = False

    # Check for Conduit screenshot
    elif context.user_data.get('awaiting_conduit_screenshot', False):
        # This is a Conduit verification screenshot
        await update.message.reply_text(TEXTS['conduit_screenshot_received'])
        
        # SEC-005: Check file size BEFORE download (do NOT store file_id before validation)
        if photo.file_size and photo.file_size > MAX_PHOTO_SIZE:
            await update.message.reply_text(
                f"❌ حجم عکس بیش از حد مجاز است ({MAX_PHOTO_SIZE // (1024*1024)} MB)",
                reply_markup=get_main_keyboard()
            )
            context.user_data['awaiting_conduit_screenshot'] = False
            context.user_data.pop('conduit_screenshot_file_id', None)
            return

        # Store screenshot file_id AFTER passing size validation
        context.user_data['conduit_screenshot_file_id'] = photo.file_id

        # SEC-004: Initialize path for cleanup in finally
        file_path = None
        # Try OCR verification
        try:
            # Download photo
            file = await context.bot.get_file(photo.file_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                file_path = tmp.name
                await file.download_to_drive(file_path)

            # SEC-006: Run OCR with timeout and concurrency limit
            async with SEC_OCR_SEM:
                loop = asyncio.get_running_loop()
                try:
                    ocr_result = await asyncio.wait_for(
                        loop.run_in_executor(_ocr_executor, ConduitHelper.verify_screenshot, file_path),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.error("OCR timeout after 30s")
                    # Clean up all stale OCR/conduit state
                    for key in ('ocr_tier', 'ocr_amount_gb', 'ocr_confidence', 'ocr_raw_text', 'conduit_screenshot_file_id'):
                        context.user_data.pop(key, None)
                    context.user_data['awaiting_conduit_screenshot'] = False
                    ocr_result = {'success': False, 'should_fallback': True}

            # Check if OCR succeeded
            if ocr_result['success'] and not ocr_result['should_fallback']:
                # OCR extracted amount successfully
                tier = ocr_result['tier']
                amount_gb = ocr_result['amount_gb']
                tier_info = CONDUIT_TIERS.get(tier)

                # Store OCR data for confirmation
                context.user_data['ocr_tier'] = tier
                context.user_data['ocr_amount_gb'] = amount_gb
                context.user_data['ocr_confidence'] = ocr_result['confidence']
                context.user_data['ocr_raw_text'] = ocr_result.get(
                    'ocr_raw_text', '')

                # Ask user to confirm
                keyboard = [
                    [InlineKeyboardButton("✅ بله، صحیح است", callback_data=f"conduit_confirm_{tier}")],
                    [InlineKeyboardButton("❌ خیر، خودم انتخاب می‌کنم", callback_data="conduit_manual_select")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"""🤖 *تشخیص خودکار داده:*\n\n{tier_info['badge']}\nحجم اشتراک: {amount_gb:.1f} GB\nامتیاز: {tier_info['points']} ⭐\nدقت تشخیص: {ocr_result['confidence']}%\n\nآیا این مقدار صحیح است؟""",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                context.user_data['awaiting_conduit_screenshot'] = False
                return

        except Exception as e:
            logger.error(f"OCR processing failed: {e}", exc_info=True)
            # Clean up all stale OCR/conduit state on exception
            for key in ('ocr_tier', 'ocr_amount_gb', 'ocr_confidence', 'ocr_raw_text', 'conduit_screenshot_file_id'):
                context.user_data.pop(key, None)
            context.user_data['awaiting_conduit_screenshot'] = False
        finally:
            # SEC-004: Always clean up temp files
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except OSError:
                    pass

        # Fallback to manual selection
        keyboard = [
            [InlineKeyboardButton("🥉 1-10 GB (+25 امتیاز)", callback_data="conduit_tier_1-10")],
            [InlineKeyboardButton("🥈 11-50 GB (+75 امتیاز)", callback_data="conduit_tier_11-50")],
            [InlineKeyboardButton("🥇 51-100 GB (+150 امتیاز)", callback_data="conduit_tier_51-100")],
            [InlineKeyboardButton("💎 101-500 GB (+300 امتیاز)", callback_data="conduit_tier_101-500")],
            [InlineKeyboardButton("👑 500+ GB (+600 امتیاز)", callback_data="conduit_tier_500+")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            TEXTS['conduit_data_select'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

        context.user_data['awaiting_conduit_screenshot'] = False
    else:
        await update.message.reply_text(
            "عکس دریافت شد! برای ارسال اسکرین‌شات Conduit یا رسانه تجمعات، از منوی مربوطه استفاده کنید.",
            reply_markup=get_main_keyboard()
        )


async def handle_protests_button(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Handle protests coordination button"""
    keyboard = [
        [InlineKeyboardButton("📅 تقویم تجمعات", callback_data="protests_calendar")],
        [InlineKeyboardButton("🌹 تقدیم گل به پلیس و مردم", callback_data="protests_flowers")],
        [InlineKeyboardButton("🧹 پاکسازی پس از تجمعات", callback_data="protests_cleanup")],
        [InlineKeyboardButton("📸 اشتراک‌گذاری رسانه", callback_data="protests_media")],
        [InlineKeyboardButton("📋 راهنمای تجمعات", callback_data="protests_guidelines")],
        [InlineKeyboardButton("👥 هماهنگ‌کنندگان محلی", callback_data="protests_organizers")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        TEXTS['protests_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    data = query.data
    
    # SEC-009: Validate callback data against whitelist
    VALID_CALLBACKS = {
        'main_menu', 'tweet_confirm', 'email_completed', 'report_completed',
        'video_viral', 'conduit_manual_select', 'back_to_email_menu',
        'protests_calendar', 'protest_create_new', 'protests_cleanup',
        'protests_media', 'protests_guidelines', 'protests_organizers',
        'protests_flowers', 'protests_menu', 'back_to_profile', 'my_certificates', 'my_rank_card',
        'my_achievements'
    }
    VALID_PREFIXES = (
        'video_', 'email_sent_', 'conduit_confirm_', 'conduit_tier_',
        'protest_country_', 'protest_event_', 'protest_attend_', 'protest_org_',
        'protest_feb14_'
    )
    
    if data not in VALID_CALLBACKS and not any(data.startswith(p) for p in VALID_PREFIXES):
        logger.warning(f"Invalid callback data received: {data[:50]}")
        await query.answer("خطا: داده نامعتبر", show_alert=True)
        return

    if data == "main_menu":
        await query.edit_message_text(
            TEXTS['main_menu'],
            reply_markup=None
        )
        await query.message.reply_text(
            "منوی اصلی:",
            reply_markup=get_main_keyboard()
        )

    elif data == "tweet_confirm":
        # User confirms they tweeted
        # SEC-007: DB-backed rate limiting (PostgreSQL, persists across restarts)
        
        user_hash = db.get_user_hash(user.id)
        last_action = await db.get_last_action(user_hash, 'tweet_confirm')
        
        if last_action:
            now = datetime.now(timezone.utc)
            time_since = now - last_action
            if time_since < timedelta(hours=1):
                remaining = timedelta(hours=1) - time_since
                minutes = int(remaining.total_seconds() // 60)
                await query.answer(
                    f"⏰ لطفاً {minutes} دقیقه دیگر صبر کنید.",
                    show_alert=True
                )
                return
        
        # Set cooldown in DB
        await db.set_last_action(user_hash, 'tweet_confirm')
        
        cert_data = await db.add_points(user.id, POINTS['tweet_shared'], 'tweet_shared')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        await query.edit_message_text(
            TEXTS['tweet_confirmed'].format(total=new_score),
            parse_mode='Markdown'
        )
        if cert_data:
            await send_certificate_notification(query, cert_data)

        await query.message.reply_text(
            "عالی! 💪",
            reply_markup=get_main_keyboard()
        )

    elif data == "email_completed":
        # User confirms they sent all emails in @IRAN_EMAIL_BOT
        # SEC-007: DB-backed rate limiting (PostgreSQL)
        
        user_hash = db.get_user_hash(user.id)
        last_action = await db.get_last_action(user_hash, 'email_completed')
        
        if last_action:
            now = datetime.now(timezone.utc)
            time_since = now - last_action
            if time_since < timedelta(hours=24):
                remaining = timedelta(hours=24) - time_since
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await query.answer(
                    f"⏰ شما امروز این کار را انجام دادید!\n"
                    f"زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه",
                    show_alert=True
                )
                return
        
        # Set DB-backed cooldown
        await db.set_last_action(user_hash, 'email_completed')
        
        cert_data = await db.add_points(user.id, 500, 'email_campaign_completed')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        success_message = f"""✅ <b>عالی! کار شما ثبت شد</b>

🎉 شما به خاطر ارسال همه ایمیل‌ها <b>500 امتیاز</b> دریافت کردید!

💎 امتیاز کل شما: {new_score:,}
🎖️ درجه جدید: {new_role}

ممنون از مشارکت شما! 🦁☀️"""

        await query.edit_message_text(
            success_message,
            parse_mode='HTML'
        )

        await query.message.reply_text(
            "منوی اصلی:",
            reply_markup=get_main_keyboard()
        )
        
        # Send certificate if rank changed
        if cert_data:
            await send_certificate_notification(query, cert_data)

    elif data == "report_completed":
        # User confirms they submitted a patriotic report
        # SEC-007: DB-backed rate limiting (PostgreSQL)
        
        user_hash = db.get_user_hash(user.id)
        last_action = await db.get_last_action(user_hash, 'report_completed')
        
        if last_action:
            now = datetime.now(timezone.utc)
            time_since = now - last_action
            if time_since < timedelta(hours=24):
                remaining = timedelta(hours=24) - time_since
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await query.answer(
                    f"⏰ شما امروز گزارش دادید!\n"
                    f"زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه",
                    show_alert=True
                )
                return
        
        # Set DB-backed cooldown
        await db.set_last_action(user_hash, 'report_completed')
        
        cert_data = await db.add_points(user.id, 100, 'patriotic_report_submitted')
        stats = await db.get_user_stats(user.id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        success_message = f"""✅ <b>گزارش شما ثبت شد</b>

🎉 شما <b>100 امتیاز</b> دریافت کردید!

💎 امتیاز کل: {new_score:,}
🎖️ درجه: {new_role}

ممنون از گزارش میهن‌پرستانه شما! 🦁☀️"""

        await query.edit_message_text(
            success_message,
            parse_mode='HTML'
        )
        
        if cert_data:
            await send_certificate_notification(query, cert_data)

        await query.message.reply_text(
            "منوی اصلی:",
            reply_markup=get_main_keyboard()
        )

    elif data.startswith("video_") and data.endswith("platform"):
        # Consolidated handler for video platform submissions
        platform_config = {
            'video_1platform': (150, '1', 'لینک'),
            'video_2platform': (300, '2', 'لینک‌های'),
            'video_3platform': (500, '3', 'لینک‌های'),
            'video_4platform': (750, '4+', 'لینک‌های'),
        }
        
        if data not in platform_config:
            await query.answer("⚠️ خطا در انتخاب", show_alert=True)
            return
        
        reward, count, link_word = platform_config[data]
        context.user_data['awaiting_video_link'] = data
        context.user_data['video_reward'] = reward
        
        msg = f"""📎 <b>ارسال {link_word} ویدیو ({count} پلتفرم)</b>

✅ لطفاً {link_word} ویدیوی خود را ارسال کنید:
{"(هر لینک در یک خط جداگانه)" if count != '1' else ""}

📱 <b>مثال:</b>
• https://instagram.com/reelexample856
• https://tiktok.com/@username/video/7123456789

⚠️ ادمین فقط محتوای ویدیو را بررسی می‌کند.

💰 پاداش پس از تایید: <b>{reward} امتیاز</b>"""

        await query.edit_message_text(msg, parse_mode='HTML')

    elif data == "video_viral":
        # Request screenshot for viral views
        context.user_data['awaiting_video_link'] = 'video_viral'
        
        msg = """🎯 <b>پاداش بازدید بالا</b>

📸 لطفاً لینک ویدیو + اسکرین‌شات آمار را ارسال کنید:

📊 <b>پاداش‌ها:</b>
• 1K بازدید: +50 امتیاز
• 10K بازدید: +200 امتیاز
• 100K بازدید: +1000 امتیاز
• 1M بازدید: +5000 امتیاز

⚠️ <b>نکته:</b>
1. ابتدا لینک ویدیو را بفرستید
2. سپس اسکرین‌شات آمار را بفرستید

ادمین پس از بررسی، امتیاز را اضافه می‌کند."""

        await query.edit_message_text(
            msg,
            parse_mode='HTML'
        )

    # Redirect all email campaigns to @IRAN_EMAIL_BOT
    elif data in ["email_un_r2p", "email_military_aid", "email_recognize_pahlavi", "email_media"]:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        redirect_message = """📧 <b>کمپین‌های ایمیلی</b>

🚀 برای استفاده از کمپین‌های ایمیلی لطفاً به ربات تخصصی مراجعه کنید:

🤖 <a href='https://t.me/IRAN_EMAIL_BOT'>@IRAN_EMAIL_BOT</a>

👉 فقط روی لینک بالا کلیک کنید و /start را بزنید"""
        
        await query.edit_message_text(redirect_message, parse_mode='HTML', reply_markup=reply_markup)

    # Email sent confirmations - redirect to @IRAN_EMAIL_BOT
    elif data.startswith("email_sent_"):
        keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        redirect_message = """📧 <b>کمپین‌های ایمیلی</b>

🚀 برای استفاده از کمپین‌های ایمیلی لطفاً به ربات تخصصی مراجعه کنید:

🤖 <a href='https://t.me/IRAN_EMAIL_BOT'>@IRAN_EMAIL_BOT</a>

👉 فقط روی لینک بالا کلیک کنید و /start را بزنید"""
        
        await query.edit_message_text(redirect_message, parse_mode='HTML', reply_markup=reply_markup)

    # Conduit OCR confirmation
    elif data.startswith("conduit_confirm_"):
        try:
            tier_name = data.replace("conduit_confirm_", "")
            tier_info = CONDUIT_TIERS.get(tier_name)
            
            # SEC-004: No user IDs in logs (zero-knowledge)
            logger.info(f"Conduit confirm clicked: tier={tier_name}")
            logger.debug(f"User data keys present: {len(context.user_data)} keys")

            if tier_info and context.user_data.get('conduit_screenshot_file_id'):
                screenshot_file_id = context.user_data['conduit_screenshot_file_id']
                amount_gb = context.user_data.get('ocr_amount_gb', 0)
                confidence = context.user_data.get('ocr_confidence', 0)
                ocr_raw_text = context.user_data.get('ocr_raw_text', '')
                points = tier_info['points']
                badge = tier_info['badge']

                # Award points and log verification
                cert_data = await db.add_points(user.id, points, 'conduit_verified')
                await db.log_conduit_verification(user.id, tier_name, amount_gb, points)
                stats = await db.get_user_stats(user.id)
                new_score = stats['imtiaz']
                new_role = stats['role']

                await query.edit_message_text(
                    TEXTS['conduit_verified'].format(
                        badge=badge,
                        data_amount=f"{amount_gb:.1f}",
                        points=points,
                        total=new_score,
                        role=new_role
                    ),
                    parse_mode='Markdown'
                )
                
                # Send certificate if rank changed
                if cert_data:
                    await send_certificate_notification(query, cert_data)

                # Clear user data
                context.user_data.pop('conduit_screenshot_file_id', None)
                context.user_data.pop('ocr_tier', None)
                context.user_data.pop('ocr_amount_gb', None)
                context.user_data.pop('ocr_confidence', None)
                context.user_data.pop('ocr_raw_text', None)

                await query.message.reply_text(
                    "منوی اصلی:",
                    reply_markup=get_main_keyboard()
                )
            else:
                logger.warning(f"Missing data: tier_info={tier_info is not None}, screenshot={context.user_data.get('conduit_screenshot_file_id')}")
                await query.edit_message_text("❌ خطا! لطفاً دوباره اسکرین‌شات ارسال کنید.")
                await query.message.reply_text(
                    "منوی اصلی:",
                    reply_markup=get_main_keyboard()
                )
        except Exception as e:
            logger.error(f"Error in conduit_confirm: {e}", exc_info=True)
            await query.answer("⚠️ خطا در پردازش. لطفاً دوباره تلاش کنید.", show_alert=True)

    # Manual tier selection after OCR
    elif data == "conduit_manual_select":
        keyboard = [
            [InlineKeyboardButton("🥉 1-10 GB (+25 امتیاز)", callback_data="conduit_tier_1-10")],
            [InlineKeyboardButton("🥈 11-50 GB (+75 امتیاز)", callback_data="conduit_tier_11-50")],
            [InlineKeyboardButton("🥇 51-100 GB (+150 امتیاز)", callback_data="conduit_tier_51-100")],
            [InlineKeyboardButton("💎 101-500 GB (+300 امتیاز)", callback_data="conduit_tier_101-500")],
            [InlineKeyboardButton("👑 500+ GB (+600 امتیاز)", callback_data="conduit_tier_500+")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            TEXTS['conduit_data_select'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    # Conduit manual tier selection
    elif data.startswith("conduit_tier_"):
        tier_name = data.replace("conduit_tier_", "")
        tier_info = CONDUIT_TIERS.get(tier_name)

        if tier_info and context.user_data.get('conduit_screenshot_file_id'):
            screenshot_file_id = context.user_data['conduit_screenshot_file_id']
            points = tier_info['points']
            badge = tier_info['badge']

            # Check if OCR data exists (user manually overrode OCR)
            ocr_amount = context.user_data.get('ocr_amount_gb', 0)

            # Award points and log verification
            cert_data = await db.add_points(user.id, points, 'conduit_verified')
            await db.log_conduit_verification(user.id, tier_name, ocr_amount, points)
            stats = await db.get_user_stats(user.id)
            new_score = stats['imtiaz']
            new_role = stats['role']

            await query.edit_message_text(
                TEXTS['conduit_verified'].format(
                    badge=badge,
                    data_amount=tier_name,
                    points=points,
                    total=new_score,
                    role=new_role
                ),
                parse_mode='Markdown'
            )

            # Clear user data
            context.user_data.pop('conduit_screenshot_file_id', None)
            context.user_data.pop('ocr_tier', None)
            context.user_data.pop('ocr_amount_gb', None)
            context.user_data.pop('ocr_confidence', None)
            context.user_data.pop('ocr_raw_text', None)

            await query.message.reply_text(
                "منوی اصلی:",
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text("خطا! لطفاً دوباره اسکرین‌شات ارسال کنید.")

    elif data == "back_to_email_menu":
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        redirect_message = """📧 <b>کمپین‌های ایمیلی</b>

🚀 برای استفاده از کمپین‌های ایمیلی لطفاً به ربات تخصصی مراجعه کنید:

🤖 <a href='https://t.me/IRAN_EMAIL_BOT'>@IRAN_EMAIL_BOT</a>

👉 فقط روی لینک بالا کلیک کنید و /start را بزنید"""
        
        await query.edit_message_text(redirect_message, parse_mode='HTML', reply_markup=reply_markup)

        # Protest System Callbacks
    elif data == "protests_calendar":
        # Show list of countries with protests
        countries = await db.get_unique_countries()
        if not countries:
            countries = [
                "USA",
                "UK",
                "Germany",
                "France",
                "Canada",
                "Sweden",
                "Netherlands",
                "Austria"]

        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(
                f"🌍 {country}", callback_data=f"protest_country_{country}")])
        keyboard.append([InlineKeyboardButton(
            "➕ ثبت تجمعات جدید", callback_data="protest_create_new")])
        keyboard.append([InlineKeyboardButton(
            "🔙 بازگشت", callback_data="protests_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            TEXTS['protest_calendar_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data.startswith("protest_country_"):
        country = data.replace("protest_country_", "")
        events = await db.get_protest_events_by_country(country)
        
        # Feb 14 Global Day of Action - hardcoded event
        feb14_cities = {
            "USA": "Los Angeles",
            "Canada": "Toronto",
            "Germany": "Munich",
            "UK": "London",
            "France": "Paris",
            "Sweden": "Stockholm",
            "Netherlands": "Amsterdam",
            "Austria": "Vienna"
        }
        
        keyboard = []
        
        # Always show Feb 14 event at the top
        feb14_city = feb14_cities.get(country, country)
        keyboard.append([InlineKeyboardButton(
            f"🔥 ۱۴ فوریه - {feb14_city} - روز جهانی اقدام",
            callback_data=f"protest_feb14_{country}"
        )])
        
        if events:
            for event in events[:5]:
                event_id, city, location, date, time, organizer, attendees = event
                keyboard.append([InlineKeyboardButton(
                    f"📍 {city} - {date}",
                    callback_data=f"protest_event_{event_id}"
                )])
        
        keyboard.append([InlineKeyboardButton(
            "➕ ثبت تجمعات جدید", callback_data="protest_create_new")])
        keyboard.append([InlineKeyboardButton(
            "🔙 بازگشت", callback_data="protests_calendar")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📅 *تجمعات در {country}*\n\nتجمعات را انتخاب کنید:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data.startswith("protest_feb14_"):
        country = data.replace("protest_feb14_", "")
        feb14_cities = {
            "USA": "Los Angeles",
            "Canada": "Toronto",
            "Germany": "Munich",
            "UK": "London",
            "France": "Paris",
            "Sweden": "Stockholm",
            "Netherlands": "Amsterdam",
            "Austria": "Vienna"
        }
        city = feb14_cities.get(country, country)

        message_text = f"""🔥 *روز جهانی اقدام — GLOBAL DAY OF ACTION*

━━━━━━━━━━━━━━━━━━━━
🌍 *کشور:* {country}
🏙️ *شهر:* {city}
📅 *تاریخ:* شنبه ۱۴ فوریه ۲۰۲۶ (Saturday February 14, 2026)
✊ *هدف:* همبستگی با انقلاب شیر و خورشید ایران
🔗 *سازماندهی:* RISE IRAN!
━━━━━━━━━━━━━━━━━━━━

🌍 *شهرهای دیگر:* تورنتو • مونیخ • لس‌آنجلس + شهرهای سراسر جهان

🌹 *یادآوری مهم:*
• گل بیاورید و به تماشاچیان و پلیس هدیه دهید
• با لبخند و مهربانی حضور پیدا کنید
• پرچم شیر و خورشید 🦁☀️ همراه داشته باشید
• بعد از تجمع محل را پاکسازی کنید

💪 *همه با هم — ۱۴ فوریه — سراسر جهان!*"""

        keyboard = [
            [InlineKeyboardButton(f"🔙 بازگشت به {country}", callback_data=f"protest_country_{country}")],
            [InlineKeyboardButton("🔙 بازگشت به تقویم", callback_data="protests_calendar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data.startswith("protest_event_"):
        try:
            event_id = int(data.replace("protest_event_", ""))
        except ValueError:
            await query.answer("❓", show_alert=False)
            return
        event = await db.get_protest_event(event_id)

        if event:
            country, city, location, date, time, organizer, attendees = event
            keyboard = [
                [InlineKeyboardButton("✅ شرکت می‌کنم!", callback_data=f"protest_attend_{event_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="protests_calendar")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message_text = TEXTS['protest_event_details'].format(
                country=country,
                city=city,
                location=location,
                date=date,
                time=time,
                attendees=attendees,
                organizer=organizer or "نامشخص"
            )

            await query.edit_message_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    elif data.startswith("protest_attend_"):
        try:
            event_id = int(data.replace("protest_attend_", ""))
        except ValueError:
            await query.answer("❓", show_alert=False)
            return
        success = await db.mark_protest_attendance(event_id, user.id)

        if success:
            cert_data = await db.add_points(user.id, POINTS['protest_attendance'], 'protest_attendance')
            stats = await db.get_user_stats(user.id)
            new_score = stats['imtiaz']
            new_role = stats['role']

            await query.edit_message_text(
                TEXTS['protest_attendance_confirmed'].format(points=POINTS['protest_attendance']),
                parse_mode='Markdown'
            )
            
            # Send certificate if rank changed
            if cert_data:
                await send_certificate_notification(query, cert_data)
        else:
            await query.edit_message_text("شما قبلاً برای این تجمعات ثبت‌نام کرده‌اید.")

            await query.message.reply_text("منوی اصلی:", reply_markup=get_main_keyboard())

    elif data == "protest_create_new":
        # Request social media link for gathering verification
        context.user_data['awaiting_gathering_link'] = True

        keyboard = [[InlineKeyboardButton(
            "🔙 انصراف", callback_data="protests_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            """📝 *ثبت تجمع جدید*

        برای ثبت تجمع، لطفاً لینک پست اینفلوئنسر معتبر (توییتر، اینستاگرام، تلگرام) را که تجمع را اعلام کرده ارسال کنید.

        این لینک توسط مدیران بررسی و در صورت تایید، در تقویم تجمعات قرار می‌گیرد.

        ✅ مثال لینک معتبر:
        • twitter.com/username/status/...
        • instagram.com/p/...
        • t.me/channelname/123

        لینک را ارسال کنید:""",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "protests_flowers":
        context.user_data['awaiting_flower_photo'] = True

        keyboard = [[InlineKeyboardButton(
            "🔙 بازگشت", callback_data="protests_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            TEXTS['flower_campaign_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "protests_cleanup":
        context.user_data['cleanup_step'] = 'before_photo'
        context.user_data['awaiting_cleanup_photo'] = True

        keyboard = [[InlineKeyboardButton(
            "🔙 انصراف", callback_data="protests_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            TEXTS['cleanup_campaign_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        await query.message.reply_text(
            TEXTS['cleanup_photo_before'],
            parse_mode='Markdown'
        )

    elif data == "protests_media":
        context.user_data['awaiting_protest_media'] = True

        keyboard = [[InlineKeyboardButton(
            "🔙 انصراف", callback_data="protests_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            TEXTS['protest_media_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "protests_guidelines":
        keyboard = [[InlineKeyboardButton(
            "🔙 بازگشت", callback_data="protests_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            TEXTS['protest_guidelines'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "protests_organizers":
        countries = [
            "USA",
            "UK",
            "Germany",
            "France",
            "Canada",
            "Sweden",
            "Netherlands",
            "Austria"]

        keyboard = []
        for country in countries:
            keyboard.append([InlineKeyboardButton(
                f"🌍 {country}", callback_data=f"protest_org_{country}")])
        keyboard.append([InlineKeyboardButton(
            "🔙 بازگشت", callback_data="protests_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            TEXTS['local_organizers_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data.startswith("protest_org_"):
        country = data.replace("protest_org_", "")
        organizers = await db.get_organizers_by_country(country)
        
        if organizers:
            text = f"👥 *هماهنگ‌کنندگان در {country}*\n\n"
            for city, handle, volunteers, verified in organizers:
                badge = "✅" if verified else "⏳"
                text += f"{badge} *{city}*\n📱 @{handle}\n👥 {volunteers} داوطلب\n\n"
                
                keyboard = [[InlineKeyboardButton(
                    "🔙 بازگشت", callback_data="protests_organizers")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            keyboard = [[InlineKeyboardButton(
                "🔙 بازگشت", callback_data="protests_organizers")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"هنوز هماهنگ‌کننده‌ای در {country} ثبت نشده است.",
                reply_markup=reply_markup
            )

    elif data == "protests_menu":
        keyboard = [
            [InlineKeyboardButton("📅 تقویم تجمعات", callback_data="protests_calendar")],
            [InlineKeyboardButton("🌹 تقدیم گل به پلیس و مردم", callback_data="protests_flowers")],
            [InlineKeyboardButton("🧹 پاکسازی پس از تجمعات", callback_data="protests_cleanup")],
            [InlineKeyboardButton("📸 اشتراک‌گذاری رسانه", callback_data="protests_media")],
            [InlineKeyboardButton("📋 راهنمای تجمعات", callback_data="protests_guidelines")],
            [InlineKeyboardButton("👥 هماهنگ‌کنندگان محلی", callback_data="protests_organizers")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            TEXTS['protests_intro'],
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif data == "back_to_profile":
        # Return to profile menu from submenus
        stats = await db.get_user_stats(user.id)
        if not stats:
            await query.edit_message_text("❌ خطا در دریافت اطلاعات. /start را بزنید.")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📜 گواهینامه‌ها", callback_data="my_certificates"),
                InlineKeyboardButton("🎴 کارت درجه", callback_data="my_rank_card")
            ],
            [
                InlineKeyboardButton("🏆 دستاوردها", callback_data="my_achievements")
            ],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        imtiaz = stats.get('imtiaz', 0) if isinstance(stats, dict) else stats[2]
        role = stats.get('role', 'سرباز') if isinstance(stats, dict) else stats[3]
        
        await query.edit_message_text(
            f"👤 *پروفایل من*\n\n"
            f"🎖️ درجه: {role}\n"
            f"💎 امتیاز: {imtiaz:,}\n\n"
            f"یک گزینه را انتخاب کنید:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data == "my_certificates":
        # Show user's certificates - convert query to update format
        if not USE_SECURE_DATABASE:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="back_to_profile")]]
            await query.edit_message_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        try:
            certificates = await db.get_user_certificates(user.id)
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="back_to_profile")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if not certificates or len(certificates) == 0:
                await query.edit_message_text(
                    "📜 *گواهینامه‌های من*\n\n"
                    "شما هنوز گواهینامه‌ای دریافت نکرده‌اید.\n\n"
                    "💡 گواهینامه‌ها هنگام ارتقای رتبه صادر می‌شوند!\n\n"
                    "🏆 با جمع‌آوری امتیاز، رتبه خود را ارتقا دهید!",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                return

            message = "📜 *گواهینامه‌های من*\n\n"
            message += f"✅ تعداد گواهینامه‌ها: {len(certificates)}\n\n"
            
            for i, cert in enumerate(certificates[:5], 1):
                message += f"{i}. 🏆 {cert['rank']}\n"
                message += f"   � امتیاز: {cert['imtiaz']:,}\n"
                message += f"   🆔 `{cert['certificate_id']}`\n"
                message += f"   📅 {cert['issued_date'][:10]}\n\n"
            
            if len(certificates) > 5:
                message += f"... و {len(certificates) - 5} گواهینامه دیگر\n\n"
            
            message += "💡 *دریافت تصویر گواهینامه:*\n"
            message += "`/get_certificate CERT-XXXX`"
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="back_to_profile")]]
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Error getting certificates: {e}")
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="back_to_profile")]]
            await query.edit_message_text(
                "📜 *گواهینامه‌های من*\n\n"
                "در حال حاضر گواهینامه‌ای برای نمایش وجود ندارد.\n\n"
                "🏆 با جمع‌آوری امتیاز و ارتقای رتبه، گواهینامه دریافت خواهید کرد! 💪",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif data == "my_rank_card":
        # Generate and send rank card
        if not USE_SECURE_DATABASE:
            await query.answer("⚠️ این ویژگی فقط با پایگاه داده امن فعال است.", show_alert=True)
            return

        await query.answer("در حال ایجاد کارت درجه شما... ⏳")
        
        try:
            stats = await db.get_user_stats(user.id)
            if not stats:
                await query.message.reply_text(
                    "❌ خطا در دریافت اطلاعات شما.\n\n"
                    "لطفاً با /start دوباره شروع کنید."
                )
                return

            rank = await db.get_user_rank(user.id)
            achievements = await db.get_user_achievements(user.id)
            streaks = await db.get_user_streaks(user.id)
            streak = streaks[0]['current_streak'] if streaks else 0

            from certificate_generator import get_certificate_generator
            generator = get_certificate_generator()
            
            card_path = generator.create_rank_card(
                stats['role'],
                stats['imtiaz'],
                len(achievements) if achievements else 0,
                streak,
                rank
            )
            
            with open(card_path, 'rb') as card_file:
                await query.message.reply_photo(
                    photo=card_file,
                    caption=f"🎴 *کارت درجه شما*\n\n🎖️ {stats['role']}\n💎 {stats['imtiaz']:,} امتیاز\n📊 رتبه: #{rank}\n\nاین تصویر را در شبکه‌های اجتماعی به اشتراک بگذارید! 🌟",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error creating rank card: {e}", exc_info=True)
            await query.message.reply_text(
                "❌ خطا در ایجاد کارت درجه.\n\n"
                "لطفاً بعداً تلاش کنید."
            )
    
    elif data == "my_achievements":
        # Show achievements list
        achievements = await db.get_user_achievements(user.id)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پروفایل", callback_data="back_to_profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if achievements:
            text = "🏆 *دستاوردهای شما:*\n\n"
            for ach in achievements[:10]:  # Limit to 10 achievements
                text += f"{ach['badge']} *{ach['name']}*\n"
                text += f"   _{ach['description']}_\n\n"
            if len(achievements) > 10:
                text += f"... و {len(achievements) - 10} دستاورد دیگر!\n\n"
        else:
            text = "🏆 *دستاوردهای من*\n\n"
            text += "هنوز دستاوردی کسب نکرده‌اید.\n\n"
            text += "💡 *چگونه دستاورد کسب کنم؟*\n\n"
            text += "• فعالیت روزانه → رگه‌های فعالیت\n"
            text += "• توییت و ایمیل → تخصص\n"
            text += "• Conduit → قهرمان اینترنت\n"
            text += "• پاکسازی → نشان پاکبان\n\n"
            text += "💪 به فعالیت ادامه دهید!"
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    
    else:
        # Catch-all for unhandled callbacks
        logger.warning(f"Unhandled callback data: {data}")
        await query.answer("⚠️ خطایی رخ داد. لطفاً دوباره تلاश کنید.", show_alert=True)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (button presses)"""
    text = update.message.text

    if text == TEXTS['email_button']:
        await handle_email_button(update, context)

    elif text == TEXTS['conduit_button']:
        await handle_conduit_button(update, context)

    elif text == TEXTS['tweet_button']:
        await handle_tweet_button(update, context)

    elif text == TEXTS['media_button']:
        await handle_media_button(update, context)

    elif text == TEXTS['video_button']:
        await handle_video_button(update, context)

    elif text == TEXTS['protests_button']:
        await handle_protests_button(update, context)

    elif text == TEXTS['profile_button']:
        await handle_profile_button(update, context)

    elif text == TEXTS['leaderboard_button']:
        await handle_leaderboard_button(update, context)

    elif text == TEXTS['help_button']:
        await help_command(update, context)

    elif text == TEXTS['security_button']:
        await handle_security_info(update, context)

    elif context.user_data.get('awaiting_video_link'):
        # Handle video link submission
        links = text.strip()
        user = update.effective_user
        submission_type = context.user_data.get('awaiting_video_link')
        reward = context.user_data.get('video_reward', 150)

        # Validate at least one link
        if any(domain in links.lower() for domain in ['instagram.com', 'tiktok.com', 'youtube.com', 'twitter.com', 'facebook.com', 'youtu.be']):
            # Generate anonymous submission token
            submission_token = secrets.token_hex(8)

            # Store submission
            if 'video_submissions' not in context.bot_data:
                context.bot_data['video_submissions'] = {}

            context.bot_data['video_submissions'][submission_token] = {
                'user_id': user.id,
                'links': links,
                'type': submission_type,
                'reward': reward,
                'timestamp': datetime.now().isoformat()
            }

            # Send to admin for verification
            type_names = {
                'video_1platform': '1 پلتفرم',
                'video_2platform': '2 پلتفرم',
                'video_3platform': '3 پلتفرم',
                'video_4platform': '4+ پلتفرم',
                'video_viral': 'بازدید بالا'
            }

            verification_msg = f"""🎥 *درخواست تایید ویدیوی شهادت*

🔐 شناسه ناشناس: `{submission_token}`
📱 نوع: {type_names.get(submission_type, submission_type)}
💰 پاداش: {reward} امتیاز

🔗 لینک(ها):
{links}

⚠️ *نکته امنیتی:*
هویت کاربر محفوظ است - شما نمی‌توانید او را شناسایی کنید.
فقط محتوای ویدیو را بررسی کنید.

✅ تایید: /approve_video {submission_token}
❌ رد: /reject_video {submission_token}"""

            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(admin_id, verification_msg, parse_mode='Markdown')
                except BaseException:
                    pass

            context.user_data['awaiting_video_link'] = None
            context.user_data['video_reward'] = None

            await update.message.reply_text(
                f"✅ لینک(های) شما دریافت شد!\n\n"
                f"🔐 شناسه ناشناس: `{submission_token}`\n\n"
                f"درخواست شما توسط ادمین بررسی می‌شود.\n"
                f"پس از تایید، {reward} امتیاز به حساب شما اضافه خواهد شد.\n\n"
                f"⏳ زمان بررسی: معمولاً کمتر از 24 ساعت",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ لینک معتبر نیست!\n\n"
                "لطفاً لینک ویدیوی خود را از یکی از این پلتفرم‌ها ارسال کنید:\n\n"
                "• Instagram (Reels)\n"
                "• TikTok\n"
                "• YouTube (Shorts)\n"
                "• Twitter/X\n"
                "• Facebook\n\n"
                "مثال:\n"
                "https://instagram.com/reelexample856",
                reply_markup=get_main_keyboard()
            )

    elif context.user_data.get('awaiting_gathering_link'):
        # Handle gathering social media link submission
        link = text.strip()
        user = update.effective_user

        # Validate link format
        if any(
            domain in link.lower() for domain in [
                'twitter.com',
                't.co',
                'instagram.com',
                't.me',
                'telegram.me']):
            # Generate anonymous submission token
            submission_token = secrets.token_hex(8)

            # Store submission with token (not in database, just in
            # memory/context)
            if 'gathering_submissions' not in context.bot_data:
                context.bot_data['gathering_submissions'] = {}

            context.bot_data['gathering_submissions'][submission_token] = {
                'user_id': user.id,
                'link': link,
                'timestamp': datetime.now().isoformat()
            }

            # Send to admin for verification
            admin_ids = ADMIN_IDS

            verification_msg = f"""📍 *درخواست ثبت تجمع جدید*

🔐 شناسه ناشناس: `{submission_token}`
🔗 لینک: {link}

⚠️ هویت کاربر محفوظ است - شما نمی‌توانید او را شناسایی کنید

برای تایید این تجمع از دستورات زیر استفاده کنید:
✅ /approve_gathering {submission_token}
❌ /reject_gathering {submission_token}"""

            for admin_id in admin_ids:
                try:
                    await context.bot.send_message(admin_id, verification_msg, parse_mode='Markdown')
                except BaseException:
                    pass

            context.user_data['awaiting_gathering_link'] = False

            await update.message.reply_text(
                "✅ لینک شما دریافت شد!\n\n"
                "درخواست شما توسط مدیران بررسی خواهد شد و در صورت تایید، در تقویم تجمعات قرار می‌گیرد.\n\n"
                f"🔐 شناسه ناشناس شما: `{submission_token}`\n\n"
                f"لینک: {link}",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ لینک معتبر نیست!\n\n"
                "لطفاً لینک از توییتر، اینستاگرام یا تلگرام ارسال کنید.\n\n"
                "مثال:\n"
                "• https://twitter.com/username/status/...\n"
                "• https://instagram.com/p/...\n"
                "• https://t.me/channelname/123",
                reply_markup=get_main_keyboard()
            )

    else:
        await update.message.reply_text(
            "از منوی زیر یک گزینه انتخاب کنید:",
            reply_markup=get_main_keyboard()
        )


async def handle_security_info(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display security and privacy information"""
    await update.message.reply_text(
        TEXTS['security_info'],
        reply_markup=get_main_keyboard()
    )
    logger.info("User viewed security information")


async def security_identity_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display identity security details"""
    await update.message.reply_text(TEXTS['security_identity'])


async def security_hashing_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display hashing security details"""
    await update.message.reply_text(TEXTS['security_hashing'])


async def security_storage_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display storage security details"""
    await update.message.reply_text(TEXTS['security_storage'])


async def security_code_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display code transparency details"""
    await update.message.reply_text(TEXTS['security_code'])


async def security_access_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display access control details"""
    await update.message.reply_text(TEXTS['security_access'])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors (anonymized)"""
    logger.error(
        f"Exception while handling an update: {context.error}",
        exc_info=context.error)


# ==================== ADMIN COMMANDS (SECURE DATABASE ONLY) =============

async def admin_stats_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Display aggregate statistics for admin - NO user identities"""
    user_id = update.effective_user.id

    # Check admin authorization
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ دستورات امنیتی فقط با پایگاه داده امن فعال است.")
        return

    # Get anonymous aggregate statistics
    stats = await db.get_aggregate_statistics()

    # Format statistics message (Persian)
    message = "📊 **آمار کلی (ناشناس)**\n\n"
    message += f"👥 تعداد کل کاربران: {stats['total_users']}\n"
    message += f"📶 مجموع دیتا اشتراک‌گذاری شده: {stats['total_gb_shared']:.2f} GB\n"
    message += f"🧹 تعداد کل پاکسازی‌ها: {stats['total_cleanups']}\n"
    message += f"📢 تعداد کل تجمعات: {stats['total_protests']}\n\n"

    # Actions by type
    if stats['actions_by_type']:
        message += "📋 **اقدامات به تفکیک نوع:**\n"
        for action, count in stats['actions_by_type'].items():
            message += f"  • {action}: {count}\n"
        message += "\n"

    # Conduit tier distribution
    if stats['conduit_tier_distribution']:
        message += "💎 **توزیع سطوح Conduit:**\n"
        for tier, count in stats['conduit_tier_distribution'].items():
            message += f"  • {tier}: {count} کاربر\n"
        message += "\n"

    # Protests by country
    if stats['protests_by_country']:
        message += "🌍 **تجمعات به تفکیک کشور:**\n"
        for country, count in stats['protests_by_country'].items():
            message += f"  • {country}: {count}\n"

    message += "\n⚠️ **توجه:** این آمار کاملاً ناشناس است و هیچ اطلاعات شناسایی کاربر ندارد."

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("Admin viewed aggregate statistics (no user IDs)")


async def export_stats_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Export aggregate statistics as CSV for admin"""
    user_id = update.effective_user.id

    # Check admin authorization
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ دستورات امنیتی فقط با پایگاه داده امن فعال است.")
        return

    # Get statistics
    stats = await db.get_aggregate_statistics()

    # Create CSV content
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(['نوع آمار', 'مقدار'])

    # Basic stats
    writer.writerow(['تعداد کل کاربران', stats['total_users']])
    writer.writerow(['مجموع دیتا اشتراک‌گذاری شده (GB)',
                    f"{stats['total_gb_shared']:.2f}"])
    writer.writerow(['تعداد کل پاکسازی‌ها', stats['total_cleanups']])
    writer.writerow(['تعداد کل تجمعات', stats['total_protests']])

    # Actions by type
    writer.writerow([])
    writer.writerow(['اقدامات به تفکیک نوع', ''])
    for action, count in stats['actions_by_type'].items():
        writer.writerow([f'  {action}', count])

    # Conduit tiers
    writer.writerow([])
    writer.writerow(['توزیع سطوح Conduit', ''])
    for tier, count in stats['conduit_tier_distribution'].items():
        writer.writerow([f'  {tier}', count])

    # Protests by country
    writer.writerow([])
    writer.writerow(['تجمعات به تفکیک کشور', ''])
    for country, count in stats['protests_by_country'].items():
        writer.writerow([f'  {country}', count])

    # Send as file
    csv_content = output.getvalue()
    output.close()

    from datetime import datetime
    filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    await update.message.reply_document(
        # BOM for Excel Persian support
        document=csv_content.encode('utf-8-sig'),
        filename=filename,
        caption="📊 آمار ناشناس (بدون اطلاعات شناسایی کاربر)"
    )

    logger.info("Admin exported aggregate statistics (no user IDs)")


async def delete_my_data_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Allow users to delete their activity data (preserves points/role for honor)"""
    user_id = update.effective_user.id

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Delete user data (keeps imtiaz and role)
    await db.delete_user_data(user_id)

    message = "✅ **داده‌های فعالیت شما حذف شد**\n\n"
    message += "🏆 امتیاز و درجه شما حفظ شد (افتخار شما محفوظ است)\n"
    message += "🗑️ تاریخچه اقدامات و تصاویر حذف شد\n\n"
    message += "⚠️ توجه: شناسه هش‌شده شما همچنان در سیستم باقی می‌ماند تا امتیازات شما حفظ شود."

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(
        "User requested data deletion (points preserved, identity protected)")


async def approve_video_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve video submission"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ استفاده: /approve_video [submission_token]")
        return

    submission_token = context.args[0]

    # Get submission data
    if 'video_submissions' not in context.bot_data or submission_token not in context.bot_data['video_submissions']:
        await update.message.reply_text("❌ شناسه نامعتبر یا منقضی شده است.")
        return

    submission = context.bot_data['video_submissions'][submission_token]
    requester_id = submission['user_id']
    reward = submission['reward']
    submission_type = submission['type']
    links = submission['links']

    try:
        # Grant points to user
        cert_data = await db.add_points(requester_id, reward, submission_type)
        stats = await db.get_user_stats(requester_id)
        new_score = stats['imtiaz']
        new_role = stats['role']

        # Notify the user
        await context.bot.send_message(
            requester_id,
            f"✅ *ویدیوی شما تایید شد!*\n\n"
            f"🎉 پاداش: *{reward} امتیاز*\n\n"
            f"💎 امتیاز کل: {new_score:,}\n"
            f"🎖️ درجه: {new_role}\n\n"
            f"🌍 ممنون که صدای ایران آزاد را به جهان رساندید! 🦁☀️",
            parse_mode='Markdown'
        )

        # Remove from pending submissions
        del context.bot_data['video_submissions'][submission_token]

        await update.message.reply_text(
            f"✅ ویدیو با شناسه `{submission_token}` تایید شد.\n\n"
            f"💰 {reward} امتیاز به کاربر ناشناس اضافه شد.\n\n"
            f"🔗 لینک(ها):\n{links}",
            parse_mode='Markdown'
        )
        logger.info(f"Admin (identity protected) approved video {submission_token}")

    except Exception as e:
        logger.error(f"Error approving video: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


async def reject_video_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject video submission"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ استفاده: /reject_video [submission_token]")
        return

    submission_token = context.args[0]

    # Get submission data
    if 'video_submissions' not in context.bot_data or submission_token not in context.bot_data['video_submissions']:
        await update.message.reply_text("❌ شناسه نامعتبر یا منقضی شده است.")
        return

    submission = context.bot_data['video_submissions'][submission_token]
    requester_id = submission['user_id']
    links = submission['links']

    try:
        # Notify the user
        await context.bot.send_message(
            requester_id,
            "❌ *ویدیوی شما تایید نشد*\n\n"
            "متأسفانه محتوای ارسالی شما مطابق با الزامات نبود.\n\n"
            "لطفاً مطمئن شوید که:\n"
            "• ویدیو واقعی و با چهره شماست\n"
            "• محتوا در حمایت از ایران آزاد است\n"
            "• کیفیت ویدیو مناسب است\n"
            "• در پلتفرم اصلی منتشر شده است\n\n"
            "می‌توانید دوباره تلاش کنید.",
            parse_mode='Markdown'
        )

        # Remove from pending submissions
        del context.bot_data['video_submissions'][submission_token]

        await update.message.reply_text(
            f"❌ ویدیو با شناسه `{submission_token}` رد شد.\n\n"
            f"🔗 لینک(ها):\n{links}\n\n"
            f"کاربر ناشناس مطلع شد.",
            parse_mode='Markdown'
        )
        logger.info(f"Admin (identity protected) rejected video {submission_token}")

    except Exception as e:
        logger.error(f"Error rejecting video: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


async def approve_gathering_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Admin command to approve gathering submission"""
    user_id = update.effective_user.id
    admin_ids = ADMIN_IDS

    if user_id not in admin_ids:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ استفاده: /approve_gathering [submission_token]")
        return

    submission_token = context.args[0]

    # Get submission data
    if 'gathering_submissions' not in context.bot_data or submission_token not in context.bot_data[
            'gathering_submissions']:
        await update.message.reply_text("❌ شناسه نامعتبر یا منقضی شده است.")
        return

    submission = context.bot_data['gathering_submissions'][submission_token]
    requester_id = submission['user_id']
    link = submission['link']

    try:
        # Notify the user
        await context.bot.send_message(
            requester_id,
            "✅ *تجمع شما تایید شد!*\n\n"
            "تجمع شما در تقویم قرار گرفت و همه کاربران می‌توانند آن را ببینند.\n\n"
            "از شما برای سازماندهی متشکریم! 🦁☀️",
            parse_mode='Markdown'
        )

        # Remove from pending submissions
        del context.bot_data['gathering_submissions'][submission_token]

        await update.message.reply_text(
            f"✅ تجمع با شناسه `{submission_token}` تایید شد.\n\n"
            f"لینک: {link}\n\n"
            f"کاربر ناشناس به او اطلاع داده شد.",
            parse_mode='Markdown'
        )
        logger.info(
            f"Admin (identity protected) approved gathering {submission_token}")

    except Exception as e:
        logger.error(f"Error approving gathering: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


async def reject_gathering_command(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reject gathering submission"""
    user_id = update.effective_user.id
    admin_ids = ADMIN_IDS

    if user_id not in admin_ids:
        await update.message.reply_text("⛔ این دستور فقط برای مدیران است.")
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ استفاده: /reject_gathering [submission_token]")
        return

    submission_token = context.args[0]

    # Get submission data
    if 'gathering_submissions' not in context.bot_data or submission_token not in context.bot_data[
            'gathering_submissions']:
        await update.message.reply_text("❌ شناسه نامعتبر یا منقضی شده است.")
        return

    submission = context.bot_data['gathering_submissions'][submission_token]
    requester_id = submission['user_id']
    link = submission['link']

    try:
        # Notify the user
        await context.bot.send_message(
            requester_id,
            "❌ *درخواست تجمع رد شد*\n\n"
            "متأسفانه لینک ارسالی شما تایید نشد.\n\n"
            "لطفاً مطمئن شوید که:\n"
            "• لینک از یک اینفلوئنسر معتبر است\n"
            "• اطلاعات تجمع واضح است\n"
            "• تجمع در راستای انقلاب ملی ۱۴۰۴ است\n\n"
            "می‌توانید دوباره تلاش کنید.",
            parse_mode='Markdown'
        )

        # Remove from pending submissions
        del context.bot_data['gathering_submissions'][submission_token]

        await update.message.reply_text(
            f"❌ تجمع با شناسه `{submission_token}` رد شد.\n\n"
            f"لینک: {link}\n\n"
            f"کاربر ناشناس به او اطلاع داده شد.",
            parse_mode='Markdown'
        )
        logger.info(
            f"Admin (identity protected) rejected gathering {submission_token}")

    except Exception as e:
        logger.error(f"Error rejecting gathering: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.")


async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their own stats (imtiaz, role, rank)"""
    user_id = update.effective_user.id

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Get user stats
    stats = await db.get_user_stats(user_id)

    if not stats:
        await update.message.reply_text("شما هنوز ثبت‌نام نکرده‌اید. از /start استفاده کنید.")
        return

    # Get user rank
    rank = await db.get_user_rank(user_id)

    message = "📊 **آمار من**\n\n"
    message += f"🏆 امتیاز: {stats['imtiaz']}\n"
    message += f"🎖️ درجه: {stats['role']}\n"
    message += f"🏅 رتبه: {rank}\n"
    message += f"📅 تاریخ عضویت: {stats['joined_date'][:10]}\n\n"
    message += "⚠️ هویت شما برای مدیر قابل شناسایی نیست (هش‌شده)."

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("User viewed own stats (identity protected)")


async def my_certificates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their digital certificates"""
    user_id = update.effective_user.id

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Get user certificates
    certificates = await db.get_user_certificates(user_id)

    if not certificates:
        await update.message.reply_text(
            "📜 شما هنوز گواهینامه‌ای دریافت نکرده‌اید.\n\n"
            "گواهینامه‌ها به صورت خودکار هنگام ارتقای رتبه صادر می‌شوند! 🏆"
        )
        return

    # Send message about certificates
    message = "📜 **گواهینامه‌های من**\n\n"
    message += f"تعداد گواهینامه‌ها: {len(certificates)}\n\n"
    
    for i, cert in enumerate(certificates[:5], 1):  # Show last 5
        message += f"{i}. 🏆 {cert['rank']}\n"
        message += f"   📊 امتیاز: {cert['imtiaz']:,}\n"
        message += f"   🆔 {cert['certificate_id']}\n"
        message += f"   📅 {cert['issued_date'][:10]}\n\n"
    
    message += "💡 برای دریافت تصویر گواهینامه از دستور:\n"
    message += "`/get_certificate [شناسه]` استفاده کنید\n\n"
    message += "🔍 برای تایید اعتبار از دستور:\n"
    message += "`/verify_certificate [شناسه]` استفاده کنید"

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("User viewed certificates list")


async def get_certificate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send certificate image to user"""
    user_id = update.effective_user.id

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Check if certificate ID provided
    if not context.args:
        await update.message.reply_text(
            "⚠️ لطفاً شناسه گواهینامه را وارد کنید:\n"
            "`/get_certificate CERT-XXXXXXXXXXXX`"
        , parse_mode='Markdown')
        return

    certificate_id = context.args[0]

    # Get user certificates to check ownership
    certificates = await db.get_user_certificates(user_id)
    cert = next((c for c in certificates if c['certificate_id'] == certificate_id), None)

    if not cert:
        await update.message.reply_text("❌ این گواهینامه به شما تعلق ندارد یا یافت نشد.")
        return

    # Generate certificate image
    from certificate_generator import get_certificate_generator
    generator = get_certificate_generator()
    
    try:
        cert_path = generator.create_certificate(
            cert['certificate_id'],
            cert['rank'],
            cert['imtiaz'],
            cert['issued_date'].split('T')[0],
            cert['verification_hash']
        )
        
        # Send certificate image
        with open(cert_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"📜 گواهینامه رسمی\n\n"
                        f"🎖️ درجه: {cert['rank']}\n"
                        f"💎 امتیاز: {cert['imtiaz']:,}\n"
                        f"🆔 {cert['certificate_id']}\n\n"
                        f"🔐 برای تأیید اصالت، شناسه را با دستور /verify بررسی کنید"
            )
        
        logger.info(f"Certificate sent: {certificate_id}")
        
    except Exception as e:
        logger.error(f"Error generating certificate: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی در ایجاد گواهینامه رخ داد. لطفاً دوباره تلاش کنید.")


async def verify_certificate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify a certificate by ID (public command)"""
    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Check if certificate ID provided
    if not context.args:
        await update.message.reply_text(
            "⚠️ لطفاً شناسه گواهینامه را وارد کنید:\n"
            "`/verify_certificate CERT-XXXXXXXXXXXX`"
        , parse_mode='Markdown')
        return

    certificate_id = context.args[0]

    # Verify certificate
    cert_data = await db.verify_certificate(certificate_id)

    if not cert_data:
        await update.message.reply_text("❌ این گواهینامه معتبر نیست یا یافت نشد.")
        return

    message = "✅ **گواهینامه معتبر است!**\n\n"
    message += f"🏆 رتبه: {cert_data['rank']}\n"
    message += f"📊 امتیاز: {cert_data['imtiaz']:,}\n"
    message += f"📅 تاریخ صدور: {cert_data['issued_date'][:10]}\n"
    message += f"🔐 Hash: `{cert_data['verification_hash'][:16]}...`\n\n"
    message += "✅ این گواهینامه توسط سیستم انقلاب ایران صادر شده است."

    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"Certificate verified: {certificate_id}")


async def my_rank_card_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send shareable rank card"""
    user_id = update.effective_user.id

    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return

    # Get user stats
    stats = await db.get_user_stats(user_id)
    if not stats:
        await update.message.reply_text("شما هنوز ثبت‌نام نکرده‌اید. از /start استفاده کنید.")
        return

    # Get additional data
    rank = await db.get_user_rank(user_id)
    achievements = await db.get_user_achievements(user_id)
    streak_data = await db.get_user_streak(user_id)
    streak = streak_data.get('current_streak', 0) if streak_data else 0

    # Generate rank card
    from certificate_generator import get_certificate_generator
    generator = get_certificate_generator()
    
    try:
        card_path = generator.create_rank_card(
            stats['role'],
            stats['imtiaz'],
            len(achievements),
            streak,
            rank
        )
        
        # Send card
        with open(card_path, 'rb') as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"🦁 کارت رتبه شما آماده است!\n\n"
                        f"این تصویر را در شبکه‌های اجتماعی به اشتراک بگذارید 📱\n\n"
                        f"#انقلاب_ایران #رضاشاه"
            )
        
        logger.info("Rank card generated and sent")
        
    except Exception as e:
        logger.error(f"Error generating rank card: {e}", exc_info=True)
        await update.message.reply_text("❌ خطایی در ایجاد کارت رتبه رخ داد. لطفاً دوباره تلاش کنید.")


# ==================== END ADMIN COMMANDS ====================


def main():
    """Start the bot"""
    # Validate environment
    ffmpeg_ok = validate_environment()
    if not ffmpeg_ok:
        logger.warning(
            "⚠️  ffmpeg not found - video metadata stripping will not work")
        logger.warning(
            "⚠️  Set ENABLE_VIDEO_PROCESSING = False in config.py for testing")
        logger.warning(
            "⚠️  Install ffmpeg for production use (see NEXT_STEPS.md)")

    # Check bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set BOT_TOKEN in config.py")
        logger.error("📝 See NEXT_STEPS.md for instructions")
        return

    # Check webapp URL
    if "yourdomain.com" in WEBAPP_URL:
        logger.warning(
            "⚠️  WEBAPP_URL not configured - email campaigns won't work")
        logger.warning("📝 See NEXT_STEPS.md for hosting instructions")

    # Create application with post_init hook for async DB setup
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Schedule daily retention cleanup job via JobQueue
    # Runs every 24 hours, first run 60 seconds after startup
    application.job_queue.run_repeating(
        retention_cleanup_job,
        interval=timedelta(hours=24),
        first=timedelta(seconds=60),
        name="retention_cleanup"
    )

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Admin commands (secure database only)
    application.add_handler(CommandHandler("stats", admin_stats_command))
    application.add_handler(
        CommandHandler(
            "export_stats",
            export_stats_command))
    application.add_handler(
        CommandHandler(
            "approve_video",
            approve_video_command))
    application.add_handler(
        CommandHandler(
            "reject_video",
            reject_video_command))
    application.add_handler(
        CommandHandler(
            "approve_gathering",
            approve_gathering_command))
    application.add_handler(
        CommandHandler(
            "reject_gathering",
            reject_gathering_command))

    # User privacy commands
    application.add_handler(
        CommandHandler(
            "delete_my_data",
            delete_my_data_command))
    application.add_handler(CommandHandler("my_stats", my_stats_command))

    # Security info commands
    application.add_handler(CommandHandler("security_identity", security_identity_command))
    application.add_handler(CommandHandler("security_hashing", security_hashing_command))
    application.add_handler(CommandHandler("security_storage", security_storage_command))
    application.add_handler(CommandHandler("security_code", security_code_command))
    application.add_handler(CommandHandler("security_access", security_access_command))

    # Certificate and recognition commands
    application.add_handler(CommandHandler("my_certificates", my_certificates_command))
    application.add_handler(CommandHandler("get_certificate", get_certificate_command))
    application.add_handler(CommandHandler("verify_certificate", verify_certificate_command))
    application.add_handler(CommandHandler("my_rank_card", my_rank_card_command))

    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Message handlers
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Error handler
    application.add_error_handler(error_handler)

    # Start bot
    logger.info("Bot starting... 🦁☀️")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
