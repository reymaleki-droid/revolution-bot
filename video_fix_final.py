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

━━━━━━━━━━━━━━━━━━━━

<b>📱 چطور؟</b>

1️⃣ سلفی 30-120 ثانیه
2️⃣ زبان: 🇺🇸 English 🇩🇪 Deutsch 🇫🇷 Français
3️⃣ مثال: "Hi, I'm [Name]. I stand with Iran. #FreeIran"
4️⃣ پلتفرم: Instagram Reels | TikTok | YouTube"""

    await update.message.reply_text(msg1, parse_mode='HTML', disable_web_page_preview=True)
    
    msg2 = """💰 <b>پاداش</b>

🥉 1 پلتفرم: 150
🥈 2 پلتفرم: 250
🥇 3 پلتفرم: 350
💎 4+ پلتفرم: 550
👑 100K: +1000
⭐ 1M: +5000

🏆 بونوس: استوری +25 | کامنت +15

━━━━━━━━━━━━━━━━━━━━

🦁☀️ <b>"امروز اقدام کنید!"</b>"""

    keyboard = [[InlineKeyboardButton("✅ ویدیو را منتشر کردم (+150 امتیاز)", callback_data="video_testimonial_completed")], [InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
    await update.message.reply_text(msg2, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
