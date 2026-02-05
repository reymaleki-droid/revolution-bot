#!/usr/bin/env python3
"""
Smoke test for database operations.
Tests all critical DB methods without Telegram API calls.
Exit 0 = PASS, non-zero = FAIL
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def smoke_test():
    """Run all critical database smoke tests."""
    tests_passed = 0
    tests_failed = 0
    
    print("=" * 60)
    print("DATABASE SMOKE TEST - RUNTIME VALIDATION")
    print("=" * 60)
    
    # Use a fake user ID for testing
    FAKE_USER_ID = 999888777666
    
    try:
        from secure_database_pg import get_database
        db = get_database()
        
        # Test 1: Initialize database
        print("\n[1] Initialize database...")
        try:
            await db.initialize()
            print("    ✅ Database initialized")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ Initialize failed: {e}")
            tests_failed += 1
            return tests_passed, tests_failed
        
        # Test 2: Health check
        print("\n[2] Health check...")
        try:
            if await db.health_check():
                print("    ✅ Health check passed")
                tests_passed += 1
            else:
                print("    ❌ Health check returned False")
                tests_failed += 1
        except Exception as e:
            print(f"    ❌ Health check failed: {e}")
            tests_failed += 1
        
        # Test 3: Add user
        print("\n[3] Add user (fake ID)...")
        try:
            result = await db.add_user(FAKE_USER_ID)
            print(f"    ✅ add_user returned: {result}")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ add_user failed: {e}")
            tests_failed += 1
        
        # Test 4: Add points
        print("\n[4] Add points...")
        try:
            cert_data = await db.add_points(FAKE_USER_ID, 100, 'smoke_test')
            print(f"    ✅ add_points returned: {cert_data}")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ add_points failed: {e}")
            tests_failed += 1
        
        # Test 5: Get user stats
        print("\n[5] Get user stats...")
        try:
            stats = await db.get_user_stats(FAKE_USER_ID)
            print(f"    ✅ get_user_stats: imtiaz={stats.get('imtiaz')}, role={stats.get('role')}")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_user_stats failed: {e}")
            tests_failed += 1
        
        # Test 6: Get user rank
        print("\n[6] Get user rank...")
        try:
            rank = await db.get_user_rank(FAKE_USER_ID)
            print(f"    ✅ get_user_rank: #{rank}")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_user_rank failed: {e}")
            tests_failed += 1
        
        # Test 7: Rate limiting - set and get
        print("\n[7] Rate limiting (set/get)...")
        try:
            user_hash = db.get_user_hash(FAKE_USER_ID)
            await db.set_last_action(user_hash, 'smoke_test_action')
            last = await db.get_last_action(user_hash, 'smoke_test_action')
            if last:
                print(f"    ✅ Rate limit works: last_action={last.isoformat()}")
                tests_passed += 1
            else:
                print("    ❌ Rate limit not persisted")
                tests_failed += 1
        except Exception as e:
            print(f"    ❌ Rate limit failed: {e}")
            tests_failed += 1
        
        # Test 8: Get user hash (sync method)
        print("\n[8] Get user hash (sync)...")
        try:
            hash1 = db.get_user_hash(FAKE_USER_ID)
            hash2 = db.get_user_hash(FAKE_USER_ID)
            if hash1 == hash2 and len(hash1) == 64:
                print(f"    ✅ get_user_hash stable: {hash1[:16]}...")
                tests_passed += 1
            else:
                print(f"    ❌ Hash unstable or invalid: {hash1} vs {hash2}")
                tests_failed += 1
        except Exception as e:
            print(f"    ❌ get_user_hash failed: {e}")
            tests_failed += 1
        
        # Test 9: Get leaderboard
        print("\n[9] Get leaderboard...")
        try:
            leaders = await db.get_leaderboard(5)
            print(f"    ✅ get_leaderboard returned {len(leaders)} entries")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_leaderboard failed: {e}")
            tests_failed += 1
        
        # Test 10: Get user streaks
        print("\n[10] Get user streaks...")
        try:
            streaks = await db.get_user_streaks(FAKE_USER_ID)
            print(f"    ✅ get_user_streaks: {len(streaks)} streaks")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_user_streaks failed: {e}")
            tests_failed += 1
        
        # Test 11: Get user achievements
        print("\n[11] Get user achievements...")
        try:
            achievements = await db.get_user_achievements(FAKE_USER_ID)
            print(f"    ✅ get_user_achievements: {len(achievements)} achievements")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_user_achievements failed: {e}")
            tests_failed += 1
        
        # Test 12: Check daily combo
        print("\n[12] Check daily combo...")
        try:
            combo = await db.check_daily_combo(FAKE_USER_ID)
            print(f"    ✅ check_daily_combo: {combo['unique_actions']} unique actions")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ check_daily_combo failed: {e}")
            tests_failed += 1
        
        # Test 13: Get user certificates
        print("\n[13] Get user certificates...")
        try:
            certs = await db.get_user_certificates(FAKE_USER_ID)
            print(f"    ✅ get_user_certificates: {len(certs)} certificates")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_user_certificates failed: {e}")
            tests_failed += 1
        
        # Test 14: Aggregate statistics
        print("\n[14] Get aggregate statistics...")
        try:
            stats = await db.get_aggregate_statistics()
            print(f"    ✅ get_aggregate_statistics: {list(stats.keys())}")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ get_aggregate_statistics failed: {e}")
            tests_failed += 1
        
        # Test 15: Retention cleanup (should delete 0 with 36500 days)
        print("\n[15] Retention cleanup (far future)...")
        try:
            deleted = await db.cleanup_old_action_logs(days=36500)
            print(f"    ✅ cleanup_old_action_logs: deleted {deleted} (expected 0)")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ cleanup_old_action_logs failed: {e}")
            tests_failed += 1
        
        # Test 16: Log conduit verification
        print("\n[16] Log conduit verification...")
        try:
            await db.log_conduit_verification(FAKE_USER_ID, 'test_tier', 5.0, 50)
            print("    ✅ log_conduit_verification completed")
            tests_passed += 1
        except Exception as e:
            print(f"    ❌ log_conduit_verification failed: {e}")
            tests_failed += 1
        
        # Cleanup: Delete test data
        print("\n[CLEANUP] Removing test data...")
        try:
            from config import DATABASE_URL
            import asyncpg
            conn = await asyncpg.connect(DATABASE_URL)
            user_hash = db.get_user_hash(FAKE_USER_ID)
            
            await conn.execute("DELETE FROM action_logs WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM rate_limits WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM conduit_verifications WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM certificates WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM user_streaks WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM user_achievements WHERE user_hash = $1", user_hash)
            await conn.execute("DELETE FROM users WHERE user_hash = $1", user_hash)
            await conn.close()
            print("    ✅ Test data cleaned up")
        except Exception as e:
            print(f"    ⚠️  Cleanup warning: {e}")
        
        # Close connection pool
        await db.close()
        print("\n    ✅ Database connection closed")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    return tests_passed, tests_failed


def main():
    passed, failed = asyncio.run(smoke_test())
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n❌ SMOKE TEST FAILED - DO NOT DEPLOY")
        sys.exit(1)
    else:
        print("\n✅ ALL SMOKE TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
