#!/usr/bin/env python3
"""Test PostgreSQL connection on Railway"""
import asyncio
import os
import traceback

async def test_connection():
    import asyncpg
    
    db_url = os.environ.get('DATABASE_URL', '')
    print(f"DATABASE_URL: {db_url[:50]}...")
    print(f"Full URL length: {len(db_url)}")
    
    # Check if URL has sslmode parameter
    if '?sslmode=' in db_url:
        print("URL contains sslmode parameter, stripping it...")
        db_url = db_url.split('?')[0]
    
    modes = [
        ('require', 'require'),
        ('prefer', 'prefer'),
        (False, 'disabled'),
    ]
    
    for ssl_mode, name in modes:
        try:
            print(f"\nAttempting connection with ssl={name}...")
            conn = await asyncpg.connect(db_url, ssl=ssl_mode, timeout=30)
            print("Connected!")
            v = await conn.fetchval('SELECT 1')
            print(f"Result: {v}")
            await conn.close()
            print(f"SUCCESS with ssl={name}!")
            return True
        except Exception as e:
            print(f"Failed with ssl={name}: {type(e).__name__}: {e}")
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
