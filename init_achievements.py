"""
Initialize achievements in the database
Run this once after updating to the new gamification system
"""
import sqlite3
from pathlib import Path

def init_achievements(db_path="revolution_bot.db"):
    """Insert predefined achievements"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    achievements = [
        # (achievement_id, name, description, category, points_reward, badge, requirement_type, requirement_value, is_secret)
        
        # Milestone Achievements
        ('first_step', 'اولین قدم', 'شروع سفر شما برای آزادی', 'milestone', 10, '🏅', 'points', 10, 0),
        ('fifty_club', 'باشگاه پنجاه', '50 امتیاز کسب کردید', 'milestone', 25, '⭐', 'points', 50, 0),
        ('century', 'صد تایی', '100 امتیاز کسب کردید', 'milestone', 50, '💫', 'points', 100, 0),
        ('quarter_k', 'ربع هزار', '250 امتیاز کسب کردید', 'milestone', 75, '🌟', 'points', 250, 0),
        ('half_k', 'پانصد', '500 امتیاز کسب کردید', 'milestone', 100, '✨', 'points', 500, 0),
        ('one_k', 'هزارتایی', '1000 امتیاز کسب کردید', 'milestone', 200, '🏆', 'points', 1000, 0),
        ('fifteen_hundred', 'پانزده صد', '1500 امتیاز کسب کردید', 'milestone', 300, '👑', 'points', 1500, 0),
        
        # Specialist Achievements
        ('twitter_starter', 'توییتر آغازگر', '10 توییت به اشتراک گذاشتید', 'specialist', 30, '🐦', 'action_count', 10, 0),
        ('twitter_warrior', 'توییتر جنگجو', '50 توییت به اشتراک گذاشتید', 'specialist', 100, '🦅', 'action_count', 50, 0),
        ('twitter_master', 'توییتر استاد', '100 توییت به اشتراک گذاشتید', 'specialist', 200, '🕊️', 'action_count', 100, 0),
        
        ('email_starter', 'ایمیل آغازگر', '10 ایمیل ارسال کردید', 'specialist', 30, '📧', 'action_count', 10, 0),
        ('email_warrior', 'ایمیل جنگجو', '50 ایمیل ارسال کردید', 'specialist', 100, '📨', 'action_count', 50, 0),
        ('email_master', 'ایمیل استاد', '100 ایمیل ارسال کردید', 'specialist', 200, '✉️', 'action_count', 100, 0),
        
        ('conduit_bronze', 'برنز Conduit', '10GB داده به اشتراک گذاشتید', 'specialist', 50, '🥉', 'conduit_total', 10, 0),
        ('conduit_silver', 'نقره Conduit', '100GB داده به اشتراک گذاشتید', 'specialist', 150, '🥈', 'conduit_total', 100, 0),
        ('conduit_gold', 'طلای Conduit', '500GB داده به اشتراک گذاشتید', 'specialist', 300, '🥇', 'conduit_total', 500, 0),
        ('conduit_legend', 'افسانه Conduit', '1TB داده به اشتراک گذاشتید', 'specialist', 600, '💎', 'conduit_total', 1000, 0),
        
        # Activity Achievements
        ('active_week', 'هفته فعال', '7 روز متوالی فعال بودید', 'activity', 80, '🔥', 'streak', 7, 0),
        ('active_two_weeks', 'دو هفته فعال', '14 روز متوالی فعال بودید', 'activity', 150, '🔥🔥', 'streak', 14, 0),
        ('active_month', 'ماه فعال', '30 روز متوالی فعال بودید', 'activity', 300, '🔥🔥🔥', 'streak', 30, 0),
        ('active_hundred', 'صد روز افسانه', '100 روز متوالی فعال بودید', 'activity', 1000, '💎🔥', 'streak', 100, 0),
        
        # Combo Achievements
        ('combo_master', 'استاد کمبو', '5 فعالیت متنوع در یک روز', 'combo', 100, '⚡', 'daily_combo', 5, 0),
        ('combo_legend', 'افسانه کمبو', '7 فعالیت متنوع در یک روز', 'combo', 200, '🌟', 'daily_combo', 7, 0),
        
        # Social Achievements
        ('organizer', 'سازمان‌دهنده', '1 رویداد اعتراضی ایجاد کردید', 'social', 50, '🎯', 'action_count', 1, 0),
        ('cleanup_hero', 'قهرمان پاکسازی', '5 پاکسازی انجام دادید', 'social', 150, '🧹', 'action_count', 5, 0),
        
        # Secret Achievements
        ('lion_of_iran', 'شیر ایران', 'دستاورد مخفی - ماموریت ویژه', 'secret', 500, '🦁', 'special', 0, 1),
        ('sun_warrior', 'جنگجوی خورشید', 'دستاورد مخفی - پیروزی نهایی', 'secret', 1000, '☀️', 'special', 0, 1),
    ]
    
    inserted = 0
    for ach in achievements:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements 
                (achievement_id, name, description, category, points_reward, badge, requirement_type, requirement_value, is_secret)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ach)
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting {ach[0]}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Initialized {inserted} achievements in {db_path}")

if __name__ == "__main__":
    # Initialize for both databases
    init_achievements("revolution_bot.db")
    
    # For secure database, we need to use the SecureDatabase class
    # but achievements table structure is the same
    if Path("revolution_bot_secure.db").exists():
        init_achievements("revolution_bot_secure.db")
    
    print("🎉 Achievement system initialized successfully!")
