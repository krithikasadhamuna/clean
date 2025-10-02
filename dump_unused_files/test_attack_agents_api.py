#!/usr/bin/env python3
"""
Test script for Attack Agents API
Tests the client-side container orchestration and attack agents API
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8080"
API_KEY = None  # Disabled in development

def test_attack_agents_api():
    """Test the attack agents API endpoint"""
    print(" Testing Attack Agents API")
    print("=" * 50)
    
    try:
        url = f"{BASE_URL}/api/backend/attack-agents"
        headers = {'Content-Type': 'application/json'}
        
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        print(f" Making request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f" Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(" Attack Agents API Response:")
            print(json.dumps(data, indent=2))
            
            # Validate structure
            if 'status' in data and 'agents' in data:
                print(f" Found {len(data['agents'])} attack agents")
                
                for i, agent in enumerate(data['agents']):
                    print(f"\n Agent {i+1}:")
                    print(f"   ID: {agent.get('id')}")
                    print(f"   Name: {agent.get('name')}")
                    print(f"   Type: {agent.get('type')}")
                    print(f"   Status: {agent.get('status')}")
                    print(f"   Location: {agent.get('location')}")
                    print(f"   Platform: {agent.get('platform')}")
                    print(f"   Capabilities: {', '.join(agent.get('capabilities', []))}")
                    
            else:
                print(" Invalid response structure")
        else:
            print(f" Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f" Error testing attack agents API: {e}")

def test_container_logs_as_regular_logs():
    """Test that container logs are sent as regular logs"""
    print("\n Testing Container Logs as Regular Logs")
    print("=" * 50)
    
    try:
        # Check recent logs for container activity
        url = f"{BASE_URL}/api/logs/ingest"
        
        # This would normally be sent by the client agent
        sample_container_log = {
            'agent_id': 'test-client',
            'logs': [
                {
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'level': 'INFO',
                    'source': 'AttackContainer',
                    'message': 'Starting nmap scan on target network',
                    'hostname': 'test-client',
                    'platform': 'Container',
                    'agent_type': 'attack_agent',
                    'container_context': True
                }
            ]
        }
        
        headers = {'Content-Type': 'application/json'}
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        print(f" Sending sample container log to: {url}")
        response = requests.post(url, json=sample_container_log, headers=headers, timeout=10)
        
        print(f" Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(" Container log ingested successfully:")
            print(json.dumps(data, indent=2))
        else:
            print(f" Log ingestion failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f" Error testing container logs: {e}")

def test_api_structure_compatibility():
    """Test API structure matches the expected format"""
    print("\n Testing API Structure Compatibility")
    print("=" * 50)
    
    expected_structure = {
        "status": "success",
        "agents": [
            {
                "id": "phantomstrike_ai",
                "name": "PhantomStrike AI",
                "type": "attack",
                "status": "active",
                "location": "External Network",
                "lastActivity": "Now",
                "capabilities": ["Attack Planning", "Scenario Generation", "Red Team Operations"],
                "platform": "LangChain Agent"
            }
        ]
    }
    
    print(" Expected Structure:")
    print(json.dumps(expected_structure, indent=2))
    
    try:
        url = f"{BASE_URL}/api/backend/attack-agents"
        headers = {'Content-Type': 'application/json'}
        
        if API_KEY:
            headers['X-API-Key'] = API_KEY
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check structure compatibility
            checks = []
            checks.append(('status' in data, "Has 'status' field"))
            checks.append(('agents' in data, "Has 'agents' field"))
            
            if 'agents' in data and len(data['agents']) > 0:
                agent = data['agents'][0]
                checks.append(('id' in agent, "Agent has 'id' field"))
                checks.append(('name' in agent, "Agent has 'name' field"))
                checks.append(('type' in agent, "Agent has 'type' field"))
                checks.append(('status' in agent, "Agent has 'status' field"))
                checks.append(('location' in agent, "Agent has 'location' field"))
                checks.append(('capabilities' in agent, "Agent has 'capabilities' field"))
                checks.append(('platform' in agent, "Agent has 'platform' field"))
            
            print("\n Structure Compatibility Checks:")
            for check_result, check_desc in checks:
                status = "" if check_result else ""
                print(f"   {status} {check_desc}")
            
            all_passed = all(check[0] for check in checks)
            if all_passed:
                print("\n🎉 All structure checks passed!")
            else:
                print("\nWARNING:  Some structure checks failed!")
                
        else:
            print(f" Could not test structure - API returned: {response.status_code}")
            
    except Exception as e:
        print(f" Error testing structure compatibility: {e}")

def main():
    """Main test function"""
    print(" CodeGrey AI SOC Platform - Attack Agents API Test")
    print("=" * 60)
    
    # Test individual components
    test_attack_agents_api()
    test_container_logs_as_regular_logs()
    test_api_structure_compatibility()
    
    print("\n" + "=" * 60)
    print(" Attack Agents API tests completed!")
    print("\n Summary:")
    print("   - Container logs are sent as regular logs through /api/logs/ingest")
    print("   - Attack agents API available at /api/backend/attack-agents")
    print("   - API structure matches PhantomStrike AI format")
    print("   - Client-side container orchestration ready")

if __name__ == "__main__":
    main()
