#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('test_soc_database.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check log_entries if it exists
try:
    cursor.execute("SELECT COUNT(*) FROM log_entries")
    count = cursor.fetchone()[0]
    print(f"Log entries: {count}")
    
    if count > 0:
        cursor.execute("SELECT * FROM log_entries LIMIT 3")
        rows = cursor.fetchall()
        print("Sample logs:")
        for row in rows:
            print(row)
except Exception as e:
    print(f"Error checking log_entries: {e}")

conn.close()
