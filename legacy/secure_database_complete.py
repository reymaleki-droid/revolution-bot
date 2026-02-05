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
        salt_file = Path("user_hash.salt")
        if salt_file.exists():
            with open(salt_file, "rb") as f:
                return f.read()
        else:
            salt = secrets.token_bytes(32)
            with open(salt_file, "wb") as f:
                f.write(salt)
            logger.warning("Created new salt file - BACKUP THIS FILE!")
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
                role TEXT DEFAULT 'انقلابی',
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
            self._increment_stat('total_users', 1)
            conn.commit()
            logger.info("New user added (identity protected)")
            return True
        except sqlite3.IntegrityError:
            logger.debug("User already exists")
            return False
        finally:
            conn.close()
    
    def add_points(self, user_id: int, points: int, action_type: str):
        """Add points to user and log action (expires in 30 days)"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ensure user exists
        self.add_user(user_id)
        
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
        
        # Update statistics
        self._increment_action_stat(action_type, 1)
        
        conn.commit()
        conn.close()
        logger.info(f"Points awarded for action (identity protected)")
    
    def log_conduit_verification(self, user_id: int, tier: str, gb_amount: float, points: int):
        """Log Conduit verification - NO screenshot or OCR stored"""
        user_hash = self._hash_user_id(user_id)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO conduit_verifications (user_hash, tier, gb_amount, points, timestamp) VALUES (?, ?, ?, ?, ?)',
            (user_hash, tier, gb_amount, points, datetime.now().isoformat())
        )
        
        # Update statistics
        self._increment_stat_float('total_gb_shared', gb_amount)
        self._increment_tier_stat(tier, 1)
        
        conn.commit()
        conn.close()
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
        """Calculate role based on imtiaz thresholds"""
        if imtiaz >= 1000:
            return 'فرمانده'
        elif imtiaz >= 500:
            return 'معاون'
        elif imtiaz >= 250:
            return 'سرتیپ'
        elif imtiaz >= 100:
            return 'سرهنگ'
        elif imtiaz >= 50:
            return 'سرگرد'
        else:
            return 'انقلابی'
    
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
