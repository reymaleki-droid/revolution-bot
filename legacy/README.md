# Legacy Files

⚠️ **DO NOT USE THESE FILES IN PRODUCTION** ⚠️

This folder contains deprecated, experimental, and fix scripts that are kept for historical reference only.

## Why These Files Are Here

1. **bot_broken.py** - Old bot version with bugs
2. **database.py** - INSECURE SQLite database that stores PLAINTEXT user IDs
3. **secure_database.py** - Early secure database attempt (SQLite)
4. **secure_database_complete.py** - Incomplete migration
5. **secure_database_part1.py** - Partial implementation
6. **certificate_generator_old.py** - Old certificate logic
7. **fix_*.py, *_fix.py** - One-time fix scripts
8. **restore_bot.py, smart_fix.py, etc.** - Development utilities

## Production Files

For production, use ONLY:
- `bot.py` - Main bot application
- `secure_database_pg.py` - Zero-knowledge PostgreSQL database
- `config.py` - Environment-based configuration
- `utils.py` - Utilities
- `certificate_generator.py` - Certificate generation
- `ocr_service.py` - OCR verification

## Security Warning

The `database.py` file in this folder stores:
- Plaintext Telegram user IDs
- Usernames
- First names
- File IDs

**NEVER use this file with real users.**
