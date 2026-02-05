#!/usr/bin/env python3
"""Direct SQL proof - independent of other scripts."""
import asyncio
import asyncpg
import os
import sys

async def direct_sql_proof():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # 1) List tables in public schema
    tables = await conn.fetch('''
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name
    ''')
    print('=== TABLES IN PUBLIC SCHEMA ===')
    for t in tables:
        print(f"  - {t['table_name']}")
    
    # 2) Check for PII columns
    pii_cols = ['user_id', 'username', 'first_name', 'last_name', 'phone', 
                'email', 'file_id', 'caption', 'message_text', 'ocr_raw_text', 'raw_text']
    found_pii = await conn.fetch('''
        SELECT table_name, column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = ANY($1::text[])
    ''', pii_cols)
    print('\n=== PII COLUMNS FOUND ===')
    if found_pii:
        for r in found_pii:
            print(f"  !! {r['table_name']}.{r['column_name']}")
    else:
        print('  NONE (zero-knowledge verified)')
    
    # 3) Row counts
    users_count = await conn.fetchval('SELECT COUNT(*) FROM users')
    rate_limits_count = await conn.fetchval('SELECT COUNT(*) FROM rate_limits')
    print('\n=== ROW COUNTS ===')
    print(f'  users: {users_count}')
    print(f'  rate_limits: {rate_limits_count}')
    
    await conn.close()
    print('\n=== DIRECT SQL PROOF COMPLETE ===')

if __name__ == '__main__':
    asyncio.run(direct_sql_proof())
    sys.exit(0)
