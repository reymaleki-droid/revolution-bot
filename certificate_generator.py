"""
Professional Certificate Generator
World-class document generation with proper RTL/LTR handling
"""

import hashlib
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
import logging

# RTL text shaping
try:
    from bidi.algorithm import get_display
    import arabic_reshaper
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    logging.warning("python-bidi/arabic-reshaper not installed - Persian text may render incorrectly")

logger = logging.getLogger(__name__)


# =============================================================================
# DESIGN SYSTEM CONSTANTS
# =============================================================================

class DesignSystem:
    """Typography and color standards"""
    
    # Colors - Professional, muted palette
    COLORS = {
        'background': '#FAFAFA',       # Off-white, not harsh
        'text_primary': '#1A1A1A',     # Near black
        'text_secondary': '#4A4A4A',   # Dark gray
        'text_tertiary': '#888888',    # Medium gray
        'accent_gold': '#B8860B',      # Dark goldenrod (not bright)
        'accent_navy': '#1B365D',      # Deep navy
        'border': '#E0E0E0',           # Light border
        'qr_dark': '#2D2D2D',          # QR foreground
    }
    
    # Spacing system (base unit: 8px)
    SPACING = {
        'xs': 8,
        'sm': 16,
        'md': 24,
        'lg': 32,
        'xl': 48,
        'xxl': 64,
    }
    
    # Document sizes (300 DPI)
    SIZES = {
        'certificate': (2480, 3508),   # A4 portrait at 300 DPI
        'social_card': (1080, 1350),   # 4:5 ratio for social
        'badge': (800, 800),           # Square badge
    }


