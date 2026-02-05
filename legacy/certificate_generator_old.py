"""
Certificate and Badge Generator for Revolution Bot
Creates NFT-like certificates with QR codes and blockchain-like verification
"""

import hashlib
import secrets
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CertificateGenerator:
    """Generate verifiable digital certificates and shareable rank cards"""
    
    def __init__(self):
        self.cert_dir = Path("certificates")
        self.badge_dir = Path("badges")
        self.cert_dir.mkdir(exist_ok=True)
        self.badge_dir.mkdir(exist_ok=True)
        
        # Try to load Persian font, fallback to default
        try:
            self.font_large = ImageFont.truetype("arial.ttf", 60)
            self.font_medium = ImageFont.truetype("arial.ttf", 40)
            self.font_small = ImageFont.truetype("arial.ttf", 30)
            self.font_tiny = ImageFont.truetype("arial.ttf", 20)
        except:
            logger.warning("Could not load custom fonts, using default")
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()
    
    def generate_certificate_id(self, user_hash: str, rank: str, timestamp: str) -> str:
        """Generate unique certificate ID"""
        data = f"{user_hash}:{rank}:{timestamp}".encode()
        return f"CERT-{hashlib.sha256(data).hexdigest()[:12].upper()}"
    
    def generate_verification_hash(self, certificate_id: str, rank: str, imtiaz: int) -> str:
        """Generate blockchain-like verification hash"""
        data = f"{certificate_id}:{rank}:{imtiaz}:{datetime.now().isoformat()}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def create_qr_code(self, data: str, size: int = 300) -> Image.Image:
        """Create QR code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img.resize((size, size))
    
    def create_certificate(
        self,
        certificate_id: str,
        rank: str,
        imtiaz: int,
        issued_date: str,
        verification_hash: str
    ) -> str:
        """
        Create beautiful certificate image with QR code
        Returns path to generated certificate
        """
        # Create certificate image (1920x1080 for HD quality)
        width, height = 1920, 1080
        img = Image.new('RGB', (width, height), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Add gradient background effect
        for i in range(height):
            r = int(26 + (16 * i / height))
            g = int(26 + (42 * i / height))
            b = int(46 + (74 * i / height))
            draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
        
        # Add decorative border
        border_color = '#FFD700'  # Gold
        border_width = 20
        draw.rectangle(
            [(border_width, border_width), (width-border_width, height-border_width)],
            outline=border_color,
            width=border_width
        )
        
        # Add inner border
        inner_border = border_width + 10
        draw.rectangle(
            [(inner_border, inner_border), (width-inner_border, height-inner_border)],
            outline=border_color,
            width=3
        )
        
        # Title
        title_text = "گواهینامه انقلابی"
        title_bbox = draw.textbbox((0, 0), title_text, font=self.font_large)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((width - title_width) // 2, 100),
            title_text,
            fill='#FFD700',
            font=self.font_large
        )
        
        # Subtitle
        subtitle = "Revolutionary Certificate of Achievement"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.font_small)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(
            ((width - subtitle_width) // 2, 180),
            subtitle,
            fill='#FFFFFF',
            font=self.font_small
        )
        
        # Rank
        rank_text = f"رتبه: {rank} 🦁"
        rank_bbox = draw.textbbox((0, 0), rank_text, font=self.font_large)
        rank_width = rank_bbox[2] - rank_bbox[0]
        draw.text(
            ((width - rank_width) // 2, 300),
            rank_text,
            fill='#00ff41',
            font=self.font_large
        )
        
        # Points
        points_text = f"امتیاز: {imtiaz:,}"
        points_bbox = draw.textbbox((0, 0), points_text, font=self.font_medium)
        points_width = points_bbox[2] - points_bbox[0]
        draw.text(
            ((width - points_width) // 2, 400),
            points_text,
            fill='#FFFFFF',
            font=self.font_medium
        )
        
        # Certificate ID
        cert_id_text = f"Certificate ID: {certificate_id}"
        cert_id_bbox = draw.textbbox((0, 0), cert_id_text, font=self.font_small)
        cert_id_width = cert_id_bbox[2] - cert_id_bbox[0]
        draw.text(
            ((width - cert_id_width) // 2, 500),
            cert_id_text,
            fill='#888888',
            font=self.font_small
        )
        
        # Issued date
        date_text = f"تاریخ صدور: {issued_date}"
        date_bbox = draw.textbbox((0, 0), date_text, font=self.font_small)
        date_width = date_bbox[2] - date_bbox[0]
        draw.text(
            ((width - date_width) // 2, 560),
            date_text,
            fill='#CCCCCC',
            font=self.font_small
        )
        
        # Verification text
        verify_text = "Verified by 500+ Activists"
        verify_bbox = draw.textbbox((0, 0), verify_text, font=self.font_medium)
        verify_width = verify_bbox[2] - verify_bbox[0]
        draw.text(
            ((width - verify_width) // 2, 640),
            verify_text,
            fill='#00ff41',
            font=self.font_medium
        )
        
        # Add QR code
        qr_data = f"VERIFY:{certificate_id}:{verification_hash}"
        qr_img = self.create_qr_code(qr_data, size=250)
        qr_position = ((width - 250) // 2, 760)
        img.paste(qr_img, qr_position)
        
        # Verification hash (partial)
        hash_text = f"Hash: {verification_hash[:16]}..."
        hash_bbox = draw.textbbox((0, 0), hash_text, font=self.font_tiny)
        hash_width = hash_bbox[2] - hash_bbox[0]
        draw.text(
            ((width - hash_width) // 2, 1020),
            hash_text,
            fill='#666666',
            font=self.font_tiny
        )
        
        # Save certificate
        filename = f"{certificate_id}.png"
        filepath = self.cert_dir / filename
        img.save(filepath, quality=95)
        
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
        Create Instagram/Twitter-ready shareable rank card
        Returns path to generated card
        """
        # Create card (1080x1080 for Instagram)
        size = 1080
        img = Image.new('RGB', (size, size), color='#0f0f1e')
        draw = ImageDraw.Draw(img)
        
        # Gradient background
        for i in range(size):
            r = int(15 + (10 * i / size))
            g = int(15 + (27 * i / size))
            b = int(30 + (47 * i / size))
            draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b))
        
        # Add glow effect border
        glow_color = '#FFD700'
        for i in range(10):
            alpha = int(255 * (10 - i) / 10)
            draw.rectangle(
                [(i*2, i*2), (size-i*2, size-i*2)],
                outline=glow_color,
                width=2
            )
        
        # Logo/Title area
        title = "🦁 انقلاب ایران ☀️"
        title_bbox = draw.textbbox((0, 0), title, font=self.font_large)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((size - title_width) // 2, 80),
            title,
            fill='#FFD700',
            font=self.font_large
        )
        
        # Main rank
        rank_text = rank
        rank_bbox = draw.textbbox((0, 0), rank_text, font=self.font_large)
        rank_width = rank_bbox[2] - rank_bbox[0]
        draw.text(
            ((size - rank_width) // 2, 250),
            rank_text,
            fill='#00ff41',
            font=self.font_large
        )
        
        # Points with icon
        points_text = f"⭐ {imtiaz:,} امتیاز"
        points_bbox = draw.textbbox((0, 0), points_text, font=self.font_medium)
        points_width = points_bbox[2] - points_bbox[0]
        draw.text(
            ((size - points_width) // 2, 380),
            points_text,
            fill='#FFFFFF',
            font=self.font_medium
        )
        
        # Stats grid
        y_pos = 520
        stats = [
            (f"🏆 رتبه #{rank_position}", '#FFD700'),
            (f"🎖️ {achievements_count} دستاورد", '#00ff41'),
            (f"🔥 {streak_days} روز فعالیت", '#FF6B6B'),
        ]
        
        for stat_text, color in stats:
            stat_bbox = draw.textbbox((0, 0), stat_text, font=self.font_medium)
            stat_width = stat_bbox[2] - stat_bbox[0]
            draw.text(
                ((size - stat_width) // 2, y_pos),
                stat_text,
                fill=color,
                font=self.font_medium
            )
            y_pos += 80
        
        # Bottom text
        bottom_text = "✊ مبارز واقعی انقلاب"
        bottom_bbox = draw.textbbox((0, 0), bottom_text, font=self.font_medium)
        bottom_width = bottom_bbox[2] - bottom_bbox[0]
        draw.text(
            ((size - bottom_width) // 2, 850),
            bottom_text,
            fill='#FFFFFF',
            font=self.font_medium
        )
        
        # Hashtags
        hashtag_text = "#انقلاب_ایران #رضاشاه"
        hashtag_bbox = draw.textbbox((0, 0), hashtag_text, font=self.font_small)
        hashtag_width = hashtag_bbox[2] - hashtag_bbox[0]
        draw.text(
            ((size - hashtag_width) // 2, 950),
            hashtag_text,
            fill='#888888',
            font=self.font_small
        )
        
        # Save card
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rank_card_{timestamp}.png"
        filepath = self.badge_dir / filename
        img.save(filepath, quality=95)
        
        logger.info(f"Rank card generated: {filename}")
        return str(filepath)
    
    def create_impact_badge(
        self,
        impact_type: str,
        value: int,
        description: str
    ) -> str:
        """
        Create impact achievement badge (square format)
        Returns path to generated badge
        """
        # Create badge (800x800)
        size = 800
        img = Image.new('RGB', (size, size), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # Circular gradient background
        center = size // 2
        for r in range(center, 0, -5):
            intensity = int(255 * r / center)
            color = (
                min(255, 26 + intensity // 3),
                min(255, 26 + intensity // 2),
                min(255, 46 + intensity)
            )
            draw.ellipse(
                [(center-r, center-r), (center+r, center+r)],
                fill=color
            )
        
        # Impact type icons
        icons = {
            'tweet_reach': '📢',
            'prisoners_freed': '🆓',
            'media_mentions': '📰',
            'international_citations': '🌍'
        }
        
        icon = icons.get(impact_type, '⭐')
        icon_text = f"{icon}"
        icon_bbox = draw.textbbox((0, 0), icon_text, font=self.font_large)
        icon_width = icon_bbox[2] - icon_bbox[0]
        draw.text(
            ((size - icon_width) // 2, 150),
            icon_text,
            font=self.font_large
        )
        
        # Value
        value_text = f"{value:,}"
        value_bbox = draw.textbbox((0, 0), value_text, font=self.font_large)
        value_width = value_bbox[2] - value_bbox[0]
        draw.text(
            ((size - value_width) // 2, 300),
            value_text,
            fill='#00ff41',
            font=self.font_large
        )
        
        # Description
        desc_lines = description.split('\n')
        y_pos = 450
        for line in desc_lines:
            line_bbox = draw.textbbox((0, 0), line, font=self.font_small)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(
                ((size - line_width) // 2, y_pos),
                line,
                fill='#FFFFFF',
                font=self.font_small
            )
            y_pos += 50
        
        # Save badge
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"impact_{impact_type}_{timestamp}.png"
        filepath = self.badge_dir / filename
        img.save(filepath, quality=95)
        
        logger.info(f"Impact badge generated: {filename}")
        return str(filepath)


# Singleton instance
_generator = None

def get_certificate_generator() -> CertificateGenerator:
    """Get singleton certificate generator instance"""
    global _generator
    if _generator is None:
        _generator = CertificateGenerator()
    return _generator
