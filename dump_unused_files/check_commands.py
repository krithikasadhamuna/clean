import sqlite3
import json

conn = sqlite3.connect('soc_database.db')
cursor = conn.cursor()

# Get recent commands
cursor.execute('SELECT agent_id, technique, command_data, status, created_at FROM commands WHERE status = "queued" LIMIT 5')
commands = cursor.fetchall()

print("Recent Queued Commands:")
print("=" * 80)
for i, (agent_id, technique, command_data, status, created_at) in enumerate(commands, 1):
    print(f"{i}. Agent: {agent_id}")
    print(f"   Technique: {technique}")
    print(f"   Status: {status}")
    print(f"   Created: {created_at}")
    
    # Parse command data
    try:
        data = json.loads(command_data)
        print(f"   Command Data:")
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"     {key}: {json.dumps(value, indent=6)}")
            else:
                print(f"     {key}: {value}")
    except:
        print(f"   Command Data: {command_data}")
    print()

conn.close()