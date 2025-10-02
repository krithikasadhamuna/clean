#!/usr/bin/env python3
"""
Script to reset or clean the production database
"""

import sqlite3
import sys
import argparse
from datetime import datetime
import os

def backup_database(db_path):
    """Create a backup of the database before reset"""
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Failed to backup database: {e}")
        return False

def clean_duplicates(db_path):
    """Remove duplicate agent entries, keeping the most recent one"""
    
    print("Cleaning duplicate agent entries...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all agents with duplicates
        cursor.execute('''
            SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_type, created_at
            FROM agents 
            ORDER BY id, created_at DESC
        ''')
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No agents found in database")
            return True
        
        # Group by agent ID and keep only the most recent entry
        seen_ids = set()
        agents_to_keep = []
        duplicates_removed = 0
        
        for row in rows:
            agent_id = row[0]
            if agent_id not in seen_ids:
                seen_ids.add(agent_id)
                agents_to_keep.append(row)
            else:
                duplicates_removed += 1
        
        if duplicates_removed == 0:
            print("No duplicates found - database is clean")
            return True
        
        # Clear the agents table
        cursor.execute('DELETE FROM agents')
        
        # Re-insert only the unique agents (most recent)
        for row in agents_to_keep:
            cursor.execute('''
                INSERT INTO agents (
                    id, hostname, ip_address, platform, status, last_heartbeat, agent_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', row)
        
        conn.commit()
        conn.close()
        
        print(f"Removed {duplicates_removed} duplicate entries")
        print(f"Kept {len(agents_to_keep)} unique agents")
        
        return True
        
    except Exception as e:
        print(f"Error cleaning duplicates: {e}")
        return False

def reset_database(db_path):
    """Completely reset the database"""
    
    print("Resetting database...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop all tables
        cursor.execute("DROP TABLE IF EXISTS agents")
        cursor.execute("DROP TABLE IF EXISTS log_entries")
        cursor.execute("DROP TABLE IF EXISTS detection_results")
        cursor.execute("DROP TABLE IF EXISTS network_topology")
        
        # Recreate agents table
        cursor.execute('''
            CREATE TABLE agents (
                id TEXT PRIMARY KEY,
                hostname TEXT,
                ip_address TEXT,
                platform TEXT,
                os_version TEXT,
                agent_version TEXT,
                status TEXT DEFAULT 'offline',
                last_heartbeat TIMESTAMP,
                last_log_sent TIMESTAMP,
                capabilities TEXT,
                log_sources TEXT,
                configuration TEXT,
                security_zone TEXT DEFAULT 'internal',
                importance TEXT DEFAULT 'medium',
                logs_sent_count INTEGER DEFAULT 0,
                bytes_sent INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Recreate log_entries table
        cursor.execute('''
            CREATE TABLE log_entries (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                source TEXT,
                timestamp TIMESTAMP,
                collected_at TIMESTAMP,
                processed_at TIMESTAMP,
                message TEXT,
                raw_data TEXT,
                level TEXT,
                parsed_data TEXT,
                enriched_data TEXT,
                event_id TEXT,
                event_type TEXT,
                process_info TEXT,
                network_info TEXT,
                attack_technique TEXT,
                attack_command TEXT,
                attack_result TEXT,
                threat_score REAL DEFAULT 0.0,
                threat_level TEXT DEFAULT 'benign',
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        ''')
        
        # Recreate detection_results table
        cursor.execute('''
            CREATE TABLE detection_results (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                log_entry_id TEXT,
                detection_type TEXT,
                threat_level TEXT,
                confidence_score REAL,
                description TEXT,
                mitigation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents (id),
                FOREIGN KEY (log_entry_id) REFERENCES log_entries (id)
            )
        ''')
        
        # Recreate network_topology table
        cursor.execute('''
            CREATE TABLE network_topology (
                id TEXT PRIMARY KEY,
                hostname TEXT,
                ip_address TEXT,
                platform TEXT,
                services TEXT,
                last_seen TIMESTAMP,
                discovered_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("Database reset successfully")
        print("All tables recreated with proper schema")
        
        return True
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="CodeGrey Database Management")
    parser.add_argument("--db-path", default="soc_database.db", help="Database file path")
    parser.add_argument("--clean-duplicates", action="store_true", help="Remove duplicate entries")
    parser.add_argument("--reset", action="store_true", help="Completely reset database")
    parser.add_argument("--backup", action="store_true", help="Create backup before operation")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup (use with caution)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CodeGrey SOC Platform - Database Management")
    print("=" * 60)
    print(f"Database: {args.db_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check if database exists
    if not os.path.exists(args.db_path):
        print(f"Database file not found: {args.db_path}")
        return 1
    
    # Create backup unless explicitly skipped
    if not args.no_backup and (args.clean_duplicates or args.reset):
        backup_path = backup_database(args.db_path)
        if not backup_path:
            print("Backup failed - aborting operation")
            return 1
    
    # Perform operations
    success = True
    
    if args.clean_duplicates:
        success = clean_duplicates(args.db_path)
    elif args.reset:
        success = reset_database(args.db_path)
    else:
        print("No operation specified. Use --clean-duplicates or --reset")
        parser.print_help()
        return 1
    
    if success:
        print()
        print("Operation completed successfully!")
        return 0
    else:
        print()
        print("Operation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
