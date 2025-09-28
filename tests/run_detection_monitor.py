#!/usr/bin/env python3
"""
Run real-time detection monitoring
"""

import requests
import json
import time
from datetime import datetime

def monitor_detections():
    """Monitor for real-time threat detections"""
    print("REAL-TIME DETECTION MONITOR")
    print("=" * 40)
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        while True:
            # Check for new detections
            response = requests.get('http://localhost:8080/api/backend/detections', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                detections = data.get('data', [])
                
                if detections:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] THREATS DETECTED: {len(detections)}")
                    
                    # Show latest detection
                    latest = detections[0]
                    print(f"  Latest: {latest.get('threatType')} - {latest.get('severity')}")
                    print(f"  Source: {latest.get('sourceAgent')} - {latest.get('logSource')}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] System secure - No threats")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] API Error: {response.status_code}")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitoring stopped")

if __name__ == "__main__":
    monitor_detections()