class FontManager:
    """Manage font loading with proper fallbacks"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.fonts = {}
        self._load_fonts()
    
    def _load_fonts(self):
        """Load all required fonts"""
        # Persian fonts (Vazirmatn)
        vazir_path = self.base_path / "vazirmatn" / "fonts" / "ttf"
        
        font_map = {
            'persian_bold': (vazir_path / "Vazirmatn-Bold.ttf", 48),
            'persian_medium': (vazir_path / "Vazirmatn-Medium.ttf", 36),
            'persian_regular': (vazir_path / "Vazirmatn-Regular.ttf", 24),
            'persian_light': (vazir_path / "Vazirmatn-Light.ttf", 18),
        }
        
        for name, (path, default_size) in font_map.items():
            try:
                if path.exists():
                    self.fonts[name] = {
                        'path': str(path),
                        'default_size': default_size
                    }
                    logger.debug(f"Loaded font: {name}")
                else:
                    logger.warning(f"Font not found: {path}")
            except Exception as e:
                logger.error(f"Error loading font {name}: {e}")
    
    def get_font(self, name: str, size: int = None) -> ImageFont.FreeTypeFont:
        """Get font by name at specified size"""
        if name in self.fonts:
            font_info = self.fonts[name]
            actual_size = size or font_info['default_size']
            try:
                return ImageFont.truetype(font_info['path'], actual_size)
            except Exception as e:
                logger.error(f"Error loading font {name} at size {actual_size}: {e}")
        
        # Fallback to default
        logger.warning(f"Using default font for {name}")
        return ImageFont.load_default()


def shape_persian(text: str) -> str:
    """Properly shape Persian/Arabic text for rendering"""
    if not HAS_BIDI:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception as e:
        logger.error(f"Error shaping Persian text: {e}")
        return text


def to_persian_numerals(text: str) -> str:
    """Convert Western numerals to Persian numerals"""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    result = ''
    for char in str(text):
        if char.isdigit():
            result += persian_digits[int(char)]
        else:
            result += char
    return result


# =============================================================================
# CERTIFICATE GENERATOR
# =============================================================================

class CertificateGenerator:
    """Generate professional, verifiable digital certificates"""
    
    def __init__(self):
        self.cert_dir = Path("certificates")
        self.badge_dir = Path("badges")
        self.assets_dir = Path("assets")
        self.fonts_dir = self.assets_dir / "fonts"
        
        # Create directories
        self.cert_dir.mkdir(exist_ok=True)
        self.badge_dir.mkdir(exist_ok=True)
        
        # Initialize font manager
        self.font_manager = FontManager(self.fonts_dir)
        
        # Design system
        self.colors = DesignSystem.COLORS
        self.spacing = DesignSystem.SPACING
    
    def generate_certificate_id(self, user_hash: str, rank: str, timestamp: str) -> str:
        """Generate unique certificate ID"""
        data = f"{user_hash}:{rank}:{timestamp}".encode()
        return f"CERT-{hashlib.sha256(data).hexdigest()[:12].upper()}"
    
    def generate_verification_hash(self, certificate_id: str, rank: str, imtiaz: int) -> str:
        """Generate verification hash"""
        data = f"{certificate_id}:{rank}:{imtiaz}:{datetime.now().isoformat()}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def _create_qr_code(self, data: str, size: int = 200) -> Image.Image:
        """Create clean QR code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,  # Minimal border
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(
            fill_color=self.colors['qr_dark'],
            back_color=self.colors['background']
        )
        return img.resize((size, size), Image.Resampling.LANCZOS)
    
    def _draw_text_centered(
        self,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str,
        width: int
    ) -> int:
        """Draw centered text and return the text height"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        draw.text((x, y), text, fill=color, font=font)
        return text_height
    
    def _draw_text_right(
        self,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        color: str,
        width: int,
        margin: int = 0
    ) -> int:
        """Draw right-aligned text (for RTL)"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = width - text_width - margin
        draw.text((x, y), text, fill=color, font=font)
        return text_height
    
    def create_certificate(
        self,
        certificate_id: str,
        rank: str,
        imtiaz: int,
        issued_date: str,
        verification_hash: str
    ) -> str:
        """
        Create professional certificate image
        Returns path to generated certificate
        """
        # Document dimensions (A4 at 300 DPI)
        width, height = 2480, 3508
        margin = int(width * 0.10)  # 10% margins
        content_width = width - (2 * margin)
        
        # Create image with off-white background
        img = Image.new('RGB', (width, height), color=self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Draw subtle border
        border_rect = [margin // 2, margin // 2, width - margin // 2, height - margin // 2]
        draw.rectangle(border_rect, outline=self.colors['border'], width=4)
        
        # Inner border with accent
        inner_margin = margin // 2 + 20
        inner_rect = [inner_margin, inner_margin, width - inner_margin, height - inner_margin]
        draw.rectangle(inner_rect, outline=self.colors['accent_gold'], width=2)
        
        # Load fonts
        font_title = self.font_manager.get_font('persian_bold', 96)
        font_subtitle = self.font_manager.get_font('persian_medium', 48)
        font_body = self.font_manager.get_font('persian_regular', 42)
        font_rank = self.font_manager.get_font('persian_bold', 72)
        font_meta = self.font_manager.get_font('persian_light', 32)
        
        # Current Y position
        y_pos = margin + self.spacing['xxl']
        
        # === HEADER ZONE ===
        
        # Main title (Persian)
        title_persian = shape_persian("گواهینامه")
        self._draw_text_centered(draw, title_persian, y_pos, font_title, self.colors['accent_navy'], width)
        y_pos += 120
        
        # Subtitle
        subtitle = "CERTIFICATE OF ACHIEVEMENT"
        self._draw_text_centered(draw, subtitle, y_pos, font_subtitle, self.colors['text_secondary'], width)
        y_pos += self.spacing['xxl'] * 2
        
        # Decorative line
        line_y = y_pos
        line_margin = margin + 200
        draw.line([(line_margin, line_y), (width - line_margin, line_y)], 
                  fill=self.colors['accent_gold'], width=2)
        y_pos += self.spacing['xl']
        
        # === CONTENT ZONE ===
        
        # Certification text (Persian)
        cert_text = shape_persian("بدینوسیله گواهی می‌شود که")
        self._draw_text_centered(draw, cert_text, y_pos, font_body, self.colors['text_secondary'], width)
        y_pos += 80
        
        # English equivalent
        cert_eng = "This is to certify that the bearer"
        self._draw_text_centered(draw, cert_eng, y_pos, font_meta, self.colors['text_tertiary'], width)
        y_pos += self.spacing['xl'] * 2
        
        # Achievement text
        achieve_text = shape_persian("به درجه زیر نائل شده است")
        self._draw_text_centered(draw, achieve_text, y_pos, font_body, self.colors['text_secondary'], width)
        y_pos += 80
        
        achieve_eng = "has achieved the rank of"
        self._draw_text_centered(draw, achieve_eng, y_pos, font_meta, self.colors['text_tertiary'], width)
        y_pos += self.spacing['xxl']
        
        # === RANK DISPLAY (Main focus) ===
        
        # Clean rank name (remove emoji if present)
        clean_rank = rank
        for emoji in ['🎖️', '🥉', '🥈', '🥇', '💎', '👑', '⭐']:
            clean_rank = clean_rank.replace(emoji, '').strip()
        
        rank_display = shape_persian(clean_rank)
        self._draw_text_centered(draw, rank_display, y_pos, font_rank, self.colors['accent_navy'], width)
        y_pos += 100
        
        # Points
        points_persian = to_persian_numerals(f"{imtiaz:,}")
        points_text = shape_persian(f"با کسب {points_persian} امتیاز")
        self._draw_text_centered(draw, points_text, y_pos, font_body, self.colors['text_secondary'], width)
        y_pos += 60
        
        points_eng = f"with {imtiaz:,} points earned"
        self._draw_text_centered(draw, points_eng, y_pos, font_meta, self.colors['text_tertiary'], width)
        y_pos += self.spacing['xxl'] * 2
        
        # Another decorative line
        draw.line([(line_margin, y_pos), (width - line_margin, y_pos)], 
                  fill=self.colors['accent_gold'], width=2)
        y_pos += self.spacing['xl']
        
        # === AUTHORITY ZONE ===
        
        # Issuer
        issuer_text = shape_persian("صادر شده توسط")
        self._draw_text_centered(draw, issuer_text, y_pos, font_meta, self.colors['text_tertiary'], width)
        y_pos += 50
        
        authority = shape_persian("جنبش انقلاب ملی ایران")
        self._draw_text_centered(draw, authority, y_pos, font_subtitle, self.colors['accent_navy'], width)
        y_pos += 80
        
        # Date
        date_label = shape_persian("تاریخ صدور")
        self._draw_text_centered(draw, date_label, y_pos, font_meta, self.colors['text_tertiary'], width)
        y_pos += 50
        
        # Format date nicely
        try:
            date_obj = datetime.fromisoformat(issued_date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except:
            formatted_date = issued_date[:10] if len(issued_date) >= 10 else issued_date
        
        self._draw_text_centered(draw, formatted_date, y_pos, font_body, self.colors['text_primary'], width)
        y_pos += self.spacing['xxl']
        
        # === FOOTER ZONE ===
        
        # QR Code
        qr_size = 280
        qr_data = f"VERIFY:{certificate_id}:{verification_hash[:16]}"
        qr_img = self._create_qr_code(qr_data, qr_size)
        qr_x = (width - qr_size) // 2
        qr_y = height - margin - qr_size - 200
        img.paste(qr_img, (qr_x, qr_y))
        
        # Certificate ID below QR
        id_y = qr_y + qr_size + 30
        id_text = f"Certificate ID: {certificate_id}"
        self._draw_text_centered(draw, id_text, id_y, font_meta, self.colors['text_tertiary'], width)
        
        # Verification hash (truncated)
        hash_y = id_y + 50
        hash_text = f"Verification: {verification_hash[:24]}..."
        self._draw_text_centered(draw, hash_text, hash_y, font_meta, self.colors['text_tertiary'], width)
        
        # Save certificate
        filename = f"{certificate_id}.png"
        filepath = self.cert_dir / filename
        img.save(filepath, quality=95, dpi=(300, 300))
        
        logger.info(f"Certificate generated: {filename}")
        return str(filepath)
    
    def create_rank_card(
        self,
        rank: str,
        imtiaz: int,
        achievements_count: int,
        streak_days: int,
        rank_position: int
    ) -> str:
        """
        Create shareable social media card (4:5 ratio)
        Returns path to generated card
        """
        # Social card dimensions
        width, height = 1080, 1350
        margin = 80
        
        # Create image
        img = Image.new('RGB', (width, height), color=self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Subtle accent bar at top
        draw.rectangle([(0, 0), (width, 8)], fill=self.colors['accent_gold'])
        
        # Load fonts
        font_title = self.font_manager.get_font('persian_bold', 64)
        font_rank = self.font_manager.get_font('persian_bold', 56)
        font_body = self.font_manager.get_font('persian_regular', 36)
        font_stat = self.font_manager.get_font('persian_medium', 32)
        font_small = self.font_manager.get_font('persian_light', 24)
        
        y_pos = margin + 40
        
        # Header
        header = shape_persian("کارت رتبه")
        self._draw_text_centered(draw, header, y_pos, font_title, self.colors['accent_navy'], width)
        y_pos += 100
        
        # Subtitle
        subtitle = "RANK CARD"
        self._draw_text_centered(draw, subtitle, y_pos, font_small, self.colors['text_tertiary'], width)
        y_pos += 80
        
        # Decorative line
        draw.line([(margin, y_pos), (width - margin, y_pos)], 
                  fill=self.colors['border'], width=2)
        y_pos += 60
        
        # Clean rank name
        clean_rank = rank
        for emoji in ['🎖️', '🥉', '🥈', '🥇', '💎', '👑', '⭐']:
            clean_rank = clean_rank.replace(emoji, '').strip()
        
        # Main rank display
        rank_text = shape_persian(clean_rank)
        self._draw_text_centered(draw, rank_text, y_pos, font_rank, self.colors['accent_navy'], width)
        y_pos += 100
        
        # Points
        points_persian = to_persian_numerals(f"{imtiaz:,}")
        points_text = shape_persian(f"{points_persian} امتیاز")
        self._draw_text_centered(draw, points_text, y_pos, font_body, self.colors['text_primary'], width)
        y_pos += 100
        
        # Stats box
        stats_box_y = y_pos
        stats_box_height = 280
        stats_margin = margin + 40
        draw.rectangle(
            [(stats_margin, stats_box_y), (width - stats_margin, stats_box_y + stats_box_height)],
            outline=self.colors['border'],
            width=2
        )
        
        # Stats inside box
        stat_y = stats_box_y + 40
        stat_spacing = 70
        
        stats = [
            (shape_persian(f"رتبه در جدول: {to_persian_numerals(str(rank_position))}"), self.colors['text_primary']),
            (shape_persian(f"تعداد دستاوردها: {to_persian_numerals(str(achievements_count))}"), self.colors['text_primary']),
            (shape_persian(f"روزهای فعالیت متوالی: {to_persian_numerals(str(streak_days))}"), self.colors['text_primary']),
        ]
        
        for stat_text, color in stats:
            self._draw_text_centered(draw, stat_text, stat_y, font_stat, color, width)
            stat_y += stat_spacing
        
        y_pos = stats_box_y + stats_box_height + 60
        
        # Bottom decorative line
        draw.line([(margin, y_pos), (width - margin, y_pos)], 
                  fill=self.colors['border'], width=2)
        y_pos += 60
        
        # Footer text
        footer = shape_persian("جنبش انقلاب ملی ایران")
        self._draw_text_centered(draw, footer, y_pos, font_body, self.colors['accent_navy'], width)
        y_pos += 60
        
        # Accent bar at bottom
        draw.rectangle([(0, height - 8), (width, height)], fill=self.colors['accent_gold'])
        
        # Save card
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rank_card_{timestamp}.png"
        filepath = self.badge_dir / filename
        img.save(filepath, quality=95)
        
        logger.info(f"Rank card generated: {filename}")
        return str(filepath)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_generator = None

def get_certificate_generator() -> CertificateGenerator:
    """Get singleton certificate generator instance"""
    global _generator
    if _generator is None:
        _generator = CertificateGenerator()
    return _generator
