#!/usr/bin/env python3
"""
Test script for client agent endpoints
"""

import requests
import json
import time

def test_endpoints():
    """Test all client agent endpoints"""
    base_url = "http://localhost:8080"
    
    print(" Testing Client Agent Endpoints")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("Health Check", "GET", "/health"),
        ("Agent Heartbeat", "POST", "/api/agents/test-agent/heartbeat", {"agent_id": "test-agent", "status": "active"}),
        ("Agent Commands", "GET", "/api/agents/test-agent/commands"),
        ("Log Ingestion", "POST", "/api/logs/ingest", {"agent_id": "test-agent", "logs": [{"message": "test log", "level": "info"}]}),
        ("Frontend Agents", "GET", "/api/backend/agents"),
        ("Network Topology", "GET", "/api/backend/network-topology"),
        ("Software Download", "GET", "/api/backend/software-download")
    ]
    
    results = []
    
    for name, method, endpoint, *data in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                payload = data[0] if data else {}
                response = requests.post(url, json=payload, timeout=5)
            
            status = " PASS" if response.status_code == 200 else f" FAIL ({response.status_code})"
            results.append((name, status, response.status_code))
            
            print(f"{status} {name}: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            results.append((name, f" ERROR", str(e)))
            print(f" ERROR {name}: {e}")
    
    print("\n Summary:")
    print("-" * 30)
    passed = len([r for r in results if "" in r[1]])
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All endpoints working!")
        return True
    else:
        print("WARNING:  Some endpoints failed")
        return False

if __name__ == "__main__":
    test_endpoints()
