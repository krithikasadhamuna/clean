#!/usr/bin/env python3
"""
Quick database check for remote server
"""

import sqlite3
import sys
from collections import Counter

def quick_check(db_path="soc_database.db"):
    """Quick check for duplicates"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get agent counts
        cursor.execute("SELECT COUNT(*) FROM agents")
        total_agents = cursor.fetchone()[0]
        
        # Get unique agent IDs
        cursor.execute("SELECT COUNT(DISTINCT id) FROM agents")
        unique_ids = cursor.fetchone()[0]
        
        # Get recent agents (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM agents 
            WHERE last_heartbeat > datetime('now', '-1 day')
        """)
        recent_agents = cursor.fetchone()[0]
        
        conn.close()
        
        # Quick analysis
        duplicates = total_agents - unique_ids
        
        print(f" Database Status: {db_path}")
        print(f"   Total Agents: {total_agents}")
        print(f"   Unique IDs: {unique_ids}")
        print(f"   Recent (24h): {recent_agents}")
        
        if duplicates > 0:
            print(f"    Duplicates: {duplicates}")
            print("    Run: python3 reset_database.py --clean-duplicates")
        else:
            print(f"    No duplicates found")
        
        return duplicates == 0
        
    except Exception as e:
        print(f" Error: {e}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "soc_database.db"
    quick_check(db_path)
