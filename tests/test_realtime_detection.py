#!/usr/bin/env python3
"""
Test real-time threat detection
"""

import requests
import json
import time

def test_detection_api():
    """Test the detection results API"""
    try:
        print(" Testing Real-Time Threat Detection API")
        print("=" * 50)
        
        # Test detection results endpoint
        response = requests.get('http://localhost:8080/api/backend/detections')
        
        print(f"Detection API Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Total Threats: {data.get('total_threats', 0)}")
            
            detections = data.get('detections', [])
            if detections:
                print(f"\n🚨 RECENT THREATS DETECTED:")
                print("-" * 30)
                for i, detection in enumerate(detections[:5]):  # Show first 5
                    print(f"Threat #{i+1}:")
                    print(f"  Type: {detection.get('threat_type')}")
                    print(f"  Severity: {detection.get('severity')}")
                    print(f"  Confidence: {detection.get('confidence_score'):.2f}")
                    print(f"  Source Machine: {detection.get('source_machine', {}).get('hostname')} ({detection.get('source_machine', {}).get('ip_address')})")
                    print(f"  Log Source: {detection.get('log_info', {}).get('source')}")
                    print(f"  Message: {detection.get('log_info', {}).get('message')[:100]}...")
                    print(f"  Detected At: {detection.get('detected_at')}")
                    print()
            else:
                print(" No threats detected yet")
        else:
            print(f" API Error: {response.text}")
            
    except Exception as e:
        print(f" Test failed: {e}")

def test_health_and_stats():
    """Test overall system health"""
    try:
        print("\n System Health Check")
        print("-" * 30)
        
        # Health check
        health = requests.get('http://localhost:8080/health').json()
        print(f"System Status: {health.get('status')}")
        
        # Agent status
        agents = requests.get('http://localhost:8080/api/backend/agents').json()
        active_agents = len([a for a in agents.get('agents', []) if a.get('status') == 'active'])
        print(f"Active Agents: {active_agents}")
        
        # Network topology
        topology = requests.get('http://localhost:8080/api/backend/network-topology').json()
        endpoints = topology.get('network_topology', {}).get('metadata', {}).get('total_endpoints', 0)
        print(f"Network Endpoints: {endpoints}")
        
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    test_detection_api()
    test_health_and_stats()
    
    print("\n Monitoring for new threats...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(30)  # Check every 30 seconds
            response = requests.get('http://localhost:8080/api/backend/detections')
            if response.status_code == 200:
                data = response.json()
                threat_count = data.get('total_threats', 0)
                if threat_count > 0:
                    print(f"🚨 {threat_count} threats detected at {time.strftime('%H:%M:%S')}")
                else:
                    print(f" System secure at {time.strftime('%H:%M:%S')}")
    except KeyboardInterrupt:
        print("\n Monitoring stopped")
