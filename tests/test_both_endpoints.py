#!/usr/bin/env python3
"""
Test if both client endpoints appear in API
"""

import requests
import json

def test_endpoints():
    """Test network topology API for both endpoints"""
    try:
        response = requests.get('http://localhost:8080/api/backend/network-topology')
        
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get('data', [])
            metadata = data.get('metadata', {})
            
            print(" NETWORK TOPOLOGY API RESULTS")
            print("=" * 40)
            print(f"Status: {data.get('status')}")
            print(f"Total Endpoints: {len(endpoints)}")
            print(f"Active: {metadata.get('activeEndpoints', 0)}")
            print(f"Inactive: {metadata.get('inactiveEndpoints', 0)}")
            print()
            
            if endpoints:
                for i, endpoint in enumerate(endpoints):
                    print(f"Endpoint #{i+1}:")
                    print(f"  Hostname: {endpoint.get('hostname')}")
                    print(f"  IP Address: {endpoint.get('ipAddress')}")
                    print(f"  Platform: {endpoint.get('platform')}")
                    print(f"  Location: {endpoint.get('location')}")
                    print(f"  Status: {endpoint.get('status')}")
                    print(f"  Services: {endpoint.get('services', [])}")
                    print(f"  Last Seen: {endpoint.get('lastSeen')}")
                    print()
            else:
                print(" No endpoints found")
                
            # Show the issue
            if len(endpoints) == 1:
                print("WARNING:  ISSUE: Only 1 endpoint showing (should be 2)")
                print("   Reason: API filtering removed inactive agents")
            elif len(endpoints) == 2:
                print(" Both endpoints showing correctly")
            
        else:
            print(f" API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f" Test failed: {e}")

if __name__ == "__main__":
    test_endpoints()
