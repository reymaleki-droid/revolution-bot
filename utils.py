"""
Utility functions for National Revolution 1404 Bot
Includes metadata scrubbing, spintax, and security helpers
"""
import random
import re
import subprocess
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Secret redaction — defence-in-depth for log / error output
# ---------------------------------------------------------------------------

# Telegram bot token: digits:base64url  (but skip all-X placeholders)
_RE_TELEGRAM_TOKEN = re.compile(
    r'[0-9]{7,10}:[A-Za-z0-9_-]{30,50}'
)

# PostgreSQL / Postgres connection URLs (full masking)
_RE_POSTGRES_URL = re.compile(
    r'(?:postgresql|postgres)://[^\s\'"<>]+'
)

# Long hex strings (≥ 32 chars) that look like salts / peppers / keys
_RE_HEX_SECRET = re.compile(
    r'(?<![a-fA-F0-9])[a-f0-9]{32,}(?![a-fA-F0-9])'
)


def redact_secrets(text: str | None) -> str:
    """
    Redact known secret patterns from *text* before it reaches logs or
    user-visible output.

    Handles:
    - Telegram bot tokens  →  ``[REDACTED-TOKEN]``
    - PostgreSQL URLs      →  ``[REDACTED-DB-URL]``
    - 32+ hex strings      →  ``[REDACTED-HEX]``

    Placeholder / documentation values (all-X tokens) are left intact so
    that example docs remain readable.
    """
    if not text:
        return ""

    # 1. Telegram tokens — skip all-X placeholders
    def _mask_token(m: re.Match) -> str:
        value = m.group(0)
        # If the "secret part" (after colon) is all X, it's a placeholder
        after_colon = value.split(":", 1)[-1]
        if set(after_colon) <= {"X", "x"}:
            return value  # keep placeholder
        return "[REDACTED-TOKEN]"

    text = _RE_TELEGRAM_TOKEN.sub(_mask_token, text)

    # 2. PostgreSQL URLs — full replacement
    text = _RE_POSTGRES_URL.sub("[REDACTED-DB-URL]", text)

    # 3. Long hex strings (salts / peppers / keys)
    text = _RE_HEX_SECRET.sub("[REDACTED-HEX]", text)

    return text


