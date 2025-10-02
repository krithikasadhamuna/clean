#!/usr/bin/env python3
"""
Quick test script to verify all backend routes are working
"""

import requests
import json

BASE_URL = "http://15.207.6.45:8080"

def test_route(method, endpoint, data=None):
    """Test a single route"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f" {method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
        
    except Exception as e:
        print(f" {method} {endpoint}: {str(e)}")
    
    print("-" * 50)

def main():
    print(" Testing AI SOC Platform Backend Routes")
    print("=" * 50)
    
    # Test working routes
    print("Testing known working routes:")
    test_route("GET", "/health")
    
    print("\nTesting updated frontend API routes:")
    print("🔍 Testing agents (should return 4 agents, last 2 inactive):")
    test_route("GET", "/api/backend/agents")
    
    print("🔍 Testing software downloads (should return 3 OS downloads):")
    test_route("GET", "/api/backend/software-download")
    
    print("🔍 Testing other endpoints:")
    test_route("GET", "/api/backend/network-topology")
    test_route("GET", "/api/backend/langgraph/detection/status")
    
    print("\nTesting attack simulation:")
    attack_data = {
        "user_request": "Plan a simple phishing simulation",
        "attack_type": "phishing",
        "complexity": "simple"
    }
    test_route("POST", "/api/backend/langgraph/attack/start", attack_data)

if __name__ == "__main__":
    main()
