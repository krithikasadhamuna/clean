#!/usr/bin/env python3
"""
Quick detection check
"""

import requests

def check_detections():
    try:
        r = requests.get('http://localhost:8080/api/backend/detections')
        data = r.json()
        
        print(f" Detection Status: {data.get('status')}")
        print(f"🚨 Total Threats: {data.get('total_threats', 0)}")
        
        detections = data.get('detections', [])
        if detections:
            print("\n🚨 RECENT THREATS:")
            for i, d in enumerate(detections[:5]):
                print(f"  {i+1}. {d.get('threat_type')} - {d.get('severity')} - Score: {d.get('confidence_score', 0):.2f}")
                print(f"     Message: {d.get('log_info', {}).get('message', '')[:80]}...")
                print(f"     Time: {d.get('detected_at', '')}")
                print()
        else:
            print(" No threats detected")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_detections()
