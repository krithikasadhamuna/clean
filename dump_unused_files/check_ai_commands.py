import sqlite3
import json

conn = sqlite3.connect('soc_database.db')
cursor = conn.cursor()

# Get latest AI-generated commands
cursor.execute('SELECT agent_id, technique, command_data FROM commands WHERE technique = "T1018" ORDER BY created_at DESC LIMIT 3')
commands = cursor.fetchall()

print("Latest AI-Generated Commands:")
print("=" * 60)

for i, (agent_id, technique, command_data_str) in enumerate(commands, 1):
    print(f"{i}. Agent: {agent_id}")
    print(f"   Technique: {technique}")
    
    try:
        command_data = json.loads(command_data_str)
        print(f"   Command Type: {command_data.get('command_type', 'unknown')}")
        print(f"   Description: {command_data.get('description', 'No description')}")
        print(f"   Script Preview:")
        script = command_data.get('script', 'No script')
        # Show first few lines
        lines = script.split('\n')[:5]
        for line in lines:
            print(f"     {line}")
        if len(script.split('\n')) > 5:
            print("     ...")
    except:
        print(f"   Raw Data: {command_data_str[:100]}...")
    
    print()

conn.close()
