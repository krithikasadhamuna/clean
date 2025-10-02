#!/usr/bin/env python3
"""
Test CORS fix for CodeGrey AI SOC Platform
"""

import requests
import json
from urllib.parse import urljoin

def test_cors_endpoint(base_url, endpoint, method="GET", data=None, headers=None):
    """Test CORS for a specific endpoint"""
    url = urljoin(base_url, endpoint)
    
    print(f"\nTesting {method} {url}")
    print("-" * 50)
    
    # Test preflight OPTIONS request
    print("1. Testing OPTIONS preflight request...")
    try:
        options_headers = {
            'Origin': 'http://dev.codegrey.ai',
            'Access-Control-Request-Method': method,
            'Access-Control-Request-Headers': 'Content-Type, Authorization, X-API-Key'
        }
        
        response = requests.options(url, headers=options_headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            'Access-Control-Max-Age': response.headers.get('Access-Control-Max-Age')
        }
        
        print("   CORS Headers:")
        for header, value in cors_headers.items():
            print(f"     {header}: {value}")
        
        if response.status_code == 204:
            print("    OPTIONS request successful")
        else:
            print(f"   x OPTIONS request failed: {response.status_code}")
            
    except Exception as e:
        print(f"   x OPTIONS request error: {e}")
    
    # Test actual request
    print(f"\n2. Testing {method} request...")
    try:
        request_headers = {
            'Origin': 'http://dev.codegrey.ai',
            'Content-Type': 'application/json'
        }
        if headers:
            request_headers.update(headers)
        
        if method == "GET":
            response = requests.get(url, headers=request_headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=request_headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=request_headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=request_headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
        print(f"   Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials')}")
        
        if response.status_code in [200, 201, 204]:
            print(f"    {method} request successful")
            if response.content:
                try:
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   x {method} request failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   x {method} request error: {e}")

def test_cors_fix():
    """Test CORS fix comprehensively"""
    print("CodeGrey AI SOC Platform - CORS Fix Test")
    print("=" * 60)
    
    base_url = "http://backend.codegrey.ai:8080"
    
    # Test endpoints
    endpoints = [
        ("/", "GET"),
        ("/health", "GET"),
        ("/api/agents", "GET"),
        ("/api/agents/register", "POST", {"agent_id": "test_agent", "hostname": "test_host"}),
        ("/api/backend/agents", "GET"),
        ("/api/logs/ingest", "POST", {"agent_id": "test", "logs": []}),
    ]
    
    print(f"Testing CORS for: {base_url}")
    print(f"Allowed Origins: http://localhost:3000, http://dev.codegrey.ai, https://dev.codegrey.ai")
    
    for endpoint_info in endpoints:
        if len(endpoint_info) == 2:
            endpoint, method = endpoint_info
            data = None
        else:
            endpoint, method, data = endpoint_info
        
        test_cors_endpoint(base_url, endpoint, method, data)
    
    print("\n" + "=" * 60)
    print("CORS Test Summary:")
    print("=" * 60)
    print(" If you see 'Access-Control-Allow-Origin' headers, CORS is working")
    print(" If OPTIONS requests return 204, preflight is working")
    print(" If actual requests succeed, CORS is fully functional")
    print("\nIf CORS is still not working:")
    print("1. Check that Nginx configuration is updated")
    print("2. Restart Nginx: sudo systemctl reload nginx")
    print("3. Check Nginx logs: sudo tail -f /var/log/nginx/error.log")
    print("4. Verify the map directive is in the http block")

if __name__ == "__main__":
    test_cors_fix()
