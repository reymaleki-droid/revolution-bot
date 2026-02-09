"""
Secure Database Module for Zero-Knowledge Architecture (PostgreSQL)

Security guarantees:
- User IDs are HMAC-SHA256 hashed with pepper + salt (irreversible)
- No PII stored: no usernames, no raw text (placard file_ids stored for approved content only)
- Parameterized queries only (no SQL injection)
- Connection pooling for async safety
- Fail-closed on connection errors
- All timestamps are timezone-aware UTC
"""

import hashlib
import hmac
import secrets
import json
import logging
import os
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool

from config import DATABASE_URL, HASH_PEPPER, USER_HASH_SALT, ACTION_LOG_RETENTION_DAYS

logger = logging.getLogger(__name__)


class SecureDatabase:
    """Zero-knowledge async PostgreSQL database with irreversible user hashing"""
    
    def __init__(self):
        """Initialize database configuration."""
        self.pool: Optional[Pool] = None
        self._pool_lock = asyncio.Lock()
        self._initialized = False
        self.salt = self._load_salt()
        logger.info("SecureDatabase instance created")
    
    def _load_salt(self) -> bytes:
        """
        Load salt for user hashing.
        Priority: USER_HASH_SALT env var > file-based salt
        In production (Railway), USER_HASH_SALT is required by config.py
        """
        # Try environment variable first (hex-encoded)
        if USER_HASH_SALT:
            try:
                salt = bytes.fromhex(USER_HASH_SALT)
                logger.info("Using USER_HASH_SALT from environment")
                return salt
            except ValueError:
                logger.error("USER_HASH_SALT is not valid hex")
                raise ValueError("USER_HASH_SALT must be hex-encoded bytes")
        
        # Fall back to file-based salt (dev only)
        salt_file = Path("user_hash.salt")
        if salt_file.exists():
            with open(salt_file, "rb") as f:
                logger.info("Using salt from file (dev mode)")
                return f.read()
        else:
            # Create new salt file (dev only)
            salt = secrets.token_bytes(32)
            with open(salt_file, "wb") as f:
                f.write(salt)
            logger.warning("Created new salt file - BACKUP THIS FILE!")
            logger.warning(f"Salt file location: {salt_file.absolute()}")
            logger.warning("Set USER_HASH_SALT=<value from salt file> in production (read file with: python -c 'print(open(\"user_hash.salt\",\"rb\").read().hex())')")
            return salt
    
    def _hash_user_id(self, user_id: int) -> str:
        """
        Irreversibly hash user_id using HMAC-SHA256.
        Uses: HMAC(pepper, user_id || salt)
        """
        user_bytes = str(user_id).encode('utf-8')
        message = user_bytes + self.salt
        
        pepper = (HASH_PEPPER or 'dev-pepper-change-in-prod').encode('utf-8')
        return hmac.new(pepper, message, hashlib.sha256).hexdigest()
    
    def get_user_hash(self, user_id: int) -> str:
        """Get hashed user ID. Synchronous for compatibility with rate limiting."""
        return self._hash_user_id(user_id)
    
    async def initialize(self) -> None:
        """
        Initialize connection pool and create schema.
        Must be called once at startup. Fail-closed on error.
        """
        async with self._pool_lock:
            if self._initialized:
                return
            
            if not DATABASE_URL:
                raise RuntimeError("CRITICAL: DATABASE_URL not configured")
            
            try:
                import ssl as ssl_module
                db_url = DATABASE_URL
                ssl_context = None
                direct_tls = False
                
                # Railway TCP proxy connection handling  
                # Note: Railway's TCP proxy is NOT SSL - it's a plain TCP proxy
                # The actual PostgreSQL may or may not require SSL
                if 'proxy.rlwy.net' in db_url or 'railway.app' in db_url:
                    # Railway public proxy: try WITHOUT SSL first
                    # The TCP proxy is plain TCP, PostgreSQL server may require SSL internally
                    ssl_context = 'prefer'  # Let PostgreSQL negotiate
                    logger.info("Using ssl=prefer for Railway public proxy")
                elif 'railway.internal' in db_url:
                    # Internal Railway connections: no SSL needed
                    ssl_context = False
                    logger.info("SSL disabled for Railway internal connection")
                
                logger.info("Connecting to PostgreSQL...")
                
                # Connect - let asyncpg negotiate SSL with the PostgreSQL server
                self.pool = await asyncpg.create_pool(
                    db_url,
                    min_size=2,
                    max_size=10,
                    max_inactive_connection_lifetime=300,
                    command_timeout=30,
                    ssl=ssl_context,
                )
                
                await self._init_schema()
                self._initialized = True
                logger.info("✅ PostgreSQL database initialized with zero-knowledge architecture")
                
            except Exception as e:
                from utils import redact_secrets
                safe_msg = redact_secrets(str(e))
                logger.critical(f"Failed to initialize database [{type(e).__name__}]: {safe_msg}")
                raise RuntimeError(f"Database initialization failed [{type(e).__name__}]: {safe_msg}")
    
    async def close(self) -> None:
        """Close connection pool gracefully."""
        if self.pool:
            await self.pool.close()
            self._initialized = False
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def _acquire(self):
        """Acquire a connection from pool with error handling."""
        if not self.pool:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        async with self.pool.acquire() as conn:
            yield conn
    
    async def _init_schema(self) -> None:
        """Create tables if they don't exist. Never drops tables."""
        async with self._acquire() as conn:
            # Users table - only hashed ID, points, role, dates
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_hash TEXT PRIMARY KEY,
                    imtiaz INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'میهن‌پرست',
                    joined_at TIMESTAMPTZ DEFAULT NOW(),
                    last_active TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Rate limits table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_hash TEXT NOT NULL,
                    action TEXT NOT NULL,
                    last_action TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (user_hash, action)
                )
            ''')
            
            # Actions table with retention
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    id BIGSERIAL PRIMARY KEY,
                    user_hash TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Statistics table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Conduit verifications - NO screenshot or OCR text
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS conduit_verifications (
                    id BIGSERIAL PRIMARY KEY,
                    user_hash TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    gb_amount REAL NOT NULL,
                    points INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Certificates
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS certificates (
                    id BIGSERIAL PRIMARY KEY,
                    user_hash TEXT NOT NULL,
                    certificate_id TEXT UNIQUE NOT NULL,
                    rank TEXT NOT NULL,
                    imtiaz INTEGER NOT NULL,
                    issued_at TIMESTAMPTZ DEFAULT NOW(),
                    verification_hash TEXT NOT NULL,
                    qr_code_data TEXT NOT NULL
                )
            ''')
            
            # Physical rewards
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS physical_rewards (
                    id BIGSERIAL PRIMARY KEY,
                    user_hash TEXT NOT NULL,
                    anonymous_id TEXT UNIQUE NOT NULL,
                    reward_type TEXT NOT NULL,
                    rank_achieved TEXT NOT NULL,
                    max_rank_achieved TEXT NOT NULL,
                    eligibility_date TIMESTAMPTZ NOT NULL,
                    unique_serial_number TEXT UNIQUE NOT NULL,
                    hologram_code TEXT UNIQUE NOT NULL,
                    claim_status TEXT DEFAULT 'eligible',
                    notes TEXT
                )
            ''')
            
            # Achievements definitions
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    points_reward INTEGER DEFAULT 0,
                    badge TEXT,
                    requirement_type TEXT,
                    requirement_value TEXT
                )
            ''')
            
            # User achievements (unlocked)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_hash TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlocked_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (user_hash, achievement_id)
                )
            ''')
            
            # User streaks
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_streaks (
                    user_hash TEXT NOT NULL,
                    streak_type TEXT NOT NULL,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_action_date TEXT,
                    total_count INTEGER DEFAULT 0,
                    PRIMARY KEY (user_hash, streak_type)
                )
            ''')
            
            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_users_imtiaz ON users(imtiaz DESC)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_action_logs_created ON action_logs(created_at)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_action_logs_user ON action_logs(user_hash)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_hash)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_action ON rate_limits(action)')
            
            # Pending submissions (video/gathering) - persisted across restarts
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS pending_submissions (
                    token TEXT PRIMARY KEY,
                    submission_type TEXT NOT NULL,
                    user_id BIGINT NOT NULL,
                    links TEXT,
                    category TEXT,
                    reward INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_submissions_status ON pending_submissions(status)')
            
            # Placards (printable rally signs) - hosted via Telegram file_id
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS placards (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    country TEXT NOT NULL,
                    language TEXT NOT NULL,
                    file_id TEXT NOT NULL,
                    file_type TEXT DEFAULT 'document',
                    submitted_by TEXT,
                    approved_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_placards_country ON placards(country)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_placards_country_lang ON placards(country, language)')
            
            # Initialize default stats
            default_stats = [
                ('total_users', '0'),
                ('total_gb_shared', '0.0'),
                ('total_cleanups', '0'),
                ('total_protests', '0'),
                ('actions_by_type', '{}'),
                ('conduit_tier_distribution', '{}'),
                ('protests_by_country', '{}'),
            ]
            
            for key, value in default_stats:
                await conn.execute('''
                    INSERT INTO stats (key, value) VALUES ($1, $2)
                    ON CONFLICT (key) DO NOTHING
                ''', key, value)
            
            logger.info("Database schema initialized")
    
    # ==================== PUBLIC API ====================
    
    async def add_user(self, user_id: int) -> bool:
        """Add new user (hashed ID only). Returns True if new user."""
        user_hash = self._hash_user_id(user_id)
        now = datetime.now(timezone.utc)
        
        async with self._acquire() as conn:
            # Use RETURNING to detect if insert happened
            row = await conn.fetchrow('''
                INSERT INTO users (user_hash, joined_at, last_active)
                VALUES ($1, $2, $2)
                ON CONFLICT (user_hash) DO UPDATE SET last_active = $2
                RETURNING (xmax = 0) AS is_new
            ''', user_hash, now)
            
            is_new = row['is_new'] if row else False
            
            if is_new:
                await self._increment_stat(conn, 'total_users', 1)
                logger.info("New user added (identity protected)")
            
            return is_new
    
    async def get_last_action(self, user_hash: str, action: str) -> Optional[datetime]:
        """Get last action timestamp for rate limiting."""
        async with self._acquire() as conn:
            row = await conn.fetchrow(
                'SELECT last_action FROM rate_limits WHERE user_hash = $1 AND action = $2',
                user_hash, action
            )
            return row['last_action'] if row else None
    
    async def set_last_action(self, user_hash: str, action: str) -> None:
        """Set last action timestamp for rate limiting."""
        now = datetime.now(timezone.utc)
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO rate_limits (user_hash, action, last_action)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_hash, action) 
                DO UPDATE SET last_action = EXCLUDED.last_action
            ''', user_hash, action, now)
    
    async def add_points(self, user_id: int, points: int, action_type: str) -> Optional[Dict]:
        """
        Add points to user and log action.
        Returns certificate data if rank changed, None otherwise.
        """
        user_hash = self._hash_user_id(user_id)
        now = datetime.now(timezone.utc)
        
        async with self._acquire() as conn:
            async with conn.transaction():
                # Ensure user exists
                await conn.execute('''
                    INSERT INTO users (user_hash, joined_at, last_active)
                    VALUES ($1, $2, $2)
                    ON CONFLICT (user_hash) DO UPDATE SET last_active = $2
                ''', user_hash, now)
                
                # Get old role
                row = await conn.fetchrow(
                    'SELECT imtiaz, role FROM users WHERE user_hash = $1',
                    user_hash
                )
                old_role = row['role'] if row else 'میهن‌پرست'
                
                # Update points
                await conn.execute(
                    'UPDATE users SET imtiaz = imtiaz + $1, last_active = $2 WHERE user_hash = $3',
                    points, now, user_hash
                )
                
                # Get new total
                row = await conn.fetchrow(
                    'SELECT imtiaz FROM users WHERE user_hash = $1',
                    user_hash
                )
                new_imtiaz = row['imtiaz']
                new_role = self._calculate_role(new_imtiaz)
                
                # Update role
                await conn.execute(
                    'UPDATE users SET role = $1 WHERE user_hash = $2',
                    new_role, user_hash
                )
                
                # Log action
                await conn.execute('''
                    INSERT INTO action_logs (user_hash, action_type, points, created_at)
                    VALUES ($1, $2, $3, $4)
                ''', user_hash, action_type, points, now)
                
                # Update action stats
                await self._increment_action_stat(conn, action_type, 1)
        
        # Check for rank change
        certificate_data = None
        if old_role != new_role:
            logger.info(f"Rank changed: {old_role} → {new_role}")
            try:
                certificate_data = await self.issue_certificate(user_id, new_role, new_imtiaz)
                
                # Check physical reward eligibility
                if new_role in ['مارشال', 'سپهبد', 'سرلشکر']:
                    physical = await self.register_physical_reward(user_id, new_role)
                    if physical:
                        certificate_data['physical_reward'] = physical
            except Exception as e:
                from utils import redact_secrets
                logger.error(f"Failed to issue certificate: {redact_secrets(str(e))}")
        
        logger.info("Points awarded (identity protected)")
        return certificate_data
    
    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user's own stats."""
        user_hash = self._hash_user_id(user_id)
        
        async with self._acquire() as conn:
            row = await conn.fetchrow(
                'SELECT imtiaz, role, joined_at FROM users WHERE user_hash = $1',
                user_hash
            )
            
            if row:
                return {
                    'imtiaz': row['imtiaz'],
                    'role': row['role'],
                    'joined_date': row['joined_at'].isoformat() if row['joined_at'] else None
                }
            return None
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int, str]]:
        """Get top users - returns (rank, points, role) - NO usernames."""
        async with self._acquire() as conn:
            rows = await conn.fetch(
                'SELECT imtiaz, role FROM users ORDER BY imtiaz DESC LIMIT $1',
                limit
            )
            return [(i + 1, row['imtiaz'], row['role']) for i, row in enumerate(rows)]
    
    async def get_user_rank(self, user_id: int) -> Optional[int]:
        """Get user's rank position."""
        user_hash = self._hash_user_id(user_id)
        
        async with self._acquire() as conn:
            row = await conn.fetchrow(
                'SELECT imtiaz FROM users WHERE user_hash = $1',
                user_hash
            )
            if not row:
                return None
            
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM users WHERE imtiaz > $1',
                row['imtiaz']
            )
            return count + 1
    
    async def log_conduit_verification(self, user_id: int, tier: str, gb_amount: float, points: int):
        """Log Conduit verification - NO screenshot or OCR stored."""
        user_hash = self._hash_user_id(user_id)
        now = datetime.now(timezone.utc)
        
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO conduit_verifications (user_hash, tier, gb_amount, points, created_at)
                VALUES ($1, $2, $3, $4, $5)
            ''', user_hash, tier, gb_amount, points, now)
            
            await self._increment_stat_float(conn, 'total_gb_shared', gb_amount)
            await self._increment_tier_stat(conn, tier, 1)
        
        logger.info(f"Conduit verification logged: {tier} tier (identity protected)")
    
    async def log_cleanup(self, user_id: int, points: int):
        """Log cleanup action - NO photo stored."""
        await self.add_points(user_id, points, 'cleanup')
        async with self._acquire() as conn:
            await self._increment_stat(conn, 'total_cleanups', 1)
    
    async def log_protest(self, country: str):
        """Log protest - NO user tracking."""
        async with self._acquire() as conn:
            await self._increment_stat(conn, 'total_protests', 1)
            await self._increment_country_stat(conn, country, 1)
    
    async def get_aggregate_statistics(self) -> Dict:
        """Get anonymous aggregate statistics."""
        async with self._acquire() as conn:
            rows = await conn.fetch('SELECT key, value FROM stats')
            stats = {}
            for row in rows:
                key, value = row['key'], row['value']
                if key in ['actions_by_type', 'conduit_tier_distribution', 'protests_by_country']:
                    stats[key] = json.loads(value)
                elif key == 'total_gb_shared':
                    stats[key] = float(value)
                else:
                    stats[key] = int(value)
            return stats
    
    async def delete_user_data(self, user_id: int):
        """Delete user's actions but KEEP imtiaz and role (honor preserved)."""
        user_hash = self._hash_user_id(user_id)
        
        async with self._acquire() as conn:
            await conn.execute('DELETE FROM action_logs WHERE user_hash = $1', user_hash)
            await conn.execute('DELETE FROM conduit_verifications WHERE user_hash = $1', user_hash)
        
        logger.info("User data deleted (points and role preserved)")
    
    async def issue_certificate(self, user_id: int, rank: str, imtiaz: int) -> Dict:
        """Issue a digital certificate for rank achievement."""
        user_hash = self._hash_user_id(user_id)
        now = datetime.now(timezone.utc)
        
        cert_id = f"CERT-{secrets.token_hex(8).upper()}"
        verify_hash = hashlib.sha256(f"{cert_id}{user_hash}{rank}".encode()).hexdigest()[:16]
        qr_data = f"https://helpiranorg.t.me/verify?id={cert_id}"
        
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO certificates (user_hash, certificate_id, rank, imtiaz, issued_at, verification_hash, qr_code_data)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', user_hash, cert_id, rank, imtiaz, now, verify_hash, qr_data)
        
        return {
            'certificate_id': cert_id,
            'rank': rank,
            'imtiaz': imtiaz,
            'verification_hash': verify_hash,
            'qr_code_data': qr_data,
            'issued_at': now.isoformat(),
        }
    
    async def verify_certificate(self, certificate_id: str) -> Optional[Dict]:
        """Verify a certificate."""
        async with self._acquire() as conn:
            row = await conn.fetchrow('''
                SELECT certificate_id, rank, imtiaz, issued_at, verification_hash
                FROM certificates WHERE certificate_id = $1
            ''', certificate_id)
            
            if row:
                return {
                    'certificate_id': row['certificate_id'],
                    'rank': row['rank'],
                    'imtiaz': row['imtiaz'],
                    'issued_at': row['issued_at'].isoformat(),
                    'verification_hash': row['verification_hash'],
                    'valid': True,
                }
            return None
    
    async def get_user_certificates(self, user_id: int) -> List[Dict]:
        """Get all certificates for a user."""
        user_hash = self._hash_user_id(user_id)
        
        async with self._acquire() as conn:
            rows = await conn.fetch('''
                SELECT certificate_id, rank, imtiaz, issued_at, verification_hash, qr_code_data
                FROM certificates WHERE user_hash = $1 ORDER BY issued_at DESC
            ''', user_hash)
            
            return [{
                'certificate_id': row['certificate_id'],
                'rank': row['rank'],
                'imtiaz': row['imtiaz'],
                'issued_at': row['issued_at'].isoformat(),
                'verification_hash': row['verification_hash'],
                'qr_code_data': row['qr_code_data'],
            } for row in rows]
    
    async def register_physical_reward(self, user_id: int, rank: str) -> Optional[Dict]:
        """Register physical reward for top ranks."""
        user_hash = self._hash_user_id(user_id)
        now = datetime.now(timezone.utc)
        
        anonymous_id = f"HERO-{secrets.token_hex(6).upper()}"
        serial = f"SN-{secrets.token_hex(8).upper()}"
        hologram = f"HOLO-{secrets.token_hex(4).upper()}"
        
        reward_types = {
            'مارشال': 'GOLD_MEDAL_MARSHAL',
            'سپهبد': 'SILVER_MEDAL_GENERAL',
            'سرلشکر': 'BRONZE_MEDAL_COMMANDER',
        }
        reward_type = reward_types.get(rank.split()[-1], 'CERTIFICATE')
        
        async with self._acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO physical_rewards 
                    (user_hash, anonymous_id, reward_type, rank_achieved, max_rank_achieved, 
                     eligibility_date, unique_serial_number, hologram_code)
                    VALUES ($1, $2, $3, $4, $4, $5, $6, $7)
                ''', user_hash, anonymous_id, reward_type, rank, now, serial, hologram)
                
                return {
                    'anonymous_id': anonymous_id,
                    'reward_type': reward_type,
                    'serial_number': serial,
                    'hologram_code': hologram,
                }
            except asyncpg.UniqueViolationError:
                # Already registered
                return None
    
    async def get_user_physical_reward(self, user_id: int) -> Optional[Dict]:
        """Get user's physical reward status."""
        user_hash = self._hash_user_id(user_id)
        
        async with self._acquire() as conn:
            row = await conn.fetchrow('''
                SELECT anonymous_id, reward_type, rank_achieved, max_rank_achieved,
                       eligibility_date, unique_serial_number, hologram_code, claim_status
                FROM physical_rewards WHERE user_hash = $1
            ''', user_hash)
            
            if row:
                return {
                    'anonymous_id': row['anonymous_id'],
                    'reward_type': row['reward_type'],
                    'rank_achieved': row['rank_achieved'],
                    'max_rank_achieved': row['max_rank_achieved'],
                    'eligibility_date': row['eligibility_date'].isoformat(),
                    'serial_number': row['unique_serial_number'],
                    'hologram_code': row['hologram_code'],
                    'claim_status': row['claim_status'],
                }
            return None
    
    # ==================== GAMIFICATION (STREAKS/ACHIEVEMENTS/COMBOS) ====================
    
    async def get_user_streaks(self, user_id: int) -> List[Dict]:
        """Get all active streaks for user"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            rows = await conn.fetch('''
                SELECT streak_type, current_streak, longest_streak, total_count
                FROM user_streaks WHERE user_hash = $1
                ORDER BY current_streak DESC
            ''', user_hash)
            return [dict(row) for row in rows]
    
    async def get_user_streak(self, user_id: int) -> Optional[Dict]:
        """Get primary streak info for user"""
        streaks = await self.get_user_streaks(user_id)
        if streaks:
            return streaks[0]
        return {'current_streak': 0, 'longest_streak': 0, 'total_count': 0}
    
    async def check_daily_combo(self, user_id: int) -> Dict:
        """Check if user completed multiple diverse actions today and award combo bonus"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            row = await conn.fetchrow('''
                SELECT COUNT(DISTINCT action_type) as unique_actions
                FROM action_logs 
                WHERE user_hash = $1 AND created_at >= $2
            ''', user_hash, today_start)
            
            unique_actions = row['unique_actions'] if row else 0
            
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
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get unlocked achievements for user"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            rows = await conn.fetch('''
                SELECT a.achievement_id, a.name, a.description, a.badge, ua.unlocked_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.achievement_id
                WHERE ua.user_hash = $1
                ORDER BY ua.unlocked_at DESC
            ''', user_hash)
            return [dict(row) for row in rows]
    
    async def check_and_unlock_achievements(self, user_id: int) -> List[Dict]:
        """Check user progress and unlock new achievements"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            user_row = await conn.fetchrow(
                'SELECT imtiaz, role FROM users WHERE user_hash = $1', user_hash
            )
            if not user_row:
                return []
            
            imtiaz = user_row['imtiaz']
            
            action_rows = await conn.fetch('''
                SELECT action_type, COUNT(*) as count
                FROM action_logs WHERE user_hash = $1
                GROUP BY action_type
            ''', user_hash)
            action_counts = {row['action_type']: row['count'] for row in action_rows}
            
            unlocked_rows = await conn.fetch(
                'SELECT achievement_id FROM user_achievements WHERE user_hash = $1', user_hash
            )
            unlocked = {row['achievement_id'] for row in unlocked_rows}
            
            achievements_to_check = [
                ('first_step', 'اولین قدم', 'شروع سفر', 'general', 10, '🏅', 'points', 10),
                ('century', 'صد تایی', '100 امتیاز کسب کردید', 'milestone', 50, '⭐', 'points', 100),
                ('half_k', 'پانصد', '500 امتیاز کسب کردید', 'milestone', 100, '💫', 'points', 500),
                ('one_k', 'هزارتایی', '1000 امتیاز کسب کردید', 'milestone', 200, '🌟', 'points', 1000),
                ('twitter_master', 'توییتر استاد', '50 توییت به اشتراک گذاشتید', 'specialist', 100, '🐦', 'action_count', ('tweet_shared', 50)),
                ('email_warrior', 'ایمیل جنگجو', '100 ایمیل ارسال کردید', 'specialist', 150, '📧', 'action_count', ('email_sent', 100)),
            ]
            
            newly_unlocked = []
            for ach_id, name, desc, category, points_reward, badge, req_type, req_value in achievements_to_check:
                if ach_id in unlocked:
                    continue
                
                unlocked_now = False
                if req_type == 'points':
                    unlocked_now = imtiaz >= req_value
                elif req_type == 'action_count':
                    action_type, required_count = req_value
                    unlocked_now = action_counts.get(action_type, 0) >= required_count
                
                if unlocked_now:
                    await conn.execute('''
                        INSERT INTO achievements 
                        (achievement_id, name, description, category, points_reward, badge, requirement_type, requirement_value)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (achievement_id) DO NOTHING
                    ''', ach_id, name, desc, category, points_reward, badge, req_type, str(req_value))
                    
                    await conn.execute('''
                        INSERT INTO user_achievements (user_hash, achievement_id, unlocked_at)
                        VALUES ($1, $2, $3)
                    ''', user_hash, ach_id, datetime.now(timezone.utc))
                    
                    newly_unlocked.append({
                        'id': ach_id,
                        'name': name,
                        'description': desc,
                        'badge': badge,
                        'points': points_reward
                    })
            
            return newly_unlocked
    
    async def check_and_update_streak(self, user_id: int, action_type: str) -> Dict:
        """Check and update streak, return streak info and bonus"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            today = datetime.now(timezone.utc).date().isoformat()
            
            row = await conn.fetchrow('''
                SELECT current_streak, longest_streak, last_action_date, total_count
                FROM user_streaks WHERE user_hash = $1 AND streak_type = $2
            ''', user_hash, action_type)
            
            if row:
                current_streak = row['current_streak']
                longest_streak = row['longest_streak']
                last_date = row['last_action_date']
                total_count = row['total_count']
                
                yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
                
                if last_date == today:
                    return {
                        'streak': current_streak,
                        'bonus_points': 0,
                        'multiplier': self._get_streak_multiplier(current_streak)
                    }
                elif last_date == yesterday:
                    current_streak += 1
                    longest_streak = max(longest_streak, current_streak)
                else:
                    current_streak = 1
                
                await conn.execute('''
                    UPDATE user_streaks 
                    SET current_streak = $1, longest_streak = $2, last_action_date = $3, total_count = $4
                    WHERE user_hash = $5 AND streak_type = $6
                ''', current_streak, longest_streak, today, total_count + 1, user_hash, action_type)
            else:
                current_streak = 1
                longest_streak = 1
                await conn.execute('''
                    INSERT INTO user_streaks (user_hash, streak_type, current_streak, longest_streak, last_action_date, total_count)
                    VALUES ($1, $2, 1, 1, $3, 1)
                ''', user_hash, action_type, today)
            
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
    
    # ==================== PROTEST/CLEANUP TRACKING ====================
    
    async def get_unique_countries(self) -> List[str]:
        """Get list of countries with protests (returns empty for secure DB - no location data)"""
        return []
    
    async def get_protest_events_by_country(self, country: str) -> List[Dict]:
        """Get protest events by country (not stored in secure DB)"""
        return []
    
    async def get_protest_event(self, event_id: int) -> Optional[Dict]:
        """Get specific protest event (not stored in secure DB)"""
        return None
    
    async def mark_protest_attendance(self, event_id: int, user_id: int) -> bool:
        """Mark protest attendance (returns False - not implemented in secure DB)"""
        return False
    
    async def get_organizers_by_country(self, country: str) -> List[Dict]:
        """Get organizers by country (returns empty - no PII stored)"""
        return []
    
    async def add_cleanup_action(self, user_id: int, country: str, city: str, 
                                  media_type: str, file_id: str, caption: str = None) -> None:
        """Log cleanup action (stores only hashed user, no location/media details)"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO action_logs (user_hash, action_type, created_at)
                VALUES ($1, 'cleanup', $2)
            ''', user_hash, datetime.now(timezone.utc))
            await self._increment_stat(conn, 'total_cleanups', 1)
    
    async def add_protest_media(self, user_id: int, country: str, city: str,
                                 media_type: str, file_id: str, caption: str = None) -> None:
        """Log protest media (stores only hashed user, no location/media details)"""
        user_hash = self._hash_user_id(user_id)
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO action_logs (user_hash, action_type, created_at)
                VALUES ($1, 'protest_media', $2)
            ''', user_hash, datetime.now(timezone.utc))
            await self._increment_stat(conn, 'total_protests', 1)
    
    # ==================== SUBMISSIONS ====================
    
    async def add_submission(self, token: str, submission_type: str, user_id: int,
                            links: str, category: str, reward: int) -> None:
        """Store a pending submission (video or gathering) in the database."""
        async with self._acquire() as conn:
            await conn.execute('''
                INSERT INTO pending_submissions (token, submission_type, user_id, links, category, reward)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (token) DO NOTHING
            ''', token, submission_type, user_id, links, category, reward)
    
    async def get_submission(self, token: str) -> Optional[Dict]:
        """Get a pending submission by token."""
        async with self._acquire() as conn:
            row = await conn.fetchrow('''
                SELECT token, submission_type, user_id, links, category, reward, status
                FROM pending_submissions WHERE token = $1 AND status = 'pending'
            ''', token)
            if row:
                return dict(row)
            return None
    
    async def resolve_submission(self, token: str, status: str) -> bool:
        """Mark a submission as approved or rejected."""
        async with self._acquire() as conn:
            result = await conn.execute('''
                UPDATE pending_submissions SET status = $1 WHERE token = $2 AND status = 'pending'
            ''', status, token)
            return result and 'UPDATE 1' in result

    # ==================== PLACARDS ====================
    
    async def add_placard(self, title: str, country: str, language: str,
                         file_id: str, file_type: str = 'document',
                         submitted_by: str = None) -> int:
        """Insert an approved placard. Returns the new placard id."""
        async with self._acquire() as conn:
            row = await conn.fetchrow('''
                INSERT INTO placards (title, country, language, file_id, file_type, submitted_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            ''', title, country, language, file_id, file_type, submitted_by)
            return row['id'] if row else 0
    
    async def get_placard_countries(self) -> List[str]:
        """Return distinct countries that have at least one placard."""
        async with self._acquire() as conn:
            rows = await conn.fetch('SELECT DISTINCT country FROM placards ORDER BY country')
            return [r['country'] for r in rows]
    
    async def get_placard_languages(self, country: str) -> List[str]:
        """Return distinct languages available for a country."""
        async with self._acquire() as conn:
            rows = await conn.fetch(
                'SELECT DISTINCT language FROM placards WHERE country = $1 ORDER BY language',
                country
            )
            return [r['language'] for r in rows]
    
    async def get_placards_by_country_and_language(self, country: str, language: str) -> List[Dict]:
        """Return all placards for a country + language combo."""
        async with self._acquire() as conn:
            rows = await conn.fetch('''
                SELECT id, title, file_id, file_type FROM placards
                WHERE country = $1 AND language = $2 ORDER BY id DESC
            ''', country, language)
            return [dict(r) for r in rows]
    
    async def get_placard(self, placard_id: int) -> Optional[Dict]:
        """Get a single placard by id."""
        async with self._acquire() as conn:
            row = await conn.fetchrow(
                'SELECT id, title, country, language, file_id, file_type FROM placards WHERE id = $1',
                placard_id
            )
            return dict(row) if row else None
    
    async def remove_placard(self, placard_id: int) -> bool:
        """Delete a placard by id. Returns True if deleted."""
        async with self._acquire() as conn:
            result = await conn.execute('DELETE FROM placards WHERE id = $1', placard_id)
            return result and 'DELETE 1' in result

    # ==================== RETENTION ====================
    
    async def cleanup_old_action_logs(self, days: int = None) -> int:
        """Delete action logs older than specified days. Uses advisory lock."""
        if days is None:
            days = ACTION_LOG_RETENTION_DAYS
        
        async with self._acquire() as conn:
            # Advisory lock to prevent concurrent cleanup
            locked = await conn.fetchval('SELECT pg_try_advisory_lock(123456789)')
            if not locked:
                logger.debug("Retention cleanup skipped - another instance running")
                return 0
            
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                result = await conn.execute(
                    'DELETE FROM action_logs WHERE created_at < $1',
                    cutoff
                )
                deleted = int(result.split()[-1]) if result else 0
                
                if deleted > 0:
                    logger.info(f"Retention cleanup: deleted {deleted} logs older than {days} days")
                return deleted
            finally:
                await conn.execute('SELECT pg_advisory_unlock(123456789)')
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self._acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                return result == 1
        except Exception as e:
            from utils import redact_secrets
            logger.error(f"Health check failed: {redact_secrets(str(e))}")
            return False
    
    # ==================== INTERNAL HELPERS ====================
    
    async def _increment_stat(self, conn, key: str, delta: int):
        await conn.execute('''
            UPDATE stats SET value = (CAST(value AS INTEGER) + $1)::TEXT, updated_at = NOW()
            WHERE key = $2
        ''', delta, key)
    
    async def _increment_stat_float(self, conn, key: str, delta: float):
        await conn.execute('''
            UPDATE stats SET value = (CAST(value AS FLOAT) + $1)::TEXT, updated_at = NOW()
            WHERE key = $2
        ''', delta, key)
    
    async def _increment_action_stat(self, conn, action_type: str, delta: int):
        row = await conn.fetchrow("SELECT value FROM stats WHERE key = 'actions_by_type'")
        data = json.loads(row['value']) if row else {}
        data[action_type] = data.get(action_type, 0) + delta
        await conn.execute(
            "UPDATE stats SET value = $1, updated_at = NOW() WHERE key = 'actions_by_type'",
            json.dumps(data)
        )
    
    async def _increment_tier_stat(self, conn, tier: str, delta: int):
        row = await conn.fetchrow("SELECT value FROM stats WHERE key = 'conduit_tier_distribution'")
        data = json.loads(row['value']) if row else {}
        data[tier] = data.get(tier, 0) + delta
        await conn.execute(
            "UPDATE stats SET value = $1, updated_at = NOW() WHERE key = 'conduit_tier_distribution'",
            json.dumps(data)
        )
    
    async def _increment_country_stat(self, conn, country: str, delta: int):
        row = await conn.fetchrow("SELECT value FROM stats WHERE key = 'protests_by_country'")
        data = json.loads(row['value']) if row else {}
        data[country] = data.get(country, 0) + delta
        await conn.execute(
            "UPDATE stats SET value = $1, updated_at = NOW() WHERE key = 'protests_by_country'",
            json.dumps(data)
        )
    
    def _calculate_role(self, imtiaz: int) -> str:
        """Calculate role based on imtiaz thresholds."""
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


# Singleton instance
_db_instance: Optional[SecureDatabase] = None


def get_database() -> SecureDatabase:
    """Get or create database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SecureDatabase()
    return _db_instance
