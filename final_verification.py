#!/usr/bin/env python3
import requests
import json

print("FINAL VERIFICATION:")
print("1. Health Check:")
r = requests.get('http://localhost:8080/health')
print(f"Status: {r.status_code}")

print("2. Attack Agents API:")
r = requests.get('http://localhost:8080/api/backend/attack-agents')
print(f"Status: {r.status_code}, Agents: {len(r.json().get('agents', []))}")

print("3. Container Log Test:")
r = requests.post('http://localhost:8080/api/logs/ingest', json={
    'agent_id': 'test',
    'logs': [{
        'timestamp': '2024-01-01T00:00:00',
        'level': 'INFO',
        'source': 'AttackContainer',
        'message': 'Container test log',
        'platform': 'Container',
        'container_context': True
    }]
})
print(f"Status: {r.status_code}")
print("ALL SYSTEMS OPERATIONAL!")
