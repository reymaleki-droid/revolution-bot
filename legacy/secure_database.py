"""
Secure Database Module for Zero-Knowledge Architecture
Implements irreversible user_id hashing with PBKDF2-HMAC-SHA256
No PII stored - admin can only see aggregate statistics
"""

import hashlib
import secrets
import json
import logging
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SecureDatabase:
    """Zero-knowledge database with irreversible user hashing"""
    
    def __init__(self, db_path: str = "revolution_bot_secure.db"):
        self.db_path = db_path
        self.salt = self._load_or_create_salt()
        self.init_database()
        logger.info("Secure database initialized with zero-knowledge architecture")
    
    def _load_or_create_salt(self) -> bytes:
        """Load or create 32-byte salt for user_id hashing"""
        import os as _os
        import stat
        salt_file = Path("user_hash.salt")
        if salt_file.exists():
            with open(salt_file, "rb") as f:
                return f.read()
        else:
            salt = secrets.token_bytes(32)
            with open(salt_file, "wb") as f:
                f.write(salt)
            # SEC-006: Set restrictive file permissions (owner read/write only)
            try:
                _os.chmod(salt_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600
            except Exception as e:
                logger.warning(f"Could not set salt file permissions: {e}")
            logger.warning("Created new salt file - BACKUP THIS FILE!")
            logger.warning("Salt file location: " + str(salt_file.absolute()))
            return salt
    
    def _hash_user_id(self, user_id: int) -> str:
        """Irreversibly hash user_id using PBKDF2-HMAC-SHA256"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            str(user_id).encode(),
            self.salt,
            100000  # 100k iterations
        ).hex()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema - NO PII columns"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table - only hashed ID, points, role, join date
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_hash TEXT PRIMARY KEY,
                imtiaz INTEGER DEFAULT 0,
                role TEXT DEFAULT 'میهن‌پرست',
                joined_date TEXT NOT NULL
            )
        ''')
        
        # Actions table - expires after 30 days (but user record persists)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                action_type TEXT NOT NULL,
                points INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # Conduit verifications - NO screenshot or OCR text stored
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conduit_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                tier TEXT NOT NULL,
                gb_amount REAL NOT NULL,
                points INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # Statistics table - anonymous aggregates only
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Certificates table - verifiable digital certificates for ranks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                certificate_id TEXT UNIQUE NOT NULL,
                rank TEXT NOT NULL,
                imtiaz INTEGER NOT NULL,
                issued_date TEXT NOT NULL,
                verification_hash TEXT NOT NULL,
                qr_code_data TEXT NOT NULL,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # Impact metrics table - track real-world impact
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                value INTEGER NOT NULL,
                description TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # Legacy archive table - permanent historical record
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legacy_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                anonymous_id TEXT UNIQUE NOT NULL,
                contribution_summary TEXT NOT NULL,
                total_impact INTEGER NOT NULL,
                archived_date TEXT NOT NULL,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # Physical rewards table - NON-REPLICABLE milestone rewards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS physical_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                anonymous_id TEXT UNIQUE NOT NULL,
                reward_type TEXT NOT NULL,
                rank_achieved TEXT NOT NULL,
                max_rank_achieved TEXT NOT NULL,
                eligibility_date TEXT NOT NULL,
                unique_serial_number TEXT UNIQUE NOT NULL,
                hologram_code TEXT UNIQUE NOT NULL,
                claim_status TEXT DEFAULT 'eligible',
                notes TEXT,
                FOREIGN KEY (user_hash) REFERENCES users(user_hash)
            )
        ''')
        
        # SEC-007: Rate limits table for persistent cooldowns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_hash TEXT NOT NULL,
                action TEXT NOT NULL,
                last_action TEXT NOT NULL,
                PRIMARY KEY (user_hash, action)
            )
        ''')
        
        # Initialize statistics if not exists
        stats_to_init = [
            ('total_users', '0'),
            ('total_gb_shared', '0.0'),
            ('total_cleanups', '0'),
            ('total_protests', '0'),
            ('actions_by_type', '{}'),
            ('conduit_tier_distribution', '{}'),
            ('protests_by_country', '{}')
        ]
        
        for key, default_value in stats_to_init:
            cursor.execute(
                'INSERT OR IGNORE INTO statistics (key, value) VALUES (?, ?)',
                (key, default_value)
            )
        
        conn.commit()
        conn.close()
        logger.info("Database schema initialized with zero-knowledge design")
    
    def add_user(self, user_id: int) -> bool:
        """Add new user (hashed ID only) - NO username or first_name"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (user_hash, joined_date) VALUES (?, ?)',
                (user_hash, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            self._increment_stat('total_users', 1)
            logger.info("New user added (identity protected)")
            return True
        except sqlite3.IntegrityError:
            conn.close()
            logger.debug("User already exists")
            return False
    
    def get_user_hash(self, user_id: int) -> str:
        """SEC-007: Get user hash for rate limiting"""
        return self._hash_user_id(user_id)
    
    def get_last_action(self, user_hash: str, action: str) -> Optional[datetime]:
        """SEC-007: Get last action timestamp for rate limiting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT last_action FROM rate_limits WHERE user_hash = ? AND action = ?',
            (user_hash, action)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return datetime.fromisoformat(row['last_action'])
        return None
    
    def set_last_action(self, user_hash: str, action: str) -> None:
        """SEC-007: Set last action timestamp for rate limiting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO rate_limits (user_hash, action, last_action)
               VALUES (?, ?, ?)''',
            (user_hash, action, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def add_points(self, user_id: int, points: int, action_type: str) -> Optional[Dict]:
        """Add points to user and log action (expires in 30 days)
        Returns certificate data if rank changed, None otherwise"""
        user_hash = self._hash_user_id(user_id)
        
        # Ensure user exists
        self.add_user(user_id)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get old role for comparison
        cursor.execute(
            'SELECT imtiaz, role FROM users WHERE user_hash = ?',
            (user_hash,)
        )
        old_data = cursor.fetchone()
        old_role = old_data['role'] if old_data else 'میهن‌پرست'
        
        # Update user points
        cursor.execute(
            'UPDATE users SET imtiaz = imtiaz + ? WHERE user_hash = ?',
            (points, user_hash)
        )
        
        # Get new total for role calculation
        cursor.execute(
            'SELECT imtiaz FROM users WHERE user_hash = ?',
            (user_hash,)
        )
        imtiaz = cursor.fetchone()['imtiaz']
        new_role = self._calculate_role(imtiaz)
        
        cursor.execute(
            'UPDATE users SET role = ? WHERE user_hash = ?',
            (new_role, user_hash)
        )
        
        # Log action with 30-day expiry
        timestamp = datetime.now()
        expires_at = timestamp + timedelta(days=30)
        
        cursor.execute(
            'INSERT INTO actions (user_hash, action_type, points, timestamp, expires_at) VALUES (?, ?, ?, ?, ?)',
            (user_hash, action_type, points, timestamp.isoformat(), expires_at.isoformat())
        )
        
        conn.commit()
        conn.close()
        
        # Update statistics (after closing connection)
        self._increment_action_stat(action_type, 1)
        
        # Check if rank changed - auto-issue certificate
        certificate_data = None
        physical_reward_data = None
        
        if old_role != new_role:
            logger.info(f"Rank changed: {old_role} → {new_role} - issuing certificate")
            try:
                certificate_data = self.issue_certificate(user_id, new_role, imtiaz)
                
                # Check if eligible for physical reward (top 3 ranks)
                if new_role in ['مارشال', 'سپهبد', 'سرلشکر']:
                    physical_reward_data = self.register_physical_reward(user_id, new_role)
                    if physical_reward_data:
                        logger.info(f"🏅 Physical reward registered: {physical_reward_data['reward_type']}")
                        # Add to certificate data for notification
                        certificate_data['physical_reward'] = physical_reward_data
                
            except Exception as e:
                logger.error(f"Failed to issue certificate: {e}")
        
        logger.info(f"Points awarded for action (identity protected)")
        return certificate_data
    
    def log_conduit_verification(self, user_id: int, tier: str, gb_amount: float, points: int):
        """Log Conduit verification - NO screenshot or OCR stored"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO conduit_verifications (user_hash, tier, gb_amount, points, timestamp) VALUES (?, ?, ?, ?, ?)',
            (user_hash, tier, gb_amount, points, datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
        
        # Update statistics (after closing connection)
        self._increment_stat_float('total_gb_shared', gb_amount)
        self._increment_tier_stat(tier, 1)
        
        logger.info(f"Conduit verification logged: {tier} tier, {gb_amount} GB (identity protected)")
    
    def log_cleanup(self, user_id: int, points: int):
        """Log cleanup action - NO photo stored"""
        self.add_points(user_id, points, 'cleanup')
        self._increment_stat('total_cleanups', 1)
        logger.info("Cleanup logged (photo deleted, identity protected)")
    
    def log_protest(self, country: str):
        """Log protest - NO user tracking or organizer info"""
        self._increment_stat('total_protests', 1)
        self._increment_country_stat(country, 1)
        logger.info(f"Protest logged for {country} (no user tracking)")
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user's own stats (imtiaz, role, join date)"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT imtiaz, role, joined_date FROM users WHERE user_hash = ?',
            (user_hash,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'imtiaz': row['imtiaz'],
                'role': row['role'],
                'joined_date': row['joined_date']
            }
        return None
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int, str]]:
        """Get top users - returns (rank, points, role) - NO usernames"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT imtiaz, role FROM users ORDER BY imtiaz DESC LIMIT ?',
            (limit,)
        )
        
        leaderboard = []
        for rank, row in enumerate(cursor.fetchall(), 1):
            leaderboard.append((rank, row['imtiaz'], row['role']))
        
        conn.close()
        return leaderboard
    
    def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank position"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT imtiaz FROM users WHERE user_hash = ?',
            (user_hash,)
        )
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        user_imtiaz = row['imtiaz']
        
        cursor.execute(
            'SELECT COUNT(*) as rank FROM users WHERE imtiaz > ?',
            (user_imtiaz,)
        )
        
        rank = cursor.fetchone()['rank'] + 1
        conn.close()
        return rank
    
    def get_aggregate_statistics(self) -> Dict:
        """Get anonymous aggregate statistics for admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM statistics')
        stats = {}
        
        for row in cursor.fetchall():
            key = row['key']
            value = row['value']
            
            # Parse JSON values
            if key in ['actions_by_type', 'conduit_tier_distribution', 'protests_by_country']:
                stats[key] = json.loads(value)
            elif key == 'total_gb_shared':
                stats[key] = float(value)
            else:
                stats[key] = int(value)
        
        conn.close()
        return stats
    
    def delete_user_data(self, user_id: int):
        """Delete user's actions but KEEP imtiaz and role (honor preserved)"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete temporary data (actions, conduit verifications)
        cursor.execute('DELETE FROM actions WHERE user_hash = ?', (user_hash,))
        cursor.execute('DELETE FROM conduit_verifications WHERE user_hash = ?', (user_hash,))
        
        # Keep user record with imtiaz and role
        conn.commit()
        conn.close()
        logger.info("User data deleted (points and role preserved for honor)")
    
    def auto_purge_expired_data(self):
        """Auto-delete actions older than 30 days - KEEPS user records"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM actions WHERE expires_at < ?',
            (datetime.now().isoformat(),)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Auto-purged {deleted_count} expired actions (user records preserved)")
    
    def _calculate_role(self, imtiaz: int) -> str:
        """Calculate role based on imtiaz thresholds - 12 level EXPONENTIAL progression"""
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
    
    def _increment_stat(self, key: str, increment: int):
        """Increment integer statistic"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM statistics WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            new_value = int(row['value']) + increment
            cursor.execute('UPDATE statistics SET value = ? WHERE key = ?', (str(new_value), key))
        else:
            cursor.execute('INSERT INTO statistics (key, value) VALUES (?, ?)', (key, str(increment)))
        
        conn.commit()
        conn.close()
    
    def _increment_stat_float(self, key: str, increment: float):
        """Increment float statistic"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM statistics WHERE key = ?', (key,))
        row = cursor.fetchone()
        
        if row:
            new_value = float(row['value']) + increment
            cursor.execute('UPDATE statistics SET value = ? WHERE key = ?', (str(new_value), key))
        else:
            cursor.execute('INSERT INTO statistics (key, value) VALUES (?, ?)', (key, str(increment)))
        
        conn.commit()
        conn.close()
    
    def _increment_action_stat(self, action_type: str, increment: int):
        """Increment action type counter in JSON statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM statistics WHERE key = ?', ('actions_by_type',))
        row = cursor.fetchone()
        
        actions_dict = json.loads(row['value']) if row else {}
        actions_dict[action_type] = actions_dict.get(action_type, 0) + increment
        
        cursor.execute(
            'UPDATE statistics SET value = ? WHERE key = ?',
            (json.dumps(actions_dict), 'actions_by_type')
        )
        
        conn.commit()
        conn.close()
    
    def _increment_tier_stat(self, tier: str, increment: int):
        """Increment Conduit tier distribution in JSON statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM statistics WHERE key = ?', ('conduit_tier_distribution',))
        row = cursor.fetchone()
        
        tiers_dict = json.loads(row['value']) if row else {}
        tiers_dict[tier] = tiers_dict.get(tier, 0) + increment
        
        cursor.execute(
            'UPDATE statistics SET value = ? WHERE key = ?',
            (json.dumps(tiers_dict), 'conduit_tier_distribution')
        )
        
        conn.commit()
        conn.close()
    
    def get_unique_countries(self) -> List[str]:
        """Get list of countries with protests (returns empty list for secure DB)"""
        # Secure database doesn't store protest events
        # Return default list for now
        return []
    
    def get_protest_events_by_country(self, country: str):
        """Get protest events by country (not implemented in secure DB)"""
        # Secure database doesn't store detailed protest events
        return []
    
    def _increment_country_stat(self, country: str, increment: int):
        """Increment protest country counter in JSON statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM statistics WHERE key = ?', ('protests_by_country',))
        row = cursor.fetchone()
        
        countries_dict = json.loads(row['value']) if row else {}
        countries_dict[country] = countries_dict.get(country, 0) + increment
        
        cursor.execute(
            'UPDATE statistics SET value = ? WHERE key = ?',
            (json.dumps(countries_dict), 'protests_by_country')
        )
        
        conn.commit()
        conn.close()

    # ========== ADVANCED GAMIFICATION FEATURES ==========
    
    def check_and_update_streak(self, user_id: int, action_type: str) -> Dict:
        """Check and update streak, return streak info and bonus"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Get current streak
        cursor.execute('''
            SELECT current_streak, longest_streak, last_action_date, total_count
            FROM user_streaks WHERE user_hash = ? AND streak_type = ?
        ''', (user_hash, action_type))
        
        row = cursor.fetchone()
        
        if row:
            current_streak = row['current_streak']
            longest_streak = row['longest_streak']
            last_date = row['last_action_date']
            total_count = row['total_count']
            
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
                WHERE user_hash = ? AND streak_type = ?
            ''', (current_streak, longest_streak, today, total_count + 1, user_hash, action_type))
        else:
            # First time
            current_streak = 1
            longest_streak = 1
            cursor.execute('''
                INSERT INTO user_streaks (user_hash, streak_type, current_streak, longest_streak, last_action_date, total_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_hash, action_type, 1, 1, today, 1))
        
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
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT streak_type, current_streak, longest_streak, total_count
            FROM user_streaks WHERE user_hash = ?
            ORDER BY current_streak DESC
        ''', (user_hash,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def check_daily_combo(self, user_id: int) -> Dict:
        """Check if user completed multiple diverse actions today and award combo bonus"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Count unique action types today
        cursor.execute('''
            SELECT COUNT(DISTINCT action_type) as unique_actions
            FROM actions 
            WHERE user_hash = ? AND timestamp >= ?
        ''', (user_hash, today_start))
        
        row = cursor.fetchone()
        conn.close()
        
        unique_actions = row['unique_actions'] if row else 0
        
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
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.achievement_id, a.name, a.description, a.badge, ua.unlocked_at
            FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.achievement_id
            WHERE ua.user_hash = ?
            ORDER BY ua.unlocked_at DESC
        ''', (user_hash,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def check_and_unlock_achievements(self, user_id: int) -> List[Dict]:
        """Check user progress and unlock new achievements"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get user stats
        cursor.execute('SELECT imtiaz, role FROM users WHERE user_hash = ?', (user_hash,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return []
        
        imtiaz = user_row['imtiaz']
        
        # Count action types
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM actions
            WHERE user_hash = ?
            GROUP BY action_type
        ''', (user_hash,))
        action_counts = {row['action_type']: row['count'] for row in cursor.fetchall()}
        
        # Get already unlocked achievements
        cursor.execute('''
            SELECT achievement_id FROM user_achievements WHERE user_hash = ?
        ''', (user_hash,))
        unlocked = {row['achievement_id'] for row in cursor.fetchall()}
        
        # Check achievements
        newly_unlocked = []
        
        achievements_to_check = [
            # Milestone achievements
            ('first_step', 'اولین قدم', 'شروع سفر', 'general', 10, '🏅', 'points', 10),
            ('century', 'صد تایی', '100 امتیاز کسب کردید', 'milestone', 50, '⭐', 'points', 100),
            ('half_k', 'پانصد', '500 امتیاز کسب کردید', 'milestone', 100, '💫', 'points', 500),
            ('one_k', 'هزارتایی', '1000 امتیاز کسب کردید', 'milestone', 200, '🌟', 'points', 1000),
            
            # Specialist achievements
            ('twitter_master', 'توییتر استاد', '50 توییت به اشتراک گذاشتید', 'specialist', 100, '🐦', 'action_count', ('tweet_shared', 50)),
            ('email_warrior', 'ایمیل جنگجو', '100 ایمیل ارسال کردید', 'specialist', 150, '📧', 'action_count', ('email_sent', 100)),
            ('conduit_legend', 'افسانه Conduit', '1 ترابایت داده به اشتراک گذاشتید', 'specialist', 500, '💾', 'conduit_total', 1000),
            
            # Activity achievements
            ('active_week', 'هفته فعال', '7 روز متوالی فعال', 'activity', 80, '🔥', 'streak', 7),
            ('active_month', 'ماه فعال', '30 روز متوالی فعال', 'activity', 300, '🔥🔥🔥', 'streak', 30),
        ]
        
        for achievement_data in achievements_to_check:
            ach_id = achievement_data[0]
            
            if ach_id in unlocked:
                continue
            
            # Check if requirement met
            req_type = achievement_data[6]
            req_value = achievement_data[7]
            
            unlocked_now = False
            
            if req_type == 'points':
                unlocked_now = imtiaz >= req_value
            elif req_type == 'action_count':
                action_type, required_count = req_value
                unlocked_now = action_counts.get(action_type, 0) >= required_count
            
            if unlocked_now:
                # Insert achievement
                cursor.execute('''
                    INSERT OR IGNORE INTO achievements 
                    (achievement_id, name, description, category, points_reward, badge, requirement_type, requirement_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', achievement_data[:8])
                
                # Unlock for user
                cursor.execute('''
                    INSERT INTO user_achievements (user_hash, achievement_id, unlocked_at)
                    VALUES (?, ?, ?)
                ''', (user_hash, ach_id, datetime.now().isoformat()))
                
                newly_unlocked.append({
                    'id': ach_id,
                    'name': achievement_data[1],
                    'description': achievement_data[2],
                    'badge': achievement_data[5],
                    'points': achievement_data[4]
                })
        
        conn.commit()
        conn.close()
        
        return newly_unlocked

    def issue_certificate(self, user_id: int, rank: str, imtiaz: int) -> Dict:
        """Issue a verifiable digital certificate for rank achievement"""
        user_hash = self._hash_user_id(user_id)
        timestamp = datetime.now().isoformat()
        
        # Generate certificate data
        from certificate_generator import get_certificate_generator
        generator = get_certificate_generator()
        
        certificate_id = generator.generate_certificate_id(user_hash, rank, timestamp)
        verification_hash = generator.generate_verification_hash(certificate_id, rank, imtiaz)
        qr_data = f"VERIFY:{certificate_id}:{verification_hash}"
        
        # Store in database
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO certificates 
            (user_hash, certificate_id, rank, imtiaz, issued_date, verification_hash, qr_code_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_hash, certificate_id, rank, imtiaz, timestamp, verification_hash, qr_data))
        
        conn.commit()
        conn.close()
        
        # Generate certificate image
        cert_path = generator.create_certificate(
            certificate_id,
            rank,
            imtiaz,
            timestamp.split('T')[0],
            verification_hash
        )
        
        logger.info(f"Certificate issued: {certificate_id}")
        
        return {
            'certificate_id': certificate_id,
            'verification_hash': verification_hash,
            'qr_data': qr_data,
            'image_path': cert_path,
            'issued_date': timestamp
        }
    
    def get_user_certificates(self, user_id: int) -> List[Dict]:
        """Get all certificates for a user"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT certificate_id, rank, imtiaz, issued_date, verification_hash
            FROM certificates
            WHERE user_hash = ?
            ORDER BY issued_date DESC
        ''', (user_hash,))
        
        certificates = []
        for row in cursor.fetchall():
            certificates.append({
                'certificate_id': row['certificate_id'],
                'rank': row['rank'],
                'imtiaz': row['imtiaz'],
                'issued_date': row['issued_date'],
                'verification_hash': row['verification_hash']
            })
        
        conn.close()
        return certificates
    
    def verify_certificate(self, certificate_id: str) -> Optional[Dict]:
        """Verify a certificate by its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rank, imtiaz, issued_date, verification_hash
            FROM certificates
            WHERE certificate_id = ?
        ''', (certificate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'valid': True,
                'rank': row['rank'],
                'imtiaz': row['imtiaz'],
                'issued_date': row['issued_date'],
                'verification_hash': row['verification_hash']
            }
        return None
    
    def add_impact_metric(self, user_id: int, metric_type: str, value: int, description: str):
        """Record real-world impact metric"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO impact_metrics (user_hash, metric_type, value, description, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_hash, metric_type, value, description, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Impact metric recorded: {metric_type} = {value}")
    
    def get_user_impact(self, user_id: int) -> Dict:
        """Get user's impact metrics"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT metric_type, SUM(value) as total, COUNT(*) as count
            FROM impact_metrics
            WHERE user_hash = ?
            GROUP BY metric_type
        ''', (user_hash,))
        
        impact = {}
        for row in cursor.fetchall():
            impact[row['metric_type']] = {
                'total': row['total'],
                'count': row['count']
            }
        
        conn.close()
        return impact
    
    def create_legacy_record(self, user_id: int) -> str:
        """Create permanent legacy archive record"""
        user_hash = self._hash_user_id(user_id)
        
        # Generate anonymous ID
        anonymous_id = f"ACTIVIST-{secrets.token_hex(8).upper()}"
        
        # Get user stats
        stats = self.get_user_stats(user_id)
        impact = self.get_user_impact(user_id)
        
        # Create contribution summary
        contribution_summary = f"Rank: {stats['role']} | Points: {stats['imtiaz']}"
        total_impact = sum(m['total'] for m in impact.values())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO legacy_archive 
            (user_hash, anonymous_id, contribution_summary, total_impact, archived_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_hash, anonymous_id, contribution_summary, total_impact, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Legacy record created: {anonymous_id}")
        return anonymous_id

    def register_physical_reward(self, user_id: int, rank: str) -> Optional[Dict]:
        """
        Register user for NON-REPLICABLE physical reward (Marshal rank+)
        Creates unique serial number and hologram code
        """
        # Only for top ranks
        top_ranks = ['مارشال', 'سپهبد', 'سرلشکر']
        if rank not in top_ranks:
            return None
        
        user_hash = self._hash_user_id(user_id)
        
        # Check if already registered
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM physical_rewards WHERE user_hash = ?
        ''', (user_hash,))
        
        existing = cursor.fetchone()
        
        # If exists, update only if higher rank
        if existing:
            # Check if current rank is higher
            rank_order = {'سرلشکر': 1, 'سپهبد': 2, 'مارشال': 3}
            current_rank_value = rank_order.get(rank, 0)
            existing_rank_value = rank_order.get(existing['max_rank_achieved'], 0)
            
            if current_rank_value > existing_rank_value:
                cursor.execute('''
                    UPDATE physical_rewards 
                    SET max_rank_achieved = ?, eligibility_date = ?
                    WHERE user_hash = ?
                ''', (rank, datetime.now().isoformat(), user_hash))
                conn.commit()
                conn.close()
                logger.info(f"Physical reward upgraded to {rank}")
                return {
                    'serial_number': existing['unique_serial_number'],
                    'hologram_code': existing['hologram_code'],
                    'rank': rank,
                    'upgraded': True
                }
            else:
                conn.close()
                return None
        
        # Generate anonymous ID
        anonymous_id = f"HERO-{secrets.token_hex(6).upper()}"
        
        # Generate UNIQUE serial number (non-replicable)
        serial_number = f"IRL-{rank[:3].upper()}-{secrets.token_hex(6).upper()}"
        
        # Generate hologram security code (anti-counterfeit)
        hologram_code = f"HOL-{hashlib.sha256(f'{user_hash}:{rank}:{datetime.now().isoformat()}'.encode()).hexdigest()[:12].upper()}"
        
        # Determine reward type
        reward_type = {
            'مارشال': 'MARSHAL_GOLD_PLAQUE',
            'سپهبد': 'GENERAL_SILVER_MEDAL',
            'سرلشکر': 'LIEUTENANT_BRONZE_MEDAL'
        }.get(rank, 'UNKNOWN')
        
        cursor.execute('''
            INSERT INTO physical_rewards 
            (user_hash, anonymous_id, reward_type, rank_achieved, max_rank_achieved, 
             eligibility_date, unique_serial_number, hologram_code, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_hash,
            anonymous_id,
            reward_type,
            rank,
            rank,
            datetime.now().isoformat(),
            serial_number,
            hologram_code,
            f"Registered on {datetime.now().strftime('%Y-%m-%d')} for post-liberation physical reward"
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Physical reward registered: {reward_type} for {rank} - Serial: {serial_number}")
        
        return {
            'anonymous_id': anonymous_id,
            'reward_type': reward_type,
            'serial_number': serial_number,
            'hologram_code': hologram_code,
            'rank': rank,
            'eligibility_date': datetime.now().isoformat()
        }
    
    def get_physical_reward_status(self, user_id: int) -> Optional[Dict]:
        """Get user's physical reward eligibility status"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT anonymous_id, reward_type, rank_achieved, max_rank_achieved,
                   eligibility_date, unique_serial_number, hologram_code, claim_status
            FROM physical_rewards
            WHERE user_hash = ?
        ''', (user_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'anonymous_id': row['anonymous_id'],
                'reward_type': row['reward_type'],
                'rank_achieved': row['rank_achieved'],
                'max_rank_achieved': row['max_rank_achieved'],
                'eligibility_date': row['eligibility_date'],
                'serial_number': row['unique_serial_number'],
                'hologram_code': row['hologram_code'],
                'claim_status': row['claim_status']
            }
        return None
    
    def get_all_physical_rewards(self) -> List[Dict]:
        """Get all physical reward registrations (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT anonymous_id, reward_type, max_rank_achieved, 
                   eligibility_date, unique_serial_number, hologram_code, claim_status
            FROM physical_rewards
            ORDER BY eligibility_date DESC
        ''')
        
        rewards = []
        for row in cursor.fetchall():
            rewards.append({
                'anonymous_id': row['anonymous_id'],
                'reward_type': row['reward_type'],
                'rank': row['max_rank_achieved'],
                'eligibility_date': row['eligibility_date'],
                'serial_number': row['unique_serial_number'],
                'hologram_code': row['hologram_code'],
                'claim_status': row['claim_status']
            })
        
        conn.close()
        return rewards
    
    def verify_physical_reward(self, serial_number: str) -> Optional[Dict]:
        """Verify authenticity of physical reward by serial number (anti-counterfeit)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT anonymous_id, reward_type, max_rank_achieved, 
                   eligibility_date, hologram_code, claim_status
            FROM physical_rewards
            WHERE unique_serial_number = ?
        ''', (serial_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'valid': True,
                'anonymous_id': row['anonymous_id'],
                'reward_type': row['reward_type'],
                'rank': row['max_rank_achieved'],
                'eligibility_date': row['eligibility_date'],
                'hologram_code': row['hologram_code'],
                'claim_status': row['claim_status']
            }
        
        return {'valid': False, 'message': 'Serial number not found - COUNTERFEIT'}
