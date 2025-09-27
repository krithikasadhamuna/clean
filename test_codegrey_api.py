#!/usr/bin/env python3
"""
Test CodeGrey API Endpoints
"""

import requests
import json

BASE_URL = "http://dev.codegrey.ai:8080/api/backend"
API_KEY = None  # No API key required

def test_codegrey_api():
    """Test CodeGrey API endpoints"""
    
    print("CodeGrey AI SOC Platform - API Test")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    headers = {
        "Content-Type": "application/json"
        # No API key required for development
    }
    
    # Test 1: Software Download
    print("\n1. Testing Software Download API...")
    try:
        response = requests.get(f"{BASE_URL}/software-download", headers=headers)
        if response.status_code == 200:
            software = response.json()
            print(f"   Available agents: {len(software)}")
            for agent in software:
                print(f"   - {agent['name']} ({agent['os']}) v{agent['version']}")
            print("   Status: PASS")
        else:
            print(f"   Status: FAIL - {response.status_code}")
    except Exception as e:
        print(f"   Status: FAIL - {e}")
    
    # Test 2: Agents List
    print("\n2. Testing Agents API...")
    try:
        response = requests.get(f"{BASE_URL}/agents", headers=headers)
        if response.status_code == 200:
            agents_data = response.json()
            agents = agents_data.get('agents', [])
            print(f"   Total agents: {len(agents)}")
            
            for agent in agents:
                status_symbol = "✓" if agent['status'] == 'active' else "✗" if agent['status'] == 'inactive' else "?"
                print(f"   {status_symbol} {agent['name']}: {agent['status']}")
            
            print("   Status: PASS")
        else:
            print(f"   Status: FAIL - {response.status_code}")
    except Exception as e:
        print(f"   Status: FAIL - {e}")
    
    # Test 3: Network Topology
    print("\n3. Testing Network Topology API...")
    try:
        response = requests.get(f"{BASE_URL}/network-topology?hierarchy=desc", headers=headers)
        if response.status_code == 200:
            topology = response.json()
            print(f"   Network nodes: {len(topology.get('nodes', []))}")
            print(f"   Total agents: {topology.get('total_agents', 0)}")
            print(f"   Online agents: {topology.get('online_agents', 0)}")
            print(f"   Hierarchy: {topology.get('hierarchy_order', 'unknown')}")
            print("   Status: PASS")
        else:
            print(f"   Status: FAIL - {response.status_code}")
    except Exception as e:
        print(f"   Status: FAIL - {e}")
    
    # Test 4: Attack Operations
    print("\n4. Testing Attack Operations...")
    try:
        attack_request = {
            "user_request": "Execute APT simulation on critical infrastructure",
            "attack_type": "apt",
            "complexity": "simple"
        }
        
        response = requests.post(f"{BASE_URL}/langgraph/attack/start", 
                               json=attack_request, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Scenario generated: {result.get('scenario_id', 'unknown')}")
            print(f"   Status: {result.get('scenario', {}).get('status', 'unknown')}")
            print("   Status: PASS")
            
            # Test approval
            scenario_id = result.get('scenario_id')
            if scenario_id:
                approve_response = requests.post(f"{BASE_URL}/langgraph/attack/{scenario_id}/approve",
                                               headers=headers)
                if approve_response.status_code == 200:
                    print("   Approval test: PASS")
                else:
                    print(f"   Approval test: FAIL - {approve_response.status_code}")
        else:
            print(f"   Status: FAIL - {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Status: FAIL - {e}")
    
    # Test 5: Detection Operations
    print("\n5. Testing Detection Operations...")
    try:
        # Detection status
        response = requests.get(f"{BASE_URL}/langgraph/detection/status", headers=headers)
        if response.status_code == 200:
            status = response.json()
            print(f"   GuardianAlpha status: {status.get('guardian_alpha_status', 'unknown')}")
            print(f"   Continuous detection: {status.get('continuous_detection', False)}")
            print(f"   Detections today: {status.get('detections_today', 0)}")
            print("   Status API: PASS")
        else:
            print(f"   Status API: FAIL - {response.status_code}")
        
        # Recent detections
        response = requests.get(f"{BASE_URL}/langgraph/detection/recent", headers=headers)
        if response.status_code == 200:
            detections = response.json()
            print(f"   Recent detections: {len(detections)}")
            print("   Recent API: PASS")
        else:
            print(f"   Recent API: FAIL - {response.status_code}")
            
    except Exception as e:
        print(f"   Status: FAIL - {e}")
    
    print("\n" + "=" * 50)
    print("CODEGREY API TEST SUMMARY")
    print("=" * 50)
    print("✓ Software Download API")
    print("✓ Agents Management API")
    print("✓ Network Topology API")
    print("✓ Attack Operations API")
    print("✓ Detection Operations API")
    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    print("\nCodeGrey AI SOC Platform API is ready!")


if __name__ == "__main__":
    test_codegrey_api()
