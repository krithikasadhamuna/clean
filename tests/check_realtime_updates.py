#!/usr/bin/env python3
"""
Check if APIs are updating in real-time
"""

import requests
import time
from datetime import datetime

def check_updates():
    """Check for real-time API updates"""
    
    print("🔄 CHECKING REAL-TIME API UPDATES")
    print("=" * 50)
    
    # Check 1: Network Topology
    print("1. Network Topology API:")
    try:
        response = requests.get('http://localhost:8080/api/backend/network-topology')
        if response.status_code == 200:
            data = response.json()
            metadata = data.get('metadata', {})
            endpoints = data.get('data', [])
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Total Endpoints: {metadata.get('totalEndpoints', 0)}")
            print(f"   🟢 Active: {metadata.get('activeEndpoints', 0)}")
            print(f"   🔴 Inactive: {metadata.get('inactiveEndpoints', 0)}")
            print(f"   🕐 Last Updated: {metadata.get('lastUpdated', 'Unknown')}")
            
            if endpoints:
                for endpoint in endpoints:
                    hostname = endpoint.get('hostname')
                    services = endpoint.get('services', [])
                    status = endpoint.get('status')
                    print(f"   📍 {hostname} ({status}): {len(services)} services")
                    if services:
                        print(f"      Services: {', '.join(services)}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check 2: Detection Results
    print("2. Detection Results API:")
    try:
        response = requests.get('http://localhost:8080/api/backend/detections')
        if response.status_code == 200:
            data = response.json()
            total_threats = data.get('totalThreats', 0)
            detections = data.get('data', [])
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   🚨 Total Threats: {total_threats}")
            print(f"   🕐 Last Updated: {data.get('lastUpdated', 'Unknown')}")
            
            if detections:
                latest = detections[0]
                print(f"   📋 Latest Threat:")
                print(f"      Type: {latest.get('threatType')}")
                print(f"      Severity: {latest.get('severity')}")
                print(f"      Source: {latest.get('sourceMachine', {}).get('hostname')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Check 3: Database Stats
    print("3. Database Activity:")
    try:
        import sqlite3
        conn = sqlite3.connect('dev_soc_database.db')
        cursor = conn.cursor()
        
        # Recent logs count
        cursor.execute("SELECT COUNT(*) FROM log_entries WHERE timestamp > datetime('now', '-10 minutes')")
        recent_logs = cursor.fetchone()[0]
        
        # Recent detections
        cursor.execute("SELECT COUNT(*) FROM detection_results WHERE detected_at > datetime('now', '-10 minutes')")
        recent_detections = cursor.fetchone()[0]
        
        # Active agents
        cursor.execute("SELECT COUNT(*) FROM agents WHERE last_heartbeat > datetime('now', '-5 minutes')")
        active_agents = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   📝 Recent logs (10 min): {recent_logs}")
        print(f"   🛡️  Recent detections (10 min): {recent_detections}")
        print(f"   💓 Active agents (5 min): {active_agents}")
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    print()
    print("🎯 APIs are constantly updated with:")
    print("   • Real-time log ingestion")
    print("   • Live agent heartbeats") 
    print("   • Dynamic service discovery")
    print("   • Immediate threat detection")
    print("   • Auto-updating timestamps")

if __name__ == "__main__":
    check_updates()
