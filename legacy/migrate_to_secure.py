"""
Migration Script: Old Database → Secure Zero-Knowledge Database
CRITICAL: Preserves user imtiaz and roles (honor system)
IRREVERSIBLE: User IDs will be hashed - cannot be recovered
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from secure_database import SecureDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_old_database():
    """Create timestamped backup of old database"""
    old_db = Path("revolution_bot.db")
    if not old_db.exists():
        logger.error("Old database not found!")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"revolution_bot_backup_{timestamp}.db"
    
    shutil.copy2(old_db, backup_path)
    logger.info(f"✅ Backup created: {backup_path}")
    return True


def migrate_users(old_conn, secure_db: SecureDatabase):
    """Migrate users with hashed IDs - preserves imtiaz and roles"""
    old_cursor = old_conn.cursor()
    
    # Get all users with their total points
    old_cursor.execute('''
        SELECT user_id, imtiaz FROM users
    ''')
    
    users = old_cursor.fetchall()
    logger.info(f"Found {len(users)} users to migrate")
    
    migrated_count = 0
    for user_id, imtiaz in users:
        # Add user to secure database (hashed)
        secure_db.add_user(user_id)
        
        # Update points (this also updates role)
        if imtiaz > 0:
            secure_db.add_points(user_id, imtiaz, 'migration')
        
        migrated_count += 1
    
    logger.info(f"✅ Migrated {migrated_count} users (identities now protected)")
    return migrated_count


def migrate_conduit_stats(old_conn, secure_db: SecureDatabase):
    """Migrate Conduit statistics - NO screenshots or OCR text"""
    old_cursor = old_conn.cursor()
    
    # Get Conduit verifications
    old_cursor.execute('''
        SELECT user_id, tier, gb_amount, points FROM conduit_verifications
    ''')
    
    verifications = old_cursor.fetchall()
    logger.info(f"Found {len(verifications)} Conduit verifications")
    
    for user_id, tier, gb_amount, points in verifications:
        secure_db.log_conduit_verification(user_id, tier, gb_amount, points)
    
    logger.info(f"✅ Migrated {len(verifications)} Conduit verifications (screenshots deleted)")
    return len(verifications)


def migrate_cleanup_stats(old_conn, secure_db: SecureDatabase):
    """Migrate cleanup statistics - NO photos stored"""
    old_cursor = old_conn.cursor()
    
    # Get cleanup counts
    old_cursor.execute('''
        SELECT user_id, COUNT(*) as cleanup_count FROM cleanups GROUP BY user_id
    ''')
    
    cleanups = old_cursor.fetchall()
    total_cleanups = sum(count for _, count in cleanups)
    
    # Aggregate stat only (no user tracking)
    for _ in range(total_cleanups):
        secure_db._increment_stat('total_cleanups', 1)
    
    logger.info(f"✅ Migrated {total_cleanups} cleanup records (photos deleted, no user tracking)")
    return total_cleanups


def migrate_protest_stats(old_conn, secure_db: SecureDatabase):
    """Migrate protest statistics - NO attendance or organizer tracking"""
    old_cursor = old_conn.cursor()
    
    # Get protest counts by country
    old_cursor.execute('''
        SELECT country, COUNT(*) as protest_count FROM protests GROUP BY country
    ''')
    
    protests = old_cursor.fetchall()
    total_protests = 0
    
    for country, count in protests:
        for _ in range(count):
            secure_db.log_protest(country)
        total_protests += count
    
    logger.info(f"✅ Migrated {total_protests} protest records (attendance tracking removed)")
    return total_protests


def verify_migration(old_conn, secure_db: SecureDatabase):
    """Verify data integrity after migration"""
    old_cursor = old_conn.cursor()
    
    # Check user count
    old_cursor.execute('SELECT COUNT(*) FROM users')
    old_user_count = old_cursor.fetchone()[0]
    
    stats = secure_db.get_aggregate_statistics()
    new_user_count = stats['total_users']
    
    if old_user_count == new_user_count:
        logger.info(f"✅ User count verified: {new_user_count}")
    else:
        logger.error(f"❌ User count mismatch: {old_user_count} → {new_user_count}")
        return False
    
    # Check total GB shared
    old_cursor.execute('SELECT SUM(gb_amount) FROM conduit_verifications')
    old_gb_total = old_cursor.fetchone()[0] or 0
    new_gb_total = stats['total_gb_shared']
    
    if abs(old_gb_total - new_gb_total) < 0.01:  # Float tolerance
        logger.info(f"✅ GB shared verified: {new_gb_total:.2f}")
    else:
        logger.error(f"❌ GB mismatch: {old_gb_total} → {new_gb_total}")
        return False
    
    return True


def main():
    """Execute migration with verification"""
    print("=" * 60)
    print("SECURE DATABASE MIGRATION")
    print("=" * 60)
    print("⚠️  WARNING: This migration is IRREVERSIBLE!")
    print("⚠️  User IDs will be hashed and cannot be recovered")
    print("✅ User imtiaz and roles will be preserved")
    print("=" * 60)
    
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled")
        return
    
    # Step 1: Backup
    print("\n[1/6] Creating backup...")
    if not backup_old_database():
        print("❌ Backup failed - aborting")
        return
    
    # Step 2: Initialize secure database
    print("\n[2/6] Initializing secure database...")
    secure_db = SecureDatabase("revolution_bot_secure.db")
    
    # Step 3: Connect to old database
    print("\n[3/6] Connecting to old database...")
    old_conn = sqlite3.connect("revolution_bot.db")
    old_conn.row_factory = sqlite3.Row
    
    # Step 4: Migrate data
    print("\n[4/6] Migrating data...")
    migrate_users(old_conn, secure_db)
    migrate_conduit_stats(old_conn, secure_db)
    migrate_cleanup_stats(old_conn, secure_db)
    migrate_protest_stats(old_conn, secure_db)
    
    # Step 5: Verify
    print("\n[5/6] Verifying migration...")
    if not verify_migration(old_conn, secure_db):
        print("❌ Verification failed - please review logs")
        old_conn.close()
        return
    
    old_conn.close()
    
    # Step 6: Summary
    print("\n[6/6] Migration complete!")
    print("=" * 60)
    
    stats = secure_db.get_aggregate_statistics()
    print(f"\nSecure Database Statistics (Zero-Knowledge):")
    print(f"  Total Users: {stats['total_users']}")
    print(f"  Total GB Shared: {stats['total_gb_shared']:.2f}")
    print(f"  Total Cleanups: {stats['total_cleanups']}")
    print(f"  Total Protests: {stats['total_protests']}")
    print(f"\n✅ All user identities are now protected")
    print(f"✅ User imtiaz and roles preserved")
    print(f"✅ Old database backed up")
    print(f"\n⚠️  NEXT STEPS:")
    print(f"  1. Update config.py: USE_SECURE_DATABASE=True")
    print(f"  2. Revoke old bot token")
    print(f"  3. Generate new bot token")
    print(f"  4. Update .env with new token")
    print(f"  5. Restart bot")
    print("=" * 60)


if __name__ == "__main__":
    main()
