#!/usr/bin/env python3
"""
Monitor API updates in real-time to show constant updates
"""

import requests
import json
import time
from datetime import datetime

def monitor_apis():
    """Monitor all APIs for constant updates"""
    
    print(" MONITORING CONSTANT API UPDATES")
    print("=" * 50)
    print("Watching for real-time changes in:")
    print("   Network Topology (services, status)")
    print("    Detection Results (new threats)")
    print("   Agent Status (heartbeats)")
    print()
    
    previous_data = {}
    
    try:
        iteration = 0
        while True:
            iteration += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            print(f"🕐 Update #{iteration} at {current_time}")
            print("-" * 30)
            
            # Check Network Topology
            try:
                response = requests.get('http://localhost:8080/api/backend/network-topology', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    endpoints = data.get('data', [])
                    metadata = data.get('metadata', {})
                    
                    print(f" Network Topology:")
                    print(f"   Total Endpoints: {metadata.get('totalEndpoints', 0)}")
                    print(f"   Active: {metadata.get('activeEndpoints', 0)}")
                    print(f"   Last Updated: {metadata.get('lastUpdated', 'Unknown')}")
                    
                    # Show services for each endpoint
                    for endpoint in endpoints:
                        hostname = endpoint.get('hostname', 'Unknown')
                        services = endpoint.get('services', [])
                        status = endpoint.get('status', 'unknown')
                        print(f"   {hostname} ({status}): {len(services)} services")
                        if services:
                            print(f"     Services: {', '.join(services[:3])}{'...' if len(services) > 3 else ''}")
                    
                    # Check for changes
                    current_topology = json.dumps(endpoints, sort_keys=True)
                    if 'topology' in previous_data and previous_data['topology'] != current_topology:
                        print("    TOPOLOGY CHANGED!")
                    previous_data['topology'] = current_topology
                    
            except Exception as e:
                print(f"    Topology error: {e}")
            
            # Check Detection Results
            try:
                response = requests.get('http://localhost:8080/api/backend/detections', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    total_threats = data.get('totalThreats', 0)
                    detections = data.get('data', [])
                    
                    print(f"  Detection Results:")
                    print(f"   Total Threats: {total_threats}")
                    
                    if detections:
                        latest = detections[0]
                        print(f"   Latest: {latest.get('threatType', 'unknown')} ({latest.get('severity', 'unknown')})")
                        print(f"   Detected: {latest.get('detectedAt', 'unknown')}")
                    
                    # Check for new threats
                    if 'threats' in previous_data and previous_data['threats'] != total_threats:
                        print("   🚨 NEW THREATS DETECTED!")
                    previous_data['threats'] = total_threats
                    
            except Exception as e:
                print(f"    Detection error: {e}")
            
            # Check Agent Status
            try:
                response = requests.get('http://localhost:8080/api/backend/agents', timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get('data', [])
                    
                    print(f" SOC Agents:")
                    active_agents = len([a for a in agents if a.get('status') == 'active'])
                    print(f"   Active Agents: {active_agents}/{len(agents)}")
                    
            except Exception as e:
                print(f"    Agents error: {e}")
            
            print()
            
            # Wait before next check
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n Monitoring stopped")
    except Exception as e:
        print(f"\n Monitoring failed: {e}")

def test_api_responsiveness():
    """Test how quickly APIs respond to changes"""
    print("lightning TESTING API RESPONSIVENESS")
    print("=" * 40)
    
    # Send a test log and measure response time
    start_time = time.time()
    
    test_payload = {
        "agent_id": "responsiveness-test",
        "logs": [
            {
                "timestamp": datetime.now().isoformat(),
                "source": "Windows-Process",
                "level": "INFO",
                "message": "Process notepad.exe started - PID: 12345",
                "process_info": {
                    "name": "notepad.exe",
                    "pid": 12345
                }
            }
        ]
    }
    
    try:
        # Send log
        requests.post('http://localhost:8080/api/logs/ingest', json=test_payload, timeout=5)
        
        # Check how quickly it appears in topology
        for i in range(5):
            response = requests.get('http://localhost:8080/api/backend/network-topology', timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Check if new data appears
                updated_time = data.get('metadata', {}).get('lastUpdated', '')
                if updated_time:
                    response_time = time.time() - start_time
                    print(f" API updated in {response_time:.2f} seconds")
                    break
            time.sleep(1)
        
    except Exception as e:
        print(f" Responsiveness test failed: {e}")

if __name__ == "__main__":
    # First test responsiveness
    time.sleep(5)  # Wait for server to start
    test_api_responsiveness()
    
    print("\n" + "="*50)
    
    # Then start monitoring
    monitor_apis()
