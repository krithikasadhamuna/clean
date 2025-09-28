#!/usr/bin/env python3
"""
Check all endpoints in database including inactive ones
"""

import sqlite3
from datetime import datetime

def check_all_endpoints():
    """Check all endpoints in database"""
    try:
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        print("🔍 ALL ENDPOINTS IN DATABASE")
        print("=" * 50)
        
        # Get all agents regardless of status
        cursor.execute('''
            SELECT id, hostname, ip_address, platform, status, last_heartbeat, agent_version
            FROM agents 
            ORDER BY last_heartbeat DESC
        ''')
        
        agents = cursor.fetchall()
        
        if agents:
            for i, agent in enumerate(agents):
                agent_id, hostname, ip_address, platform, status, last_heartbeat, agent_type = agent
                
                print(f"Endpoint #{i+1}:")
                print(f"  ID: {agent_id}")
                print(f"  Hostname: {hostname}")
                print(f"  IP Address: {ip_address}")
                print(f"  Platform: {platform}")
                print(f"  Status: {status}")
                print(f"  Last Heartbeat: {last_heartbeat}")
                print(f"  Agent Type: {agent_type}")
                
                # Calculate if it should be active
                if last_heartbeat:
                    try:
                        last_heartbeat_dt = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                        time_diff = (datetime.now() - last_heartbeat_dt).total_seconds()
                        should_be_active = time_diff < 300  # 5 minutes
                        print(f"  Time Since Heartbeat: {time_diff:.0f} seconds")
                        print(f"  Should Be Active: {should_be_active}")
                    except:
                        print(f"  Time Parse Error")
                
                print()
        else:
            print("No agents found in database")
        
        # Check why the API might be filtering
        print("🔍 API FILTERING ANALYSIS")
        print("-" * 30)
        
        # Check the exact query the API uses
        cursor.execute('''
            SELECT a.id, a.hostname, a.ip_address, a.platform, a.status, a.last_heartbeat, a.agent_version
            FROM agents a
            LEFT JOIN log_entries le ON a.id = le.agent_id 
            WHERE le.timestamp > datetime('now', '-1 hour')
            GROUP BY a.id, a.hostname, a.ip_address, a.platform, a.status, a.last_heartbeat, a.agent_version
            ORDER BY a.last_heartbeat DESC
        ''')
        
        api_agents = cursor.fetchall()
        print(f"Agents returned by API query: {len(api_agents)}")
        
        for agent in api_agents:
            print(f"  API sees: {agent[1]} ({agent[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_endpoints()
