#!/usr/bin/env python3
"""
Test pattern matching logic directly
"""

import re

def test_threat_patterns():
    """Test threat pattern matching"""
    
    # Test message
    test_message = "powershell.exe -enc JABhAD0AJwBoAHQAdABwADoALwAvAG0AYQBsAGkAYwBpAG8AdQBzAC4AYwBvAG0A"
    
    # Threat patterns (same as in detection engine)
    threat_patterns = {
        'malicious_processes': [
            r'powershell.*-enc.*',
            r'powershell.*-encoded.*',
            r'net.*user.*\/add',
            r'reg.*add.*hklm',
            r'schtasks.*\/create',
            r'wmic.*process.*call.*create',
            r'certutil.*-decode'
        ]
    }
    
    print(" TESTING PATTERN MATCHING")
    print("=" * 40)
    print(f"Test message: {test_message}")
    print()
    
    threat_score = 0.0
    indicators = []
    
    for category, patterns in threat_patterns.items():
        print(f"Testing {category}:")
        for pattern in patterns:
            if re.search(pattern, test_message, re.IGNORECASE):
                threat_score += 0.3
                indicators.append(f"{category}: {pattern}")
                print(f"   MATCH: {pattern}")
            else:
                print(f"   No match: {pattern}")
    
    print(f"\nFinal Results:")
    print(f"  Threat Score: {threat_score}")
    print(f"  Indicators: {indicators}")
    print(f"  Threat Detected: {threat_score > 0.3}")
    
    if threat_score > 0.3:
        print("🚨 MALICIOUS ACTIVITY DETECTED!")
    else:
        print(" No threats detected")

if __name__ == "__main__":
    test_threat_patterns()
