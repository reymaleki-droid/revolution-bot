"""
Migrate existing databases to new gamification schema
Adds new tables for streaks, achievements, challenges, prestige
"""
import sqlite3
from pathlib import Path

def migrate_regular_db(db_path="revolution_bot.db"):
    """Migrate regular database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Migrating {db_path}...")
    
    # Add new tables
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_prestige (
            user_id INTEGER PRIMARY KEY,
            prestige_level INTEGER DEFAULT 0,
            total_lifetime_points INTEGER DEFAULT 0,
            prestige_history TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
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
    print(f"✅ {db_path} migrated successfully")

def migrate_secure_db(db_path="revolution_bot_secure.db"):
    """Migrate secure database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Migrating {db_path}...")
    
    # Add new tables for secure DB (using user_hash instead of user_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            user_hash TEXT,
            streak_type TEXT,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_action_date TEXT,
            total_count INTEGER DEFAULT 0,
            PRIMARY KEY (user_hash, streak_type),
            FOREIGN KEY (user_hash) REFERENCES users (user_hash)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            points_reward INTEGER DEFAULT 0,
            badge TEXT NOT NULL,
            requirement_type TEXT NOT NULL,
            requirement_value TEXT NOT NULL,
            is_secret BOOLEAN DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_hash TEXT,
            achievement_id TEXT,
            unlocked_at TEXT NOT NULL,
            PRIMARY KEY (user_hash, achievement_id),
            FOREIGN KEY (user_hash) REFERENCES users (user_hash),
            FOREIGN KEY (achievement_id) REFERENCES achievements (achievement_id)
        )
    """)
    
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_challenge_progress (
            user_hash TEXT,
            challenge_id INTEGER,
            progress INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_at TEXT,
            PRIMARY KEY (user_hash, challenge_id),
            FOREIGN KEY (user_hash) REFERENCES users (user_hash),
            FOREIGN KEY (challenge_id) REFERENCES weekly_challenges (challenge_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_prestige (
            user_hash TEXT PRIMARY KEY,
            prestige_level INTEGER DEFAULT 0,
            total_lifetime_points INTEGER DEFAULT 0,
            prestige_history TEXT,
            FOREIGN KEY (user_hash) REFERENCES users (user_hash)
        )
    """)
    
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
    print(f"✅ {db_path} migrated successfully")

if __name__ == "__main__":
    # Migrate both databases
    if Path("revolution_bot.db").exists():
        migrate_regular_db()
    else:
        print("⚠️  revolution_bot.db not found")
    
    if Path("revolution_bot_secure.db").exists():
        migrate_secure_db()
    else:
        print("⚠️  revolution_bot_secure.db not found")
    
    print("\n🎉 Migration complete! Run init_achievements.py next.")
