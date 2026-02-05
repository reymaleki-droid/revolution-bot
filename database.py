"""
Database module for National Revolution 1404 Bot
Handles user tracking, gamification, and leaderboard
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Dict

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite database operations for the bot"""
    
    def __init__(self, db_path: str = "revolution_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table with gamification
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                imtiaz INTEGER DEFAULT 0,
                role TEXT DEFAULT 'Sarbaz',
                joined_date TEXT,
                last_active TEXT
            )
        """)
        
        # Actions log for tracking contributions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                points INTEGER,
                timestamp TEXT,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Conduit verifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conduit_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                screenshot_file_id TEXT,
                data_shared TEXT,
                points_earned INTEGER DEFAULT 0,
                ocr_extracted_amount REAL,
                ocr_confidence INTEGER,
                verification_method TEXT,
                ocr_raw_text TEXT,
                verified BOOLEAN DEFAULT 0,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Protest events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protest_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT NOT NULL,
                city TEXT NOT NULL,
                location TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                organizer_contact TEXT,
                attendee_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT,
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        """)
        
        # Protest attendance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protest_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                confirmed_at TEXT,
                FOREIGN KEY (event_id) REFERENCES protest_events (event_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(event_id, user_id)
            )
        """)
        
        # Cleanup actions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleanup_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                protest_location TEXT NOT NULL,
                country TEXT,
                city TEXT,
                before_photo_id TEXT NOT NULL,
                after_photo_id TEXT NOT NULL,
                timestamp TEXT,
                verified BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Protest media uploads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protest_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                country TEXT,
                city TEXT,
                media_type TEXT,
                file_id TEXT NOT NULL,
                caption TEXT,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Protest organizers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS protest_organizers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                country TEXT NOT NULL,
                city TEXT NOT NULL,
                telegram_handle TEXT NOT NULL,
                verified BOOLEAN DEFAULT 0,
                volunteer_count INTEGER DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Streak tracking for daily/weekly activity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_streaks (
                user_id INTEGER,
                streak_type TEXT,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_action_date TEXT,
                total_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, streak_type),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Achievement definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                points_reward INTEGER DEFAULT 0,
                badge TEXT NOT NULL,
                requirement_type TEXT NOT NULL,
                requirement_value INTEGER NOT NULL,
                is_secret BOOLEAN DEFAULT 0
            )
        """)
        
        # User achievement unlocks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER,
                achievement_id TEXT,
                unlocked_at TEXT NOT NULL,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements (achievement_id)
            )
        """)
        
        # Weekly challenges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                challenge_name TEXT NOT NULL,
                objective_type TEXT NOT NULL,
                objective_target INTEGER NOT NULL,
                points_reward INTEGER DEFAULT 0,
                badge TEXT,
                multiplier REAL DEFAULT 1.0,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # User challenge progress
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_challenge_progress (
                user_id INTEGER,
                challenge_id INTEGER,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                completed_at TEXT,
                PRIMARY KEY (user_id, challenge_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (challenge_id) REFERENCES weekly_challenges (challenge_id)
            )
        """)
        
        # Prestige system
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_prestige (
                user_id INTEGER PRIMARY KEY,
                prestige_level INTEGER DEFAULT 0,
                total_lifetime_points INTEGER DEFAULT 0,
                prestige_history TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Active events (time-based multipliers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                multiplier REAL DEFAULT 1.0,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                applies_to TEXT DEFAULT 'all',
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully with advanced gamification")
    
    def add_user(self, user_id: int, username: Optional[str] = None, 
                 first_name: Optional[str] = None):
        """Add new user or update existing"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO users (user_id, username, first_name, joined_date, last_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_active = excluded.last_active
        """, (user_id, username, first_name, now, now))
        
        conn.commit()
        conn.close()
        logger.info(f"User {user_id} added/updated")
    
    def add_points(self, user_id: int, points: int, action_type: str, 
                   details: Optional[str] = None):
        """Add points to user and log action"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Update user score
        cursor.execute("""
            UPDATE users 
            SET imtiaz = imtiaz + ?,
                last_active = ?
            WHERE user_id = ?
        """, (points, datetime.now().isoformat(), user_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO actions (user_id, action_type, points, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, action_type, points, datetime.now().isoformat(), details))
        
        # Update role based on points
        cursor.execute("SELECT imtiaz FROM users WHERE user_id = ?", (user_id,))
        imtiaz = cursor.fetchone()[0]
        
        role = self._calculate_role(imtiaz)
        cursor.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Added {points} points to user {user_id} for {action_type}")
        
        return imtiaz, role
    
    def _calculate_role(self, imtiaz: int) -> str:
        """Calculate role based on points - 12 level EXPONENTIAL progression"""
        if imtiaz >= 10000:
            return '👑 مارشال'
        elif imtiaz >= 6500:
            return '👑 سپهبد'
        elif imtiaz >= 4000:
            return '💎 سرلشکر'
        elif imtiaz >= 2500:
            return '⭐ سرتیپ دوم'
        elif imtiaz >= 1600:
            return '🎖️ سرتیپ'
        elif imtiaz >= 1000:
            return '🥇 سرهنگ'
        elif imtiaz >= 600:
            return '🥇 سرگرد'
        elif imtiaz >= 370:
            return '🥈 سروان'
        elif imtiaz >= 220:
            return '🥈 ستوان دوم'
        elif imtiaz >= 120:
            return '🥈 ستوان یکم'
        elif imtiaz >= 50:
            return '🥉 گروهبان یکم'
        else:
            return '🥉 سرباز'
    
    def get_user_stats(self, user_id: int) -> Optional[Tuple]:
        """Get user statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, first_name, imtiaz, role, joined_date
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Get top users by points"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, first_name, imtiaz, role
            FROM users
            ORDER BY imtiaz DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank position"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) + 1
            FROM users
            WHERE imtiaz > (SELECT imtiaz FROM users WHERE user_id = ?)
        """, (user_id,))
        
        rank = cursor.fetchone()[0]
        conn.close()
        
        return rank
    
    def log_conduit_verification(self, user_id: int, screenshot_file_id: str, data_shared: str = None, 
                                  points_earned: int = 0, ocr_extracted_amount: float = None, 
                                  ocr_confidence: int = None, verification_method: str = 'manual', 
                                  ocr_raw_text: str = None):
        """Log conduit screenshot submission with OCR data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conduit_verifications 
            (user_id, screenshot_file_id, data_shared, points_earned, ocr_extracted_amount, 
             ocr_confidence, verification_method, ocr_raw_text, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, screenshot_file_id, data_shared, points_earned, ocr_extracted_amount,
              ocr_confidence, verification_method, ocr_raw_text, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_actions(self, user_id: int, limit: int = 10) -> List[Tuple]:
        """Get recent actions by user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT action_type, points, timestamp, details
            FROM actions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    # Protest Events Methods
    
    def create_protest_event(self, country: str, city: str, location: str, 
                            date: str, time: str, organizer_contact: str, 
                            created_by: int) -> int:
        """Create new protest event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO protest_events 
            (country, city, location, date, time, organizer_contact, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (country, city, location, date, time, organizer_contact, created_by, 
              datetime.now().isoformat()))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Protest event {event_id} created by user {created_by}")
        
        return event_id
    
    def get_protest_events_by_country(self, country: str) -> List[Tuple]:
        """Get all protest events for a country"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_id, city, location, date, time, organizer_contact, attendee_count
            FROM protest_events
            WHERE country = ?
            ORDER BY date ASC
        """, (country,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_protest_event(self, event_id: int) -> Optional[Tuple]:
        """Get specific protest event details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT country, city, location, date, time, organizer_contact, attendee_count
            FROM protest_events
            WHERE event_id = ?
        """, (event_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def mark_protest_attendance(self, event_id: int, user_id: int) -> bool:
        """Mark user attendance for protest event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO protest_attendance (event_id, user_id, confirmed_at)
                VALUES (?, ?, ?)
            """, (event_id, user_id, datetime.now().isoformat()))
            
            # Increment attendee count
            cursor.execute("""
                UPDATE protest_events
                SET attendee_count = attendee_count + 1
                WHERE event_id = ?
            """, (event_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"User {user_id} marked attendance for event {event_id}")
            return True
        except sqlite3.IntegrityError:
            conn.close()
            logger.warning(f"User {user_id} already marked attendance for event {event_id}")
            return False
    
    def get_unique_countries(self) -> List[str]:
        """Get list of countries with protest events"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT country FROM protest_events
            ORDER BY country
        """)
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    # Cleanup Actions Methods
    
    def add_cleanup_action(self, user_id: int, location: str, country: str,
                          city: str, before_photo_id: str, after_photo_id: str):
        """Log cleanup action"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO cleanup_actions 
            (user_id, protest_location, country, city, before_photo_id, after_photo_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, location, country, city, before_photo_id, after_photo_id, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"Cleanup action logged for user {user_id}")
    
    def get_recent_cleanups(self, limit: int = 10) -> List[Tuple]:
        """Get recent cleanup actions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.username, u.first_name, c.country, c.city, 
                   c.before_photo_id, c.after_photo_id, c.timestamp
            FROM cleanup_actions c
            JOIN users u ON c.user_id = u.user_id
            ORDER BY c.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    # Protest Media Methods
    
    def add_protest_media(self, user_id: int, country: str, city: str,
                         media_type: str, file_id: str, caption: Optional[str] = None):
        """Add protest media upload"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO protest_media 
            (user_id, country, city, media_type, file_id, caption, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, country, city, media_type, file_id, caption, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        logger.info(f"Protest media added by user {user_id}")
    
    def get_protest_media_by_country(self, country: str, limit: int = 20) -> List[Tuple]:
        """Get protest media for a country"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.username, u.first_name, pm.city, pm.media_type, 
                   pm.file_id, pm.caption, pm.timestamp
            FROM protest_media pm
            JOIN users u ON pm.user_id = u.user_id
            WHERE pm.country = ?
            ORDER BY pm.timestamp DESC
            LIMIT ?
        """, (country, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    # Protest Organizers Methods
    
    def add_protest_organizer(self, user_id: int, country: str, city: str,
                             telegram_handle: str) -> bool:
        """Add protest organizer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO protest_organizers 
                (user_id, country, city, telegram_handle, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, country, city, telegram_handle, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"Organizer {user_id} added for {city}, {country}")
            return True
        except sqlite3.IntegrityError:
            conn.close()
            logger.warning(f"User {user_id} already registered as organizer")
            return False
    
    def get_organizers_by_country(self, country: str) -> List[Tuple]:
        """Get organizers for a country (verified only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT city, telegram_handle, volunteer_count, verified
            FROM protest_organizers
            WHERE country = ? AND verified = 1
            ORDER BY city
        """, (country,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results

    # ========== ADVANCED GAMIFICATION FEATURES ==========
    
    def check_and_update_streak(self, user_id: int, action_type: str) -> Dict:
        """Check and update streak, return streak info and bonus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Get current streak
        cursor.execute('''
            SELECT current_streak, longest_streak, last_action_date, total_count
            FROM user_streaks WHERE user_id = ? AND streak_type = ?
        ''', (user_id, action_type))
        
        row = cursor.fetchone()
        
        if row:
            current_streak, longest_streak, last_date, total_count = row
            
            # Check if continued streak
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            
            if last_date == today:
                # Already did today, no bonus
                conn.close()
                return {'streak': current_streak, 'bonus_points': 0, 'multiplier': self._get_streak_multiplier(current_streak)}
            elif last_date == yesterday:
                # Continue streak
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                # Streak broken, reset
                current_streak = 1
            
            cursor.execute('''
                UPDATE user_streaks 
                SET current_streak = ?, longest_streak = ?, last_action_date = ?, total_count = ?
                WHERE user_id = ? AND streak_type = ?
            ''', (current_streak, longest_streak, today, total_count + 1, user_id, action_type))
        else:
            # First time
            current_streak = 1
            longest_streak = 1
            cursor.execute('''
                INSERT INTO user_streaks (user_id, streak_type, current_streak, longest_streak, last_action_date, total_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, action_type, 1, 1, today, 1))
        
        conn.commit()
        conn.close()
        
        # Calculate bonus
        bonus_points = self._get_streak_bonus(current_streak)
        multiplier = self._get_streak_multiplier(current_streak)
        
        return {
            'streak': current_streak,
            'longest': longest_streak,
            'bonus_points': bonus_points,
            'multiplier': multiplier,
            'badge': self._get_streak_badge(current_streak)
        }
    
    def _get_streak_bonus(self, streak: int) -> int:
        """Get bonus points for streak milestones"""
        from config import STREAK_BONUSES
        for days in sorted(STREAK_BONUSES.keys(), reverse=True):
            if streak >= days and streak % days == 0:
                return STREAK_BONUSES[days]['points']
        return 0
    
    def _get_streak_multiplier(self, streak: int) -> float:
        """Get point multiplier based on current streak"""
        from config import STREAK_BONUSES
        multiplier = 1.0
        for days in sorted(STREAK_BONUSES.keys()):
            if streak >= days:
                multiplier = STREAK_BONUSES[days]['multiplier']
        return multiplier
    
    def _get_streak_badge(self, streak: int) -> str:
        """Get badge emoji for streak"""
        from config import STREAK_BONUSES
        badge = ''
        for days in sorted(STREAK_BONUSES.keys()):
            if streak >= days:
                badge = STREAK_BONUSES[days]['badge']
        return badge
    
    def get_user_streaks(self, user_id: int) -> List[Dict]:
        """Get all active streaks for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT streak_type, current_streak, longest_streak, total_count
            FROM user_streaks WHERE user_id = ?
            ORDER BY current_streak DESC
        ''', (user_id,))
        
        results = [{'type': row[0], 'current': row[1], 'longest': row[2], 'total': row[3]} for row in cursor.fetchall()]
        conn.close()
        return results
    
    def check_daily_combo(self, user_id: int) -> Dict:
        """Check if user completed multiple diverse actions today and award combo bonus"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Count unique action types today
        cursor.execute('''
            SELECT COUNT(DISTINCT action_type) as unique_actions
            FROM actions 
            WHERE user_id = ? AND timestamp >= ?
        ''', (user_id, today_start))
        
        row = cursor.fetchone()
        conn.close()
        
        unique_actions = row[0] if row else 0
        
        # Check combo bonuses
        from config import COMBO_BONUSES
        bonus_points = 0
        badge = ''
        
        for combo_count in sorted(COMBO_BONUSES.keys(), reverse=True):
            if unique_actions >= combo_count:
                bonus_points = COMBO_BONUSES[combo_count]['points']
                badge = COMBO_BONUSES[combo_count]['badge']
                break
        
        return {
            'unique_actions': unique_actions,
            'bonus_points': bonus_points,
            'badge': badge
        }
    
    def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get unlocked achievements for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.achievement_id, a.name, a.description, a.badge, ua.unlocked_at
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.achievement_id
            WHERE ua.user_id = ?
            ORDER BY ua.unlocked_at DESC
        ''', (user_id,))
        
        results = [{'id': row[0], 'name': row[1], 'description': row[2], 'badge': row[3], 'unlocked': row[4]} for row in cursor.fetchall()]
        conn.close()
        return results
