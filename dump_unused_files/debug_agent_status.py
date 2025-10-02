#!/usr/bin/env python3
"""
Debug script to check agent status and heartbeat issues
"""

import sqlite3
import requests
import json
from datetime import datetime, timedelta
import sys

def check_agent_status(db_path="soc_database.db", server_url="http://backend.codegrey.ai:8080"):
    """Debug agent status and heartbeat issues"""
    
    print("=" * 60)
    print("CodeGrey Agent Status Debug")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Server: {server_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check database
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
            return
        
        print(f" Found {len(rows)} agents in database:")
        print("-" * 40)
        
        for i, row in enumerate(rows, 1):
            agent_id, hostname, ip_address, platform, status, last_heartbeat, agent_type, created_at = row
            
            # Parse last heartbeat
            try:
                if last_heartbeat:
                    last_hb = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                    time_diff = datetime.now() - last_hb.replace(tzinfo=None)
                    minutes_ago = int(time_diff.total_seconds() / 60)
                else:
                    minutes_ago = "Never"
            except:
                minutes_ago = "Invalid"
            
            print(f"{i}. Agent ID: {agent_id}")
            print(f"   Hostname: {hostname}")
            print(f"   IP: {ip_address}")
            print(f"   Status: {status}")
            print(f"   Last Heartbeat: {last_heartbeat} ({minutes_ago} minutes ago)")
            print(f"   Type: {agent_type}")
            print(f"   Created: {created_at}")
            
            # Status analysis
            if status == 'active':
                if isinstance(minutes_ago, int) and minutes_ago > 5:
                    print(f"   WARNING:  WARNING: Agent marked as 'active' but last heartbeat was {minutes_ago} minutes ago")
                else:
                    print(f"    Agent appears healthy")
            elif status == 'offline':
                print(f"    Agent marked as 'offline'")
            else:
                print(f"   ? Unknown status: {status}")
            
            print()
        
        # Check for recent heartbeats
        print("🔍 RECENT ACTIVITY ANALYSIS:")
        print("-" * 40)
        
        recent_agents = [row for row in rows if row[5] and 
                        datetime.fromisoformat(row[5].replace('Z', '+00:00')).replace(tzinfo=None) > 
                        datetime.now() - timedelta(minutes=10)]
        
        print(f"Agents with heartbeats in last 10 minutes: {len(recent_agents)}")
        
        for row in recent_agents:
            agent_id, hostname, status, last_heartbeat = row[0], row[1], row[4], row[5]
            if status != 'active':
                print(f" {agent_id} ({hostname}): Heartbeat received but status is '{status}'")
            else:
                print(f" {agent_id} ({hostname}): Status matches heartbeat")
        
    except Exception as e:
        print(f" Database error: {e}")
        return
    
    # Check server API
    print("\n SERVER API CHECK:")
    print("-" * 40)
    
    try:
        # Test server connectivity
        response = requests.get(f"{server_url}/health", timeout=10)
        if response.status_code == 200:
            print(f" Server is reachable: {server_url}")
        else:
            print(f" Server returned status {response.status_code}")
    except Exception as e:
        print(f" Cannot reach server: {e}")
        return
    
    try:
        # Check agents API
        response = requests.get(f"{server_url}/api/agents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            server_agents = data.get('agents', [])
            print(f" Server API returned {len(server_agents)} agents")
            
            # Compare with database
            db_agent_ids = {row[0] for row in rows}
            server_agent_ids = {agent.get('id') for agent in server_agents}
            
            missing_in_server = db_agent_ids - server_agent_ids
            missing_in_db = server_agent_ids - db_agent_ids
            
            if missing_in_server:
                print(f"WARNING:  Agents in DB but not in server API: {missing_in_server}")
            if missing_in_db:
                print(f"WARNING:  Agents in server API but not in DB: {missing_in_db}")
            
            if not missing_in_server and not missing_in_db:
                print(" Database and server API are in sync")
                
        else:
            print(f" Server API returned status {response.status_code}")
    except Exception as e:
        print(f" Server API error: {e}")

def check_heartbeat_endpoint(server_url="http://backend.codegrey.ai:8080"):
    """Test heartbeat endpoint directly"""
    
    print("\n💓 HEARTBEAT ENDPOINT TEST:")
    print("-" * 40)
    
    # Test heartbeat endpoint
    test_agent_id = "test_agent_debug"
    test_data = {
        "agent_id": test_agent_id,
        "timestamp": datetime.now().isoformat(),
        "status": "online",
        "statistics": {
            "runtime_seconds": 100,
            "logs_processed": 50
        }
    }
    
    try:
        response = requests.post(
            f"{server_url}/api/agents/{test_agent_id}/heartbeat",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f" Heartbeat endpoint working: {response.json()}")
        else:
            print(f" Heartbeat endpoint failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f" Heartbeat endpoint error: {e}")

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "soc_database.db"
    server_url = sys.argv[2] if len(sys.argv) > 2 else "http://backend.codegrey.ai:8080"
    
    check_agent_status(db_path, server_url)
    check_heartbeat_endpoint(server_url)
    
    print("\n RECOMMENDATIONS:")
    print("-" * 40)
    print("1. Update client config to use correct server URL")
    print("2. Restart the client agent after config change")
    print("3. Check server logs for heartbeat processing errors")
    print("4. Verify agent ID consistency between registration and heartbeats")
    print("5. Check database for status update issues")

if __name__ == "__main__":
    main()