class MediaSecurity:
    """Handles secure media processing and metadata removal"""
    
    @staticmethod
    def strip_photo_metadata_pillow(input_path: str, output_path: Optional[str] = None) -> str:
        """
        Strip ALL metadata from photos using Pillow (alternative to ffmpeg)
        Critical for user safety - removes GPS, EXIF, camera info, etc.
        
        Args:
            input_path: Path to original photo
            output_path: Path for cleaned photo (optional)
            
        Returns:
            Path to cleaned file
        """
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_clean{ext}"
        
        try:
            from PIL import Image
            
            # Open image
            img = Image.open(input_path)
            
            # Remove all EXIF data by creating new image
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            
            # Save without metadata
            image_without_exif.save(output_path, quality=95, optimize=True)
            
            logger.info(f"🔒 Successfully stripped photo metadata from {input_path}")
            
            # Remove original file for security
            try:
                os.remove(input_path)
            except:
                pass
            
            return output_path
            
        except ImportError:
            logger.error("⚠️ Pillow not installed - cannot strip photo metadata")
            logger.error("Install with: pip install Pillow")
            raise RuntimeError("Pillow not installed")
        except Exception as e:
            logger.error(f"❌ Photo metadata stripping failed: {e}")
            raise
    
    @staticmethod
    def strip_metadata(input_path: str, output_path: Optional[str] = None) -> str:
        """
        Strip ALL metadata from video/image files using ffmpeg
        Critical for user safety - removes GPS, EXIF, creation time, etc.
        
        Args:
            input_path: Path to original file
            output_path: Path for cleaned file (optional)
            
        Returns:
            Path to cleaned file
        """
        if output_path is None:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_clean{ext}"
        
        # For photos, try Pillow first (more reliable on Windows)
        if input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            try:
                return MediaSecurity.strip_photo_metadata_pillow(input_path, output_path)
            except:
                logger.warning("⚠️ Pillow failed, falling back to ffmpeg for photos")
        
        # For videos or if Pillow failed, use ffmpeg
        try:
            # For videos
            if input_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm')):
                cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-map_metadata', '-1',  # Remove all metadata
                    '-c:v', 'copy',  # Copy video codec (fast)
                    '-c:a', 'copy',  # Copy audio codec (fast)
                    '-fflags', '+bitexact',  # Reproducible output
                    '-flags:v', '+bitexact',
                    '-flags:a', '+bitexact',
                    output_path,
                    '-y'  # Overwrite without asking
                ]
            # For images
            elif input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-map_metadata', '-1',  # Remove all metadata
                    '-c:v', 'copy',
                    output_path,
                    '-y'
                ]
            else:
                raise ValueError(f"Unsupported file type: {input_path}")
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # SEC-010: Reduced from 300s to 60s
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully stripped metadata from {input_path}")
                # Remove original file for security
                try:
                    os.remove(input_path)
                except:
                    pass
                return output_path
            else:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise RuntimeError(f"Failed to strip metadata: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timeout - file too large")
            raise RuntimeError("File processing timeout")
        except FileNotFoundError:
            logger.error("ffmpeg not found - please install ffmpeg")
            raise RuntimeError("ffmpeg not installed")
        except Exception as e:
            logger.error(f"Metadata stripping failed: {e}")
            raise
    
    @staticmethod
    def verify_clean(file_path: str) -> bool:
        """
        Verify that a file has no metadata
        
        Returns:
            True if file is clean, False otherwise
        """
        try:
            cmd = ['ffprobe', '-show_format', '-show_streams', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Check for common metadata tags
            dangerous_tags = ['location', 'gps', 'creation_time', 'make', 'model']
            output_lower = result.stdout.lower()
            
            for tag in dangerous_tags:
                if tag in output_lower:
                    return False
            
            return True
        except:
            return False


class Spintax:
    """Generates randomized text to avoid spam detection"""
    
    @staticmethod
    def spin(text: str) -> str:
        """
        Process spintax and return randomized text
        Format: {option1|option2|option3}
        
        Example:
            "{Stop|Halt|End} the {killings|executions}" 
            -> "Stop the killings" or "Halt the executions" etc.
        """
        pattern = r'\{([^{}]+)\}'
        
        def replace_spin(match):
            options = match.group(1).split('|')
            return random.choice(options)
        
        while re.search(pattern, text):
            text = re.sub(pattern, replace_spin, text, count=1)
        
        return text
    
    @staticmethod
    def generate_tweet() -> str:
        """Generate randomized advocacy tweet - authentic Iranian political voice with mandatory hashtags"""
        templates = [
            # Emotional personal appeal
            "🩸 {مادران ایران خون گریه می‌کنند|خون فرزندان ایران بر زمین است|زمین ایران از خون جوانانش رنگین شد}! {Islamic Republic has turned Iran into a slaughterhouse|The mullahs' regime massacres its own children|46 years of murder is ENOUGH}! {The time of reckoning has come|Enough blood has been spilled|This regime's end is near}! {Freedom for Iran|Democracy for Iran|Azadi} 🦁☀️ @PahlaviReza\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Diaspora call to action
            "📢 To every Iranian in exile: {our silence is complicity|we owe it to those dying inside Iran|our brothers and sisters bleed while we watch}! {Rise up wherever you are|Take to the streets of your cities|Make your host country's government hear Iran's cry}! {Prince Reza Pahlavi|@PahlaviReza|Reza Pahlavi} is the {voice of 85 million Iranians|leader of Iran's democratic movement|beacon of Iran's future}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Expose regime crimes internationally
            "⚠️ {BREAKING|URGENT|WORLD MUST KNOW}: {Islamic Republic executed 12 political prisoners last night|IRGC opened fire on protesters in Zahedan AGAIN|Regime tortured teenagers to death in Evin Prison}! {This is genocide against Iranians|These are crimes against humanity|The world can't look away anymore}! We stand with {Prince Reza Pahlavi|@PahlaviReza} for a {free|democratic|secular} Iran 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Historical / civilization
            "🦁☀️ {Iran had 2500 years of civilization before 1979|The mullahs hijacked our revolution in '79|Islamic Republic was NEVER the choice of Iranians}! {Now the people have spoken|The nation demands democracy|Iran's destiny is freedom}! {Prince Reza Pahlavi|@PahlaviReza} represents {our democratic future|freedom & human rights|our civilizational identity}! {زنده باد ایران آزاد|Iran will be free|پرچم شیر و خورشید}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Women's struggle
            "💔 {Mahsa Amini was murdered for showing her hair|Armita Geravand was killed at 16 for being free|Nika Shakarami was beaten to death for singing freedom}! The Islamic Republic {murders women daily|has declared war on Iranian women|is the enemy of every woman on earth}! {Iranian women lead this revolution and|Women Life Freedom means|زن زندگی آزادی —} {Prince Reza Pahlavi|@PahlaviReza} stands with them! 🌹🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Economic devastation + regime blame
            "📉 Under Islamic Republic: {80% of Iranians live below poverty|Iran's currency lost 99% of its value|regime spent $30B funding Hezbollah while Iranians starve}! {This is not mismanagement—it's THEFT|They rob Iran to fund terror|Mullahs live in palaces while Iran burns}! {Prince Reza Pahlavi|@PahlaviReza} has a plan for {Iran's prosperity|economic recovery|rebuilding our great nation}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # IRGC terrorism exposure
            "🔴 IRGC is a {designated terrorist organization|terror army in uniform|the world's largest state-sponsored militia} that {kills Iranians at home and exports terror abroad|massacred 1500+ protesters in Nov 2019|runs drug cartels, executions & proxy wars}! {Every IRGC commander must face The Hague|Sanction them ALL|Disband this criminal army}! {Prince Reza Pahlavi|@PahlaviReza} will bring justice! ⚖️🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Unity message
            "🤝 {Kurd, Baluch, Azeri, Lor, Arab, Persian — we are ALL Iran|Every ethnicity, every faith — ONE Iran|From Kurdistan to Sistan, ONE nation}! The Islamic Republic {divides us to rule us|fears our unity more than anything|tried to break us but FAILED}! United behind {Prince Reza Pahlavi|@PahlaviReza|our leader}, {Iran will be free|we are unstoppable|democracy will prevail}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # International community shame
            "🌍 Dear @UN @EU_Commission @StateDept: {How many more Iranians must die before you act?|You condemned apartheid but ignore Iran's genocide|Your silence enables the massacres}! {Islamic Republic has killed more of its own people than ISIS|1988 massacre, 2019 massacre, 2022 massacre — HOW MANY MORE?|Every dead protester is blood on your hands too}! Support {Prince Reza Pahlavi|@PahlaviReza} & the Iranian people! 🆘🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Prisoner of conscience
            "⛓️ RIGHT NOW in {Evin Prison|Rajaei Shahr Prison|regime dungeons}: {political prisoners are being tortured|teenagers await execution|journalists rot for writing truth}! {Toomaj Salehi rapped for freedom — sentenced to death|Narges Mohammadi won Nobel Prize — still imprisoned|Thousands jailed for wanting basic rights}! {Prince Reza Pahlavi|@PahlaviReza} {demands their freedom|fights for every prisoner|will bring them justice}! 🕊️🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Revolutionary momentum 2026
            "🔥 {The revolution is not dead — it's GROWING|2026 is the year of Iran's liberation|Every protest, every tweet, every act of defiance brings us closer}! {Islamic Republic is weaker than ever|Regime is crumbling from within|Khamenei's grip is slipping}! {History is on our side|Iran WILL be free|The countdown has begun}! Stand with {Prince Reza Pahlavi|@PahlaviReza}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Legacy of martyrs
            "🕯️ I will NEVER forget: {the 16-year-old girl shot in the chest for protesting|the student blinded by IRGC pellets|the mother executed for mourning her son|the child killed on his way to school}! {Their blood is the seed of Iran's freedom tree|Every martyr brings us closer to liberation|They did not die in vain}! {Prince Reza Pahlavi|@PahlaviReza} carries their legacy! 💐🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Direct challenge to Khamenei
            "🎯 {Khamenei|The so-called Supreme Leader|Ali Khamenei}: {your time is UP|you cannot massacre your way to survival|history will judge you as the worst tyrant Iran has known}! {Your own military is turning against you|The people have chosen democracy|Even your own supporters are abandoning you}! {Prince Reza Pahlavi|@PahlaviReza} is the voice of free Iran and {there's nothing you can do|Iran will be liberated|justice will be served}! ⚖️🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Secular democracy vision
            "🌅 Imagine Iran where: {women walk free without forced hijab|no one is executed for their beliefs|every ethnicity is celebrated, not persecuted|free press, free internet, free people}! {This is not a dream — this is Reza Pahlavi's vision|This is what we're fighting for|This will be reality}! {Prince Reza Pahlavi|@PahlaviReza} = {secular democracy|freedom & prosperity|Iran's bright future}! 🦁☀️✨\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Social media mobilization
            "📱 {Every tweet is a bullet against tyranny|Your RT saves lives inside Iran|This hashtag is the regime's nightmare}! {The mullahs spent $2B on internet censorship — prove them wrong|They block VPNs because they fear YOUR voice|Our digital army is stronger than their propaganda}! {Amplify|Share|Spread the word} for {Prince Reza Pahlavi|@PahlaviReza} and a free Iran! 🔊🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # November 2019 massacre
            "🖤 November 2019: Islamic Republic {massacred 1500+ unarmed protesters in 3 days|shut down the internet and slaughtered its people|committed the bloodiest crackdown since 1988}! {Internet was cut so the world wouldn't see|Bodies were hidden, families threatened|They thought we'd forget — WE NEVER WILL}! {Prince Reza Pahlavi|@PahlaviReza} demands accountability! 🩸🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Environmental destruction
            "🏜️ Islamic Republic has {dried up Lake Urmia|destroyed Iran's forests|polluted every major river|turned Khuzestan into a dust bowl}! {They don't just kill people — they're killing the LAND|Iran's environment is dying under mullah rule|46 years of ecological catastrophe}! {Prince Reza Pahlavi|@PahlaviReza} {will restore Iran's natural heritage|has a green recovery plan|cares about Iran's future}! 🌱🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Persian/bilingual emotional
            "ایران، ای سرزمین مادری! 🦁☀️ {جمهوری اسلامی تو را ویران کرد|آخوندها خاک تو را فروختند|۴۶ سال خون و اشک بس است}! {We will take back our homeland|Iran's liberation is inevitable|The motherland is calling her children}! {Prince Reza Pahlavi|@PahlaviReza|شاهزاده رضا پهلوی} is {our leader for a free Iran|the voice of democracy|leading us to freedom}! {زنده باد ایران آزاد|پرچم شیر و خورشید}! 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Sports / cultural pride
            "⚽ When {Iranian athletes are forced to compete without their flag|our wrestlers must throw matches on regime orders|sports champions are executed for speaking out} — you know the regime fears EVERYTHING Iranian! {Ali Daei stood up|Wrestlers refused to stay silent|Athletes chose Iran over regime}! {Prince Reza Pahlavi|@PahlaviReza} stands with {Iran's brave athletes|every Iranian hero|those who risk all}! 🏆🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",

            # Heartfelt RT request
            "❤️ If you believe {no government should massacre its own people|freedom is a human right not a privilege|Iran deserves democracy}: {please RT this|share for those who can't speak|be the voice of 85 million silenced Iranians}! {Every share puts pressure on the regime|Your one RT could save a life|Together we are louder than their guns}! {Prince Reza Pahlavi|@PahlaviReza} 🦁☀️\n\n#IranMassacre #IranRevolution2026 #KingRezaPahlavi",
        ]
        
        template = random.choice(templates)
        return Spintax.spin(template)
    
    @staticmethod
    def generate_email(campaign_type: str, subject_templates: list, body_template: str) -> tuple:
        """
        Generate randomized email subject and body for a campaign
        
        Args:
            campaign_type: Type of campaign (un_r2p, military_aid, etc.)
            subject_templates: List of subject line templates with spintax
            body_template: Email body template with spintax
            
        Returns:
            Tuple of (subject, body)
        """
        # Choose random subject template and spin it
        subject_template = random.choice(subject_templates)
        subject = Spintax.spin(subject_template)
        
        # Spin the body template
        body = Spintax.spin(body_template)
        
        return subject, body


class ConduitHelper:
    """Helpers for Psiphon Conduit verification"""
    
    @staticmethod
    def get_install_instructions() -> str:
        """Get Persian instructions for Psiphon Conduit"""
        return """🌐 نصب و راه‌اندازی Psiphon Conduit

📥 نصب:
1. به لینک زیر مراجعه کنید:
   https://psiphon.ca/

2. برنامه Psiphon را دانلود و نصب کنید

3. در تنظیمات، گزینه "Share VPN" یا "Conduit" را فعال کنید

📊 تأیید اعتبار:
• برنامه را به مدت حداقل 24 ساعت روشن نگه دارید
• اسکرین‌شات از Traffic Stats خود بگیرید که حجم بالای مصرف را نشان دهد
• اسکرین‌شات را در همین بات ارسال کنید

🏆 پاداش: 50 امتیاز

با این کار، شما به ایرانیان در داخل کشور برای عبور از سانسور کمک می‌کنید! 💪"""
    
    @staticmethod
    def verify_screenshot(file_path: str) -> dict:
        """
        Verify Conduit screenshot using OCR
        
        Args:
            file_path: Path to screenshot file
            
        Returns:
            Dict with verification results:
                - success: bool
                - tier: str or None ('1-10', '11-50', etc.)
                - amount_gb: float or None
                - confidence: int (0-100)
                - should_fallback: bool (show manual buttons)
                - error: str (if failed)
                - ocr_raw_text: str (for logging)
        """
        try:
            from ocr_service import get_ocr_service
            from config import ENABLE_OCR_VERIFICATION, OCR_CONFIDENCE_THRESHOLD, TESSERACT_PATH
            
            if not ENABLE_OCR_VERIFICATION:
                return {
                    'success': False,
                    'tier': None,
                    'amount_gb': None,
                    'confidence': 0,
                    'should_fallback': True,
                    'error': 'OCR disabled in config',
                    'ocr_raw_text': ''
                }
            
            ocr = get_ocr_service(TESSERACT_PATH)
            
            if not ocr.available:
                return {
                    'success': False,
                    'tier': None,
                    'amount_gb': None,
                    'confidence': 0,
                    'should_fallback': True,
                    'error': 'OCR not available - Tesseract not installed',
                    'ocr_raw_text': ''
                }
            
            # Perform OCR verification
            result = ocr.verify_screenshot(file_path, min_confidence=OCR_CONFIDENCE_THRESHOLD)
            
            # Add raw_text if not present
            if 'ocr_raw_text' not in result:
                extract_result = ocr.extract_data_amount(file_path)
                result['ocr_raw_text'] = extract_result.get('raw_text', '')
            
            logger.info(f"Conduit OCR result: success={result['success']}, tier={result.get('tier')}, confidence={result['confidence']}%")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying screenshot: {e}", exc_info=True)
            return {
                'success': False,
                'tier': None,
                'amount_gb': None,
                'confidence': 0,
                'should_fallback': True,
                'error': str(e),
                'ocr_raw_text': ''
            }


class TextFormatter:
    """Format text for Telegram messages"""
    
    # Anonymous hero names for leaderboard (preserves privacy while adding personality)
    HERO_NAMES = [
        "شیر پارس",      # Lion of Persia
        "ستاره آزادی",    # Star of Freedom  
        "رعد انقلاب",     # Thunder of Revolution
        "سپر میهن",      # Shield of Homeland
        "شعله امید",      # Flame of Hope
        "صاعقه آزادی",    # Lightning of Freedom
        "قهرمان گمنام",   # Unknown Hero
        "رزمنده دیجیتال", # Digital Warrior
        "مبارز سایبری",  # Cyber Fighter
        "نگهبان ایران",   # Guardian of Iran
    ]
    
    @staticmethod
    def format_leaderboard(leaderboard: list) -> str:
        """Format leaderboard for display with anonymous hero names"""
        text = "🏆 *تابلوی افتخار رزمندگان*\n"
        text += "انقلاب ملی ۱۴۰۴ 🦁☀️\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        
        for rank, imtiaz, role in leaderboard:
            medal = medals[rank - 1] if rank <= 3 else f"{rank}."
            # Use creative name based on position (cycles through list)
            hero_name = TextFormatter.HERO_NAMES[(rank - 1) % len(TextFormatter.HERO_NAMES)]
            
            text += f"{medal} *{hero_name}*\n"
            text += f"   🏅 {role} | 💎 {imtiaz:,} امتیاز\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "💪 *شما هم می‌توانید اینجا باشید!*"
        
        return text
    
    @staticmethod
    def format_profile(stats: tuple, rank: int) -> str:
        """Format user profile"""
        username, first_name, imtiaz, role, joined_date = stats
        
        name = username or first_name or "ناشناس"
        
        text = f"👤 *پروفایل میهن پرست داوطلب گارد جاویدان*\n\n"
        text += f"نام: {name}\n"
        text += f"درجه: {role}\n"
        text += f"امتیاز: {imtiaz}\n"
        text += f"رتبه: {rank}\n"
        text += f"تاریخ عضویت: {joined_date[:10]}\n"
        
        return text


def get_webapp_url(bot_username: str) -> str:
    """Generate Web App URL for email advocacy"""
    from config import WEBAPP_URL
    if WEBAPP_URL:
        return f"{WEBAPP_URL}?bot={bot_username}"
    return ""  # Return empty if not configured


def validate_environment() -> bool:
    """Check if required tools are installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        logger.info("ffmpeg is installed")
        return True
    except FileNotFoundError:
        logger.error("ffmpeg not found - metadata stripping will fail")
        return False
