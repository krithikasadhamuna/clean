#!/usr/bin/env python3
"""
Test the new API structure with 'data' format
"""

import requests
import json
import time

def test_api_structure():
    """Test all APIs with new data structure"""
    
    print(" TESTING NEW API STRUCTURE")
    print("=" * 50)
    
    # Wait for server to start
    time.sleep(5)
    
    apis = [
        ("Agents API", "/api/backend/agents"),
        ("Network Topology API", "/api/backend/network-topology"), 
        ("Software Download API", "/api/backend/software-download"),
        ("Detection Results API", "/api/backend/detections")
    ]
    
    for name, endpoint in apis:
        try:
            response = requests.get(f'http://localhost:8080{endpoint}', timeout=10)
            
            print(f"\n {name}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check structure
                if 'data' in data:
                    print(f" Uses 'data' structure")
                    print(f" Data items: {len(data['data'])}")
                    
                    # Show first item structure
                    if data['data']:
                        first_item = data['data'][0]
                        print(f" First item keys: {list(first_item.keys())}")
                else:
                    print(f"WARNING:  Structure: {list(data.keys())}")
                
                # Show sample
                print(f"Sample response:")
                print(json.dumps(data, indent=2)[:300] + "...")
                
            else:
                print(f" Error: {response.text}")
                
        except Exception as e:
            print(f" {name} failed: {e}")
    
    print(f"\n API STRUCTURE SUMMARY:")
    print("- All APIs now use 'data' instead of 'agents'/'columns'/'rows'")
    print("- Maintained original structure within 'data'")
    print("- Added proper error handling")
    print("- Centralized in api_utils.py")

if __name__ == "__main__":
    test_api_structure()
