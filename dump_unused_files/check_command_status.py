import sqlite3

conn = sqlite3.connect('soc_database.db')
cursor = conn.cursor()

print("=== COMMAND STATUS SUMMARY ===")

# Check command statuses
try:
    cursor.execute('SELECT status, COUNT(*) FROM commands GROUP BY status')
    statuses = cursor.fetchall()
    print("Command Status Counts:")
    for status, count in statuses:
        print(f"  {status}: {count}")
except Exception as e:
    print(f"Error checking command statuses: {e}")

print()

# Check for execution results
try:
    cursor.execute('SELECT COUNT(*) FROM command_results')
    result_count = cursor.fetchone()[0]
    print(f"Total execution results: {result_count}")
    
    if result_count > 0:
        cursor.execute('SELECT command_id, agent_id, success, output FROM command_results ORDER BY created_at DESC LIMIT 5')
        results = cursor.fetchall()
        print("\nRecent execution results:")
        for i, (cmd_id, agent_id, success, output) in enumerate(results, 1):
            print(f"  {i}. Command: {cmd_id}")
            print(f"     Agent: {agent_id}")
            print(f"     Success: {success}")
            if output:
                output_preview = str(output)[:100].replace('\n', ' | ')
                print(f"     Output: {output_preview}...")
            print()
except Exception as e:
    print(f"Error checking execution results: {e}")

print()

# Check recent commands
try:
    cursor.execute('SELECT agent_id, technique, status, created_at FROM commands ORDER BY created_at DESC LIMIT 5')
    commands = cursor.fetchall()
    print("Recent commands:")
    for i, (agent_id, technique, status, created_at) in enumerate(commands, 1):
        print(f"  {i}. Agent: {agent_id}")
        print(f"     Technique: {technique}")
        print(f"     Status: {status}")
        print(f"     Created: {created_at}")
        print()
except Exception as e:
    print(f"Error checking recent commands: {e}")

conn.close()
