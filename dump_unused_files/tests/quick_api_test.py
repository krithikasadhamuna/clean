#!/usr/bin/env python3
"""
Quick API test to verify current status
"""

import requests

def quick_test():
    try:
        # Test network topology
        response = requests.get('http://localhost:8080/api/backend/network-topology')
        if response.status_code == 200:
            data = response.json()
            print(f"Network Topology Status: {data.get('status')}")
            print(f"Data count: {len(data.get('data', []))}")
            
            for endpoint in data.get('data', []):
                print(f"  {endpoint.get('hostname')} ({endpoint.get('ipAddress')})")
                print(f"    Location: {endpoint.get('location')}")
                print(f"    Network Zone: {endpoint.get('networkZone')}")
                print(f"    Status: {endpoint.get('status')}")
        
        # Test agents API
        response = requests.get('http://localhost:8080/api/backend/agents')
        if response.status_code == 200:
            data = response.json()
            print(f"\nAgents API Status: {data.get('status')}")
            print(f"Agent count: {len(data.get('data', []))}")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    quick_test()
