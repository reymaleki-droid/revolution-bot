#!/usr/bin/env python3
"""
Database verification script for release gates.
Exit code 0 = all checks pass, non-zero = failure.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone


async def verify_database():
    """Run all database verification checks."""
    checks_passed = 0
    checks_failed = 0
    
    print("=" * 60)
    print("DATABASE VERIFICATION - RELEASE GATES")
    print("=" * 60)
    
    # Import after path setup
    from config import DATABASE_URL, HASH_PEPPER, USER_HASH_SALT, ACTION_LOG_RETENTION_DAYS
    
    # Check 1: DATABASE_URL configured
    print("\n[1] Checking DATABASE_URL configuration...")
    if DATABASE_URL:
        masked = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL[:20]
        print(f"    ✅ DATABASE_URL configured: ...@{masked}")
        checks_passed += 1
    else:
        print("    ❌ DATABASE_URL not configured!")
        checks_failed += 1
        return checks_passed, checks_failed
    
    # Check 2: HASH_PEPPER configured
    print("\n[2] Checking HASH_PEPPER configuration...")
    if HASH_PEPPER and len(HASH_PEPPER) >= 32:
        print(f"    ✅ HASH_PEPPER configured ({len(HASH_PEPPER)} chars)")
        checks_passed += 1
    elif HASH_PEPPER:
        print(f"    ⚠️  HASH_PEPPER short ({len(HASH_PEPPER)} chars, recommend 64)")
        checks_passed += 1
    else:
        print("    ❌ HASH_PEPPER not configured!")
        checks_failed += 1
    
    # Check 3: USER_HASH_SALT configured
    print("\n[3] Checking USER_HASH_SALT configuration...")
    if USER_HASH_SALT:
        print(f"    ✅ USER_HASH_SALT configured ({len(USER_HASH_SALT)} hex chars)")
        checks_passed += 1
    else:
        print("    ⚠️  USER_HASH_SALT not set, using file-based salt")
        checks_passed += 1
    
    # Check 4: Database connection
    print("\n[4] Testing database connection...")
    try:
        from secure_database_pg import get_database
        db = get_database()
        await db.initialize()
        
        if await db.health_check():
            print("    ✅ Database connection successful")
            checks_passed += 1
        else:
            print("    ❌ Database health check failed")
            checks_failed += 1
            return checks_passed, checks_failed
    except Exception as e:
        print(f"    ❌ Database connection failed: {e}")
        checks_failed += 1
        return checks_passed, checks_failed
    
    # Check 5: Tables exist
    print("\n[5] Checking required tables...")
    required_tables = [
        'users', 'rate_limits', 'action_logs', 'stats', 
        'achievements', 'user_achievements', 'user_streaks',
        'certificates', 'conduit_verifications', 'physical_rewards'
    ]
    
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for table in required_tables:
            exists = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            ''', table)
            if exists:
                print(f"    ✅ Table '{table}' exists")
                checks_passed += 1
            else:
                print(f"    ❌ Table '{table}' missing!")
                checks_failed += 1
    finally:
        await conn.close()
    
    # Check 6: No PII columns
    print("\n[6] Checking for PII columns (should be NONE)...")
    pii_columns = ['user_id', 'username', 'first_name', 'last_name', 'phone', 'email', 'file_id', 'caption', 'message_text']
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        pii_found = []
        for col in pii_columns:
            found = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' AND column_name = $1
                )
            ''', col)
            if found:
                pii_found.append(col)
        
        if not pii_found:
            print("    ✅ No PII columns found")
            checks_passed += 1
        else:
            print(f"    ❌ PII columns found: {pii_found}")
            checks_failed += 1
    finally:
        await conn.close()
    
    # Check 7: Rate limiting persistence
    print("\n[7] Testing rate limit persistence...")
    try:
        test_hash = db.get_user_hash(999999999)
        await db.set_last_action(test_hash, 'verification_test')
        last = await db.get_last_action(test_hash, 'verification_test')
        
        if last:
            print(f"    ✅ Rate limit written and read: {last.isoformat()}")
            checks_passed += 1
            
            # Cleanup
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.execute(
                "DELETE FROM rate_limits WHERE user_hash = $1 AND action = 'verification_test'",
                test_hash
            )
            await conn.close()
        else:
            print("    ❌ Rate limit not persisted!")
            checks_failed += 1
    except Exception as e:
        print(f"    ❌ Rate limit test failed: {e}")
        checks_failed += 1
    
    # Check 8: Retention job
    print("\n[8] Testing retention cleanup job...")
    try:
        deleted = await db.cleanup_old_action_logs(days=36500)
        print(f"    ✅ Retention job executed (deleted {deleted} rows)")
        checks_passed += 1
    except Exception as e:
        print(f"    ❌ Retention job failed: {e}")
        checks_failed += 1
    
    # Check 9: Timestamp timezone
    print("\n[9] Checking UTC timestamp handling...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        now = await conn.fetchval("SELECT NOW()")
        await conn.close()
        
        if now.tzinfo is not None:
            print(f"    ✅ Timestamps are timezone-aware: {now.isoformat()}")
            checks_passed += 1
        else:
            print("    ❌ Timestamps are naive (no timezone)!")
            checks_failed += 1
    except Exception as e:
        print(f"    ❌ Timezone check failed: {e}")
        checks_failed += 1
    
    print(f"\n[10] Retention policy: {ACTION_LOG_RETENTION_DAYS} days")
    checks_passed += 1
    
    await db.close()
    
    return checks_passed, checks_failed


def main():
    passed, failed = asyncio.run(verify_database())
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n❌ VERIFICATION FAILED - DO NOT DEPLOY")
        sys.exit(1)
    else:
        print("\n✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        sys.exit(0)


if __name__ == '__main__':
    main()
