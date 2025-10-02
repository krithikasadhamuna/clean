#!/usr/bin/env python3
"""
Test CORS fix for CodeGrey AI SOC Platform on Amazon Linux 2023
Tests the actual API endpoints that your frontend uses
"""

import requests
import json
from urllib.parse import urljoin

def test_cors_endpoint(base_url, endpoint, method="GET", data=None, headers=None):
    """Test CORS for a specific endpoint"""
    url = urljoin(base_url, endpoint)
    
    print(f"\nTesting {method} {url}")
    print("-" * 60)
    
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
            status = "" if value else "x"
            print(f"     {status} {header}: {value}")
        
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
                    if isinstance(data, list):
                        print(f"   Response: Array with {len(data)} items")
                    elif isinstance(data, dict):
                        if 'agents' in data:
                            print(f"   Response: {len(data.get('agents', []))} agents")
                        elif 'nodes' in data:
                            print(f"   Response: {len(data.get('nodes', []))} nodes")
                        else:
                            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   x {method} request failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}...")
            
    except Exception as e:
        print(f"   x {method} request error: {e}")

def test_cors_fix():
    """Test CORS fix for Amazon Linux 2023 server"""
    print("CodeGrey AI SOC Platform - CORS Fix Test (Amazon Linux 2023)")
    print("=" * 70)
    
    base_url = "http://dev.codegrey.ai:8080"
    
    # Test your actual API endpoints
    endpoints = [
        # Core API endpoints
        ("/health", "GET"),
        ("/api/backend/agents", "GET"),
        ("/api/backend/network-topology", "GET"),
        ("/api/backend/software-download", "GET"),
        
        # LangGraph endpoints
        ("/api/backend/langgraph/attack/start", "POST", {
            "user_request": "Test CORS attack simulation",
            "attack_type": "apt",
            "complexity": "simple"
        }),
        ("/api/backend/langgraph/detection/status", "GET"),
        
        # Agent registration (for client agents)
        ("/api/agents/register", "POST", {
            "agent_id": "test_cors_agent",
            "hostname": "test_host",
            "platform": "test"
        }),
    ]
    
    print(f"Testing CORS for: {base_url}")
    print(f"Allowed Origins: http://localhost:3000, http://dev.codegrey.ai, https://dev.codegrey.ai")
    print(f"Frontend Domain: http://dev.codegrey.ai")
    
    for endpoint_info in endpoints:
        if len(endpoint_info) == 2:
            endpoint, method = endpoint_info
            data = None
        else:
            endpoint, method, data = endpoint_info
        
        test_cors_endpoint(base_url, endpoint, method, data)
    
    print("\n" + "=" * 70)
    print("CORS Test Summary for Amazon Linux 2023:")
    print("=" * 70)
    print(" If you see 'Access-Control-Allow-Origin' headers, CORS is working")
    print(" If OPTIONS requests return 204, preflight is working")
    print(" If actual requests succeed, CORS is fully functional")
    print("\nYour frontend at http://dev.codegrey.ai should now work!")
    print("\nTo apply this fix to your Amazon Linux 2023 server:")
    print("1. Copy the nginx/nginx_config.conf to your server")
    print("2. Place it in /etc/nginx/sites-available/complete-soc")
    print("3. Run: sudo nginx -t")
    print("4. Run: sudo systemctl reload nginx")
    print("\nIf CORS is still not working:")
    print("1. Check that your frontend is running on http://dev.codegrey.ai")
    print("2. Check browser developer tools for CORS errors")
    print("3. Check Nginx logs: sudo tail -f /var/log/nginx/error.log")
    print("4. Verify the map directive is in the http block of nginx.conf")

if __name__ == "__main__":
    test_cors_fix()

