#!/usr/bin/env python3
"""
Real-time agent status monitor
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta
from collections import defaultdict

def monitor_agent_status(db_path="soc_database.db", refresh_interval=10):
    """Monitor agent status in real-time"""
    
    print("=" * 60)
    print("CodeGrey Agent Status Monitor")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Refresh: Every {refresh_interval} seconds")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 60)
            print(f"CodeGrey Agent Status Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all agents
                cursor.execute('''
                    SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_type, created_at
                    FROM agents 
                    ORDER BY last_heartbeat DESC
                ''')
                
                rows = cursor.fetchall()
                conn.close()
                
                if not rows:
                    print(" No agents found in database")
                    time.sleep(refresh_interval)
                    continue
                
                # Categorize agents by status
                status_counts = defaultdict(int)
                recent_agents = []
                stale_agents = []
                
                for row in rows:
                    agent_id, hostname, ip_address, platform, status, last_heartbeat, agent_type, created_at = row
                    
                    status_counts[status] += 1
                    
                    # Check if heartbeat is recent (within 5 minutes)
                    try:
                        if last_heartbeat:
                            last_hb = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                            time_diff = datetime.now() - last_hb.replace(tzinfo=None)
                            minutes_ago = int(time_diff.total_seconds() / 60)
                            
                            if minutes_ago <= 5:
                                recent_agents.append((row, minutes_ago))
                            else:
                                stale_agents.append((row, minutes_ago))
                        else:
                            stale_agents.append((row, "Never"))
                    except:
                        stale_agents.append((row, "Invalid"))
                
                # Status summary
                print(f" STATUS SUMMARY:")
                print(f"   Total Agents: {len(rows)}")
                for status, count in status_counts.items():
                    print(f"   {status.title()}: {count}")
                print()
                
                # Recent activity (last 5 minutes)
                if recent_agents:
                    print(f" RECENT ACTIVITY (Last 5 minutes): {len(recent_agents)} agents")
                    print("-" * 40)
                    for (row, minutes_ago) in recent_agents:
                        agent_id, hostname, status = row[0], row[1], row[4]
                        print(f"   {agent_id} ({hostname}) - Status: {status} - {minutes_ago}m ago")
                    print()
                
                # Stale agents
                if stale_agents:
                    print(f"WARNING:  STALE AGENTS (No recent heartbeat): {len(stale_agents)} agents")
                    print("-" * 40)
                    for (row, minutes_ago) in stale_agents:
                        agent_id, hostname, status = row[0], row[1], row[4]
                        print(f"   {agent_id} ({hostname}) - Status: {status} - Last: {minutes_ago}")
                    print()
                
                # Status issues
                print("🔍 STATUS ANALYSIS:")
                print("-" * 40)
                
                issues_found = False
                
                # Check for agents with heartbeats but wrong status
                for (row, minutes_ago) in recent_agents:
                    agent_id, hostname, status = row[0], row[1], row[4]
                    if status != 'active':
                        print(f" {agent_id} ({hostname}): Has recent heartbeat but status is '{status}'")
                        issues_found = True
                
                # Check for agents marked active but no recent heartbeat
                for (row, minutes_ago) in stale_agents:
                    agent_id, hostname, status = row[0], row[1], row[4]
                    if status == 'active':
                        print(f" {agent_id} ({hostname}): Marked as 'active' but no recent heartbeat ({minutes_ago})")
                        issues_found = True
                
                if not issues_found:
                    print(" No status issues detected")
                
                print()
                print(f" Refreshing in {refresh_interval} seconds... (Ctrl+C to stop)")
                
            except Exception as e:
                print(f" Database error: {e}")
            
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\n Monitor stopped by user")
    except Exception as e:
        print(f"\n Monitor error: {e}")

if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "soc_database.db"
    refresh_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    monitor_agent_status(db_path, refresh_interval)
