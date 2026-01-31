"""
Database Migration: Add OCR fields to conduit_verifications table
"""
import sqlite3
import os

DB_PATH = 'revolution_bot.db'

def migrate_database():
    """Add OCR tracking fields to existing table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return False
    
    print("🔄 Starting database migration...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(conduit_verifications)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        
        print(f"📋 Current columns: {', '.join(existing_columns)}")
        
        # Add new columns if they don't exist
        new_columns = [
            ('data_shared', 'TEXT'),
            ('points_earned', 'INTEGER DEFAULT 0'),
            ('ocr_extracted_amount', 'REAL'),
            ('ocr_confidence', 'INTEGER'),
            ('verification_method', 'TEXT'),
            ('ocr_raw_text', 'TEXT'),
        ]
        
        added = 0
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE conduit_verifications ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"  ✅ Added: {col_name} ({col_type})")
                    added += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"  ⏭️  Skipped: {col_name} (already exists)")
                    else:
                        raise
            else:
                print(f"  ⏭️  Skipped: {col_name} (already exists)")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(conduit_verifications)")
        final_columns = cursor.fetchall()
        
        print(f"\n✅ Migration complete!")
        print(f"📊 Final schema ({len(final_columns)} columns):")
        for col in final_columns:
            print(f"   {col[1]:25} {col[2]}")
        
        conn.close()
        
        if added > 0:
            print(f"\n🎉 Successfully added {added} new columns!")
        else:
            print(f"\n✅ Database already up to date!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
