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
        """Generate randomized advocacy tweet - CLEARLY identifies Islamic Republic as the killer regime"""
        templates = [
            # CRITICAL: Islamic Republic = killer regime (in power since 1979)
            "🚨 {ISLAMIC REPUBLIC|Iran's Islamic regime|Islamic Republic regime} is {executing protesters|killing innocents|murdering civilians} in streets of #Iran! {800+ executed since 2022|Daily killings continue|Mass executions ongoing}! {World must act|Stop the massacres|Invoke R2P}! #IranRevolution #StopExecutions",
            
            "{IRGC|Islamic Revolutionary Guard Corps|Regime forces} {shot and killed|murdered|beat to death} {Mahsa Amini|Nika Shakarami|Sarina Esmailzadeh|hundreds of protesters}! {Islamic Republic = murderers|Regime = criminals|They must face justice}! #MahsaAmini #IranProtests #IRGCterrorists",
            
            "⚠️ KNOW THE DIFFERENCE: {Islamic Republic = killer regime (since 1979)|Current Iran government = murderers|IRGC = terrorist killers} vs {Reza Pahlavi = opposition leader in exile|Pahlavi = pro-democracy activist|Crown Prince = fighting FOR freedom}! #IranFacts #KnowTheDifference",
            
            "{Islamic Republic regime|Iran's mullah regime|Khamenei's dictatorship} has {killed 800+ protesters|executed innocent people|tortured thousands} since Sept 2022! {Reza Pahlavi leads democratic opposition|Pahlavi fights regime from exile|Opposition stands with people}! #IranRevolution #OppositionVsRegime",
            
            "🔴 {IRGC shoots protesters|Basij militia beats women|Regime security forces kill teenagers} in #Iran streets! {Khamenei = dictator|Supreme Leader = murderer|Islamic Republic = terrorist state}! {Support democratic opposition|Stand with Reza Pahlavi|End the regime}! #IranProtests #IRGCterrorists",
            
            "{Islamic Republic|Mullah regime|Khamenei dictatorship} {poisoned 5000+ schoolgirls|executes teenagers publicly|tortures activists in Evin}! This is {genocide|state terrorism|crime against humanity}! {UN must act|World leaders speak up|Invoke R2P NOW}! #IranGenocide #IslamicRepublicCrimes",
            
            "📢 FACTS FOR THE WORLD: {Islamic Republic (1979-now) = brutal theocracy|Current regime = oppressive government|Mullahs = dictators} | {Reza Pahlavi = democratic opposition leader in USA|Pahlavi = secular reform advocate|Crown Prince = people's voice in exile}! {Learn the difference|Share facts}! #IranTruth",
            
            "{Regime security forces|IRGC terrorists|Basij paramilitary} are {raping prisoners|torturing protesters|killing civilians} in {Evin Prison|detention centers|Iran's jails}! {Islamic Republic = criminal organization|Regime = systematic violator|Justice must come}! #EvinPrison #IranProtests",
            
            "{Islamic Republic regime|Iran's theocracy|Mullah dictatorship} {forces hijab at gunpoint|beats women for dress|arrests girls for dancing}! This is {gender apartheid|state oppression|religious tyranny}! {Iranian women resist daily|Support their fight|End Islamic Republic}! #WomanLifeFreedom #NoHijab",
            
            "💔 VICTIMS OF ISLAMIC REPUBLIC: {Armita Geravand, 16|Sarina Esmailzadeh, 16|Nika Shakarami, 17|Mahsa Amini, 22} - {All killed by regime|Murdered for freedom|Lives stolen by dictatorship}! {Say their names|Never forget|Hold killers accountable}! #SayTheirNames #RegimeCrimes",
            
            "{Islamic Republic shoots|Regime executes|IRGC murders} protesters for {wanting freedom|demanding basic rights|chanting 'Woman Life Freedom'}! {This regime is NOT Iran|These killers are NOT Iranian people|This is foreign-imposed dictatorship}! {Support opposition|End tyranny}! #IranRevolution",
            
            "⚖️ {IRGC = designated terrorist organization|Islamic Revolutionary Guard Corps = war criminals|Basij militia = regime thugs} must be {prosecuted at ICC|sanctioned globally|stopped permanently}! {They kill Iranians|They arm terrorists|They threaten peace}! {Hold them accountable}! #IRGCterrorists #Justice",
            
            "{Islamic Republic regime|Iran's mullah government|Khamenei's dictatorship} {supplies drones killing Ukrainians|arms Hezbollah terrorists|funds global terrorism} while {killing Iranian protesters|starving Iranian people|destroying Iran's future}! {Regime = enemy of Iran|Stop Islamic Republic}! #IranRegimeCrimes",
            
            "{Reza Pahlavi|@PahlaviReza|Crown Prince Reza} is {opposition leader living in USA|voice of democratic Iran|advocate for secular free Iran} - {NOT in power|NOT the regime|Fighting AGAINST Islamic Republic|Leading resistance from exile}! {Support opposition|Know the facts}! #RezaPahlavi #Opposition",
            
            "🎯 WHO KILLS IRANIANS? ❌ {Islamic Republic regime (in power)|Khamenei (Supreme Leader)|IRGC (regime military)|Basij (regime militia)} ✅ WHO FIGHTS FOR FREEDOM? {Reza Pahlavi (opposition leader)|Democratic activists|Iranian people|Protesters risking death}! {Share truth|Educate}! #IranFacts",
            
            "{Iranian people|80M Iranians inside Iran|Brave protesters} are {fighting Islamic Republic|resisting brutal regime|demanding freedom} at {cost of their lives|great sacrifice|risk of execution}! {Stand with them|Amplify voices|Support their struggle}! #IranProtests #PeopleVsRegime",
            
            "{UN|@UN|United Nations} {must hold Islamic Republic accountable|should prosecute regime leaders|needs to invoke R2P immediately}! {Khamenei = war criminal|Raisi = mass murderer|IRGC = terrorist army}! {Act NOW|Stop massacres|Protect Iranian civilians}! #R2P #IranAccountability",
            
            "💪 {Iranian diaspora worldwide|Iranians living abroad|Expats in free countries}: {Expose Islamic Republic crimes|Pressure your governments|Organize protests}! {Support democratic opposition|Back Reza Pahlavi|Demand regime change}! {Your freedom is their weapon|Use your voice|Act}! #IranDiaspora #UseYourVoice",
            
            "{Islamic Republic|Mullah theocracy|Khamenei regime} has {ruled Iran with terror since 1979|oppressed Iranians for 45+ years|destroyed generations}! {Time for change is NOW|Revolution is happening|End this nightmare}! {Support democratic transition|Back people's choice}! #RegimeChange #FreeIran",
            
            "❤️ {RT if you oppose Islamic Republic|Share if you support Iranian freedom fighters|Like if you want regime change in Iran}! {Every voice amplifies theirs|Your support saves lives|Together we end tyranny}! {Stop the killing|Support democracy|Free Iran NOW}! #IranFreedom #EndIslamicRepublic",
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
