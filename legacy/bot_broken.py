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
from datetime import datetime
from typing import Optional
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

from database import Database
from secure_database import SecureDatabase
from utils import MediaSecurity, Spintax, ConduitHelper, TextFormatter, validate_environment
from config import (BOT_TOKEN, WEBAPP_URL, TEXTS, POINTS, EMAIL_TEMPLATES, TWITTER_HASHTAGS, 
                    ENABLE_VIDEO_PROCESSING, EMAIL_RECIPIENTS, EMAIL_SUBJECTS, EMAIL_BODY_TEMPLATES, CONDUIT_TIERS,
                    USE_SECURE_DATABASE, ADMIN_IDS)

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database (secure or legacy)
if USE_SECURE_DATABASE:
    db = SecureDatabase()
    logger.info("✅ Running with SECURE zero-knowledge database")
else:
    db = Database()
    logger.warning("⚠️ Running with legacy database (not secure)")


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
            KeyboardButton(TEXTS['protests_button']),
            KeyboardButton(TEXTS['profile_button'])
        ],
        [
            KeyboardButton(TEXTS['leaderboard_button']),
            KeyboardButton(TEXTS['help_button'])
        ],
        [
            KeyboardButton(TEXTS['security_button'])
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome new users"""
    user = update.effective_user
    
    # Add user to database (secure DB only needs user_id)
    if USE_SECURE_DATABASE:
        db.add_user(user.id)
        db.add_points(user.id, POINTS['daily_login'], 'daily_login')
    else:
        db.add_user(user.id, user.username, user.first_name)
        db.add_points(user.id, POINTS['daily_login'], 'daily_login', 'User started bot')
    
    welcome_text = TEXTS['welcome'].format(name=user.first_name or user.username or 'میهن پرست داوطلب گارد جاویدان')
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        TEXTS['help'],
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def handle_email_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle email advocacy button - show campaign options"""
    user = update.effective_user
    
    # Create buttons for each email campaign
    keyboard = [
        [InlineKeyboardButton("🆘 سازمان ملل (R2P)", callback_data="email_un_r2p")],
        [InlineKeyboardButton("🤝 حمایت بین‌المللی", callback_data="email_military_aid")],
        [InlineKeyboardButton("👑 شاهزاده رضا پهلوی", callback_data="email_recognize_pahlavi")],
        [InlineKeyboardButton("� پیام به رسانه‌ها", callback_data="email_media")],
        [InlineKeyboardButton("�🔙 بازگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        TEXTS['email_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_conduit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Conduit/Psiphon instructions"""
    user = update.effective_user
    
    await update.message.reply_text(
        TEXTS['conduit_instructions'],
        parse_mode='Markdown',
        disable_web_page_preview=False
    )
    
    # Set state to expect screenshot
    context.user_data['awaiting_conduit_screenshot'] = True


async def handle_tweet_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate randomized tweet with intent link"""
    user = update.effective_user
    
    # Generate spintax tweet
    tweet_text = Spintax.generate_tweet()
    
    # Create Twitter intent URL
    encoded_tweet = quote(tweet_text)
    twitter_url = f"https://twitter.com/intent/tweet?text={encoded_tweet}"
    
    keyboard = [
        [InlineKeyboardButton("� توییت کن!", url=twitter_url)],
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


async def handle_media_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle media submission button"""
    await update.message.reply_text(
        """📹 *ارسال مستندات جنایات*

عکس یا ویدیوی خود را ارسال کنید. ما به صورت خودکار:

🔒 تمام متادیتا را حذف می‌کنیم (GPS, EXIF, زمان)
✅ فایل را برای استفاده امن آماده می‌کنیم
⭐ 15 امتیاز به شما می‌دهیم

*امنیت شما اولویت ماست!*

لطفاً عکس یا ویدیو را ارسال کنید:""",
        parse_mode='Markdown'
    )
    
    context.user_data['awaiting_media'] = True


async def handle_profile_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    user = update.effective_user
    
    stats = db.get_user_stats(user.id)
    rank = db.get_user_rank(user.id)
    
    if stats:
        # Secure database returns dict with keys: imtiaz, role, joined_date
        if USE_SECURE_DATABASE:
            imtiaz = stats['imtiaz']
            role = stats['role']
            joined_date = stats['joined_date']
            name = "میهن‌پرست"  # No name stored in secure DB
        else:
            username, first_name, imtiaz, role, joined_date = stats
            name = username or first_name or "ناشناس"
        
        # Calculate points needed for next rank
        next_rank_points = {
            'سرباز': 50,
            'گروهبان': 100,
            'ستوان': 200,
            'سرگرد': 500,
            'فرمانده': 1000,
            'فرمانده کل': 0
        }
        next_points = next_rank_points.get(role, 0) - imtiaz
        if next_points < 0:
            next_points = 0
        
        profile_text = TEXTS['profile_stats'].format(
            name=name,
            role=role,
            imtiaz=imtiaz,
            rank=rank,
            joined=joined_date[:10],
            next_points=next_points
        )
        
        await update.message.reply_text(
            profile_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )


async def handle_leaderboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard"""
    leaderboard = db.get_leaderboard(10)
    
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
        new_score, new_role = db.add_points(
            user.id, 
            POINTS['media_submitted'], 
            'media_submitted_test',
            f'Video submitted (test mode): {update.message.video.file_id}'
        )
        await update.message.reply_text(
            f"✅ امتیاز شما: +{POINTS['media_submitted']}\n"
            f"مجموع: {new_score}\n"
            f"درجه: {new_role}",
            reply_markup=get_main_keyboard()
        )
        context.user_data['awaiting_media'] = False
        return
    
    try:
        # Download video
        video = update.message.video
        file = await context.bot.get_file(video.file_id)
        
        # Create temp files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_input:
            input_path = tmp_input.name
            await file.download_to_drive(input_path)
        
        # Strip metadata
        output_path = input_path.replace('.mp4', '_clean.mp4')
        MediaSecurity.strip_metadata(input_path, output_path)
        
        # Award points
        new_score, new_role = db.add_points(
            user.id, 
            POINTS['media_submitted'], 
            'media_submitted',
            f'Video submitted: {video.file_id}'
        )
        
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
        
        # Keep video for revolution documentation
        # Files are stored for historical record of the revolution
        # try:
        #     os.remove(output_path)
        # except:
        #     pass
        
        context.user_data['awaiting_media'] = False
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await update.message.reply_text(
            TEXTS['media_error'],
            parse_mode='Markdown'
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads - check if Conduit screenshot or cleanup photos or protest media"""
    user = update.effective_user
    photo = update.message.photo[-1]  # Get highest resolution
    
    # Check for cleanup photo upload
    if context.user_data.get('awaiting_cleanup_photo', False):
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
            
            # Save to database (user will provide location later)
            db.add_cleanup_action(
                user.id,
                location="Protest location",
                country="Unknown",
                city="Unknown",
                before_photo_id=before_photo_id,
                after_photo_id=after_photo_id
            )
            
            # Award points
            new_score, new_role = db.add_points(
                user.id,
                POINTS['protest_cleanup'],
                'protest_cleanup',
                f'Cleanup photos: {before_photo_id}, {after_photo_id}'
            )
            
            await update.message.reply_text(
                TEXTS['cleanup_completed'].format(points=POINTS['protest_cleanup']),
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
            
            # Clear state
            context.user_data['awaiting_cleanup_photo'] = False
            context.user_data['cleanup_step'] = None
            context.user_data['cleanup_before_photo'] = None
    
    # Check for protest media upload
    elif context.user_data.get('awaiting_protest_media', False):
        db.add_protest_media(
            user.id,
            country="Unknown",
            city="Unknown",
            media_type='photo',
            file_id=photo.file_id,
            caption=update.message.caption
        )
        
        new_score, new_role = db.add_points(
            user.id,
            POINTS['protest_media_shared'],
            'protest_media_shared',
            f'Photo: {photo.file_id}'
        )
        
        await update.message.reply_text(
            TEXTS['protest_media_received'].format(points=POINTS['protest_media_shared']),
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        context.user_data['awaiting_protest_media'] = False
    
    # Check for Conduit screenshot
    elif context.user_data.get('awaiting_conduit_screenshot', False):
        # This is a Conduit verification screenshot
        await update.message.reply_text(TEXTS['conduit_screenshot_received'])
        
        # Store screenshot file_id temporarily
        context.user_data['conduit_screenshot_file_id'] = photo.file_id
        
        # Try OCR verification
        try:
            # Download photo
            file = await context.bot.get_file(photo.file_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                file_path = tmp.name
                await file.download_to_drive(file_path)
            
            # Run OCR verification
            ocr_result = ConduitHelper.verify_screenshot(file_path)
            
            # Keep photo for revolution documentation
            # Files are stored for historical record
            # try:
            #     os.unlink(file_path)
            # except:
            #     pass
            
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
                context.user_data['ocr_raw_text'] = ocr_result.get('ocr_raw_text', '')
                
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
        
        # Fallback to manual selection
        keyboard = [
            [InlineKeyboardButton("🥉 1-10 GB (10 امتیاز)", callback_data="conduit_tier_1-10")],
            [InlineKeyboardButton("🥈 11-50 GB (30 امتیاز)", callback_data="conduit_tier_11-50")],
            [InlineKeyboardButton("🥇 51-100 GB (60 امتیاز)", callback_data="conduit_tier_51-100")],
            [InlineKeyboardButton("💎 101-500 GB (120 امتیاز)", callback_data="conduit_tier_101-500")],
            [InlineKeyboardButton("👑 500+ GB (250 امتیاز)", callback_data="conduit_tier_500+")],
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


async def handle_protests_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle protests coordination button"""
    keyboard = [
        [InlineKeyboardButton("📅 تقویم تجمعات", callback_data="protests_calendar")],
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
        new_score, new_role = db.add_points(
            user.id,
            POINTS['tweet_shared'],
            'tweet_shared',
            'Daily tweet confirmed'
        )
        
        await query.edit_message_text(
            TEXTS['tweet_confirmed'].format(total=new_score),
            parse_mode='Markdown'
        )
        
        await query.message.reply_text(
            "عالی! 💪",
            reply_markup=get_main_keyboard()
        )
    
    # Email campaign handlers - Generate random email content and show as copyable text
    elif data == "email_un_r2p":
        # Generate random email content
        subject, body = Spintax.generate_email('un_r2p', EMAIL_SUBJECTS['un_r2p'], EMAIL_BODY_TEMPLATES['un_r2p'])
        
        # Use all recipients
        recipients = EMAIL_RECIPIENTS['un_r2p']
        
        # Create buttons without mailto links
        keyboard = [
        [InlineKeyboardButton("✅ ایمیل را فرستادم", callback_data="email_sent_un")],
        [InlineKeyboardButton("🔄 متن جدید بساز", callback_data="email_un_r2p")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_email_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format recipients as copyable code blocks
    recipients_text = "\n".join([f"`{r}`" for r in recipients])
    
    preview_text = f"""🆘 *کمپین سازمان ملل (R2P)*

📧 *آدرس‌های ایمیل:*
{recipients_text}

📌 *موضوع (Subject):*
`{subject}`

📝 *متن ایمیل (Body):*
```
{body}
```

📞 *دستورالعمل:*
1️⃣ روی متن‌ها بزنید تا کپی شود
2️⃣ اپلیکیشن ایمیل خود را باز کنید
3️⃣ هر 3 ایمیل را بفرستید
4️⃣ دکمه "ایمیل را فرستادم" را بزنید

🔄 برای متن جدید: "متن جدید بساز"""
        
        await query.edit_message_text(preview_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data == "email_military_aid":
        subject, body = Spintax.generate_email('military_aid', EMAIL_SUBJECTS['military_aid'], EMAIL_BODY_TEMPLATES['military_aid'])
        recipients = EMAIL_RECIPIENTS['military_aid']
    
    # Create buttons without mailto links
    keyboard = [
        [InlineKeyboardButton("✅ ایمیل را فرستادم", callback_data="email_sent_military")],
        [InlineKeyboardButton("🔄 متن جدید بساز", callback_data="email_military_aid")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_email_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format recipients as copyable code blocks
    recipients_text = "\n".join([f"`{r}`" for r in recipients])
    
    preview_text = f"""🤝 *کمپین حمایت بین‌المللی*

📧 *آدرس‌های ایمیل:*
{recipients_text}

📌 *موضوع (Subject):*
`{subject}`

📝 *متن ایمیل (Body):*
```
{body}
```

📞 *دستورالعمل:*
1️⃣ روی متن‌ها بزنید تا کپی شود
2️⃣ اپلیکیشن ایمیل خود را باز کنید
3️⃣ هر 3 ایمیل را بفرستید
4️⃣ دکمه "ایمیل را فرستادم" را بزنید

🔄 برای متن جدید: "متن جدید بساز"""
    
    await query.edit_message_text(preview_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data == "email_recognize_pahlavi":
    subject, body = Spintax.generate_email('recognize_pahlavi', EMAIL_SUBJECTS['recognize_pahlavi'], EMAIL_BODY_TEMPLATES['recognize_pahlavi'])
    recipients = EMAIL_RECIPIENTS['recognize_pahlavi']
    
    # Create buttons without mailto links
    keyboard = [
        [InlineKeyboardButton("✅ ایمیل را فرستادم", callback_data="email_sent_pahlavi")],
        [InlineKeyboardButton("🔄 متن جدید بساز", callback_data="email_recognize_pahlavi")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_email_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format recipients as copyable code blocks
    recipients_text = "\n".join([f"`{r}`" for r in recipients])
    
    preview_text = f"""👑 *کمپین شاهزاده رضا پهلوی*

📧 *آدرس‌های ایمیل:*
{recipients_text}

📌 *موضوع (Subject):*
`{subject}`

📝 *متن ایمیل (Body):*
```
{body}
```

📞 *دستورالعمل:*
1️⃣ روی متن‌ها بزنید تا کپی شود
2️⃣ اپلیکیشن ایمیل خود را باز کنید
3️⃣ هر 3 ایمیل را بفرستید
4️⃣ دکمه "ایمیل را فرستادم" را بزنید

🔄 برای متن جدید: "متن جدید بساز"""
    
    await query.edit_message_text(preview_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data == "email_media":
    # Generate random email content for media
    subject, body = Spintax.generate_email('media', EMAIL_SUBJECTS['media'], EMAIL_BODY_TEMPLATES['media'])
    
    # Use all recipients
    recipients = EMAIL_RECIPIENTS['media']
    
    # Create buttons
    keyboard = [
        [InlineKeyboardButton("✅ ایمیل را فرستادم", callback_data="email_sent_media")],
        [InlineKeyboardButton("🔄 متن جدید بساز", callback_data="email_media")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_email_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format recipients as copyable code blocks
    recipients_text = "\n".join([f"`{r}`" for r in recipients])
    
    preview_text = f"""📰 *پیام به رسانه‌ها - شاهزاده رضا پهلوی*

📧 *آدرس‌های ایمیل:*
{recipients_text}

📌 *موضوع (Subject):*
`{subject}`

📝 *متن ایمیل (Body):*
```
{body}
```

📞 *دستورالعمل:*
1️⃣ روی متن‌ها بزنید تا کپی شود
2️⃣ اپلیکیشن ایمیل خود را باز کنید
3️⃣ همه ایمیل‌ها را بفرستید
4️⃣ دکمه "ایمیل را فرستادم" را بزنید

🔄 برای متن جدید: "متن جدید بساز"""
    
    await query.edit_message_text(preview_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Email sent confirmations
    elif data.startswith("email_sent_"):
    new_score, new_role = db.add_points(
        user.id,
        POINTS['email_sent'],
        'email_sent',
        f'Email campaign: {data}'
    )
    
    await query.edit_message_text(
        TEXTS['email_sent_confirmation'].format(total=new_score, role=new_role),
        parse_mode='Markdown'
    )
    
    # Show back to campaigns option
    keyboard = [
        [InlineKeyboardButton("📧 ارسال ایمیل دیگر", callback_data="back_to_email_menu")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "می‌خواهید کمپین دیگری ارسال کنید؟",
        reply_markup=reply_markup
    )
    
    # Conduit OCR confirmation
    elif data.startswith("conduit_confirm_"):
    tier_name = data.replace("conduit_confirm_", "")
    tier_info = CONDUIT_TIERS.get(tier_name)
    
    if tier_info and context.user_data.get('conduit_screenshot_file_id'):
        screenshot_file_id = context.user_data['conduit_screenshot_file_id']
        amount_gb = context.user_data.get('ocr_amount_gb', 0)
        confidence = context.user_data.get('ocr_confidence', 0)
        ocr_raw_text = context.user_data.get('ocr_raw_text', '')
        points = tier_info['points']
        badge = tier_info['badge']
        
        # Log to database with OCR data
        db.log_conduit_verification(
            user.id, 
            screenshot_file_id, 
            tier_name, 
            points,
            ocr_extracted_amount=amount_gb,
            ocr_confidence=confidence,
            verification_method='auto',
            ocr_raw_text=ocr_raw_text[:500]  # Truncate
        )
        
        # Award points
        new_score, new_role = db.add_points(
            user.id,
            points,
            'conduit_verified',
            f'Conduit {tier_name} GB (OCR): {screenshot_file_id}'
        )
        
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
    
    # Manual tier selection after OCR
    elif data == "conduit_manual_select":
    keyboard = [
        [InlineKeyboardButton("🥉 1-10 GB (10 امتیاز)", callback_data="conduit_tier_1-10")],
        [InlineKeyboardButton("🥈 11-50 GB (30 امتیاز)", callback_data="conduit_tier_11-50")],
        [InlineKeyboardButton("🥇 51-100 GB (60 امتیاز)", callback_data="conduit_tier_51-100")],
        [InlineKeyboardButton("💎 101-500 GB (120 امتیاز)", callback_data="conduit_tier_101-500")],
        [InlineKeyboardButton("👑 500+ GB (250 امتیاز)", callback_data="conduit_tier_500+")],
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
        ocr_amount = context.user_data.get('ocr_amount_gb')
        ocr_confidence = context.user_data.get('ocr_confidence', 0)
        ocr_raw_text = context.user_data.get('ocr_raw_text', '')
        
        # Log to database with data amount and points
        db.log_conduit_verification(
            user.id, 
            screenshot_file_id, 
            tier_name, 
            points,
            ocr_extracted_amount=ocr_amount,
            ocr_confidence=ocr_confidence,
            verification_method='manual',
            ocr_raw_text=ocr_raw_text[:500] if ocr_raw_text else None
        )
        
        # Award points
        new_score, new_role = db.add_points(
            user.id,
            points,
            'conduit_verified',
            f'Conduit {tier_name} GB: {screenshot_file_id}'
        )
        
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
    keyboard = [
        [InlineKeyboardButton("🆘 سازمان ملل (R2P)", callback_data="email_un_r2p")],
        [InlineKeyboardButton("🤝 حمایت بین‌المللی", callback_data="email_military_aid")],
        [InlineKeyboardButton("👑 شاهزاده رضا پهلوی", callback_data="email_recognize_pahlavi")],
        [InlineKeyboardButton("� پیام به رسانه‌ها", callback_data="email_media")],
        [InlineKeyboardButton("�🔙 بازگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TEXTS['email_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    # Protest System Callbacks
    elif data == "protests_calendar":
    # Show list of countries with protests
    countries = db.get_unique_countries()
    if not countries:
        countries = ["USA", "UK", "Germany", "France", "Canada", "Sweden", "Netherlands", "Austria"]
    
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"protest_country_{country}")])
    keyboard.append([InlineKeyboardButton("➕ ثبت تجمعات جدید", callback_data="protest_create_new")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="protests_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        TEXTS['protest_calendar_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    elif data.startswith("protest_country_"):
    country = data.replace("protest_country_", "")
    events = db.get_protest_events_by_country(country)
    
    if events:
        keyboard = []
        for event in events[:5]:  # Show max 5 events
            event_id, city, location, date, time, organizer, attendees = event
            keyboard.append([InlineKeyboardButton(
                f"📍 {city} - {date}", 
                callback_data=f"protest_event_{event_id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="protests_calendar")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📅 *تجمعات در {country}*\n\nتجمعات را انتخاب کنید:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("➕ اولین تجمعات را ثبت کنید", callback_data="protest_create_new")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="protests_calendar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"هیچ تجمعاتی در {country} ثبت نشده است.\n\nاولین نفر باشید!",
            reply_markup=reply_markup
        )
    
    elif data.startswith("protest_event_"):
    event_id = int(data.replace("protest_event_", ""))
    event = db.get_protest_event(event_id)
    
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
    event_id = int(data.replace("protest_attend_", ""))
    success = db.mark_protest_attendance(event_id, user.id)
    
    if success:
        new_score, new_role = db.add_points(
            user.id,
            POINTS['protest_attendance'],
            'protest_attendance',
            f'Event {event_id}'
        )
        
        await query.edit_message_text(
            TEXTS['protest_attendance_confirmed'].format(points=POINTS['protest_attendance']),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("شما قبلاً برای این تجمعات ثبت‌نام کرده‌اید.")
    
    await query.message.reply_text("منوی اصلی:", reply_markup=get_main_keyboard())
    
    elif data == "protest_create_new":
    # Request social media link for gathering verification
    context.user_data['awaiting_gathering_link'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="protests_menu")]]
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
    
    elif data == "protests_cleanup":
    context.user_data['cleanup_step'] = 'before_photo'
    context.user_data['awaiting_cleanup_photo'] = True
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="protests_menu")]]
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
    
    keyboard = [[InlineKeyboardButton("🔙 انصراف", callback_data="protests_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TEXTS['protest_media_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    elif data == "protests_guidelines":
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="protests_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TEXTS['protest_guidelines'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    elif data == "protests_organizers":
    countries = ["USA", "UK", "Germany", "France", "Canada", "Sweden", "Netherlands", "Austria"]
    
    keyboard = []
    for country in countries:
        keyboard.append([InlineKeyboardButton(f"🌍 {country}", callback_data=f"protest_org_{country}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="protests_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        TEXTS['local_organizers_intro'],
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    elif data.startswith("protest_org_"):
    country = data.replace("protest_org_", "")
    organizers = db.get_organizers_by_country(country)
    
    if organizers:
        text = f"👥 *هماهنگ‌کنندگان در {country}*\n\n"
        for city, handle, volunteers, verified in organizers:
            badge = "✅" if verified else "⏳"
            text += f"{badge} *{city}*\n📱 @{handle}\n👥 {volunteers} داوطلب\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="protests_organizers")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="protests_organizers")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"هنوز هماهنگ‌کننده‌ای در {country} ثبت نشده است.",
            reply_markup=reply_markup
        )
    
    elif data == "protests_menu":
    keyboard = [
        [InlineKeyboardButton("📅 تقویم تجمعات", callback_data="protests_calendar")],
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
    
    else:
        # Catch-all for unhandled callbacks
        logger.warning(f"Unhandled callback data: {data}")
        await query.answer("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    
    logger.error(f"Error in handle_callback: {e}", exc_info=True)
    try:
        await query.answer("⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید.", show_alert=True)
    except:
        pass


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
    
    elif context.user_data.get('awaiting_gathering_link'):
        # Handle gathering social media link submission
        link = text.strip()
        user = update.effective_user
        
        # Validate link format
        if any(domain in link.lower() for domain in ['twitter.com', 't.co', 'instagram.com', 't.me', 'telegram.me']):
            # Generate anonymous submission token
            submission_token = secrets.token_hex(8)
            
            # Store submission with token (not in database, just in memory/context)
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
                except:
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


async def handle_security_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display security and privacy information"""
    await update.message.reply_text(
        TEXTS['security_info'],
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    logger.info("User viewed security information")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors (anonymized)"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


# ==================== ADMIN COMMANDS (SECURE DATABASE ONLY) ====================

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    stats = db.get_aggregate_statistics()
    
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


async def export_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    stats = db.get_aggregate_statistics()
    
    # Create CSV content
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['نوع آمار', 'مقدار'])
    
    # Basic stats
    writer.writerow(['تعداد کل کاربران', stats['total_users']])
    writer.writerow(['مجموع دیتا اشتراک‌گذاری شده (GB)', f"{stats['total_gb_shared']:.2f}"])
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
        document=csv_content.encode('utf-8-sig'),  # BOM for Excel Persian support
        filename=filename,
        caption="📊 آمار ناشناس (بدون اطلاعات شناسایی کاربر)"
    )
    
    logger.info("Admin exported aggregate statistics (no user IDs)")


async def delete_my_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to delete their activity data (preserves points/role for honor)"""
    user_id = update.effective_user.id
    
    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return
    
    # Delete user data (keeps imtiaz and role)
    db.delete_user_data(user_id)
    
    message = "✅ **داده‌های فعالیت شما حذف شد**\n\n"
    message += "🏆 امتیاز و درجه شما حفظ شد (افتخار شما محفوظ است)\n"
    message += "🗑️ تاریخچه اقدامات و تصاویر حذف شد\n\n"
    message += "⚠️ توجه: شناسه هش‌شده شما همچنان در سیستم باقی می‌ماند تا امتیازات شما حفظ شود."
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("User requested data deletion (points preserved, identity protected)")


async def approve_gathering_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if 'gathering_submissions' not in context.bot_data or submission_token not in context.bot_data['gathering_submissions']:
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
        logger.info(f"Admin {user_id} approved gathering {submission_token} (user identity protected)")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال پیام: {str(e)}")


async def reject_gathering_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    if 'gathering_submissions' not in context.bot_data or submission_token not in context.bot_data['gathering_submissions']:
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
        logger.info(f"Admin {user_id} rejected gathering {submission_token} (user identity protected)")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در ارسال پیام: {str(e)}")


async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their own stats (imtiaz, role, rank)"""
    user_id = update.effective_user.id
    
    if not USE_SECURE_DATABASE:
        await update.message.reply_text("⚠️ این دستور فقط با پایگاه داده امن فعال است.")
        return
    
    # Get user stats
    stats = db.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text("شما هنوز ثبت‌نام نکرده‌اید. از /start استفاده کنید.")
        return
    
    # Get user rank
    rank = db.get_user_rank(user_id)
    
    message = "📊 **آمار من**\n\n"
    message += f"🏆 امتیاز: {stats['imtiaz']}\n"
    message += f"🎖️ درجه: {stats['role']}\n"
    message += f"🏅 رتبه: {rank}\n"
    message += f"📅 تاریخ عضویت: {stats['joined_date'][:10]}\n\n"
    message += "⚠️ هویت شما برای مدیر قابل شناسایی نیست (هش‌شده)."
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info("User viewed own stats (identity protected)")


# ==================== END ADMIN COMMANDS ====================


def main():
    """Start the bot"""
    # Validate environment
    ffmpeg_ok = validate_environment()
    if not ffmpeg_ok:
        logger.warning("⚠️  ffmpeg not found - video metadata stripping will not work")
        logger.warning("⚠️  Set ENABLE_VIDEO_PROCESSING = False in config.py for testing")
        logger.warning("⚠️  Install ffmpeg for production use (see NEXT_STEPS.md)")
    
    # Check bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set BOT_TOKEN in config.py")
        logger.error("📝 See NEXT_STEPS.md for instructions")
        return
    
    # Check webapp URL
    if "yourdomain.com" in WEBAPP_URL:
        logger.warning("⚠️  WEBAPP_URL not configured - email campaigns won't work")
        logger.warning("📝 See NEXT_STEPS.md for hosting instructions")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin commands (secure database only)
    application.add_handler(CommandHandler("stats", admin_stats_command))
    application.add_handler(CommandHandler("export_stats", export_stats_command))
    application.add_handler(CommandHandler("approve_gathering", approve_gathering_command))
    application.add_handler(CommandHandler("reject_gathering", reject_gathering_command))
    
    # User privacy commands
    application.add_handler(CommandHandler("delete_my_data", delete_my_data_command))
    application.add_handler(CommandHandler("my_stats", my_stats_command))
    
    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Bot started successfully! 🦁☀️")
    
    # Python 3.14 compatibility: ensure event loop exists
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
