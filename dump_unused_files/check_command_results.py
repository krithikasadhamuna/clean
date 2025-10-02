import sqlite3

conn = sqlite3.connect('soc_database.db')
cursor = conn.cursor()

print("=" * 80)
print("COMMAND EXECUTION RESULTS")
print("=" * 80)

cursor.execute('''
    SELECT command_id, success, execution_time_ms, output 
    FROM command_results 
    WHERE agent_id = 'MinKri_ec11c1e5'
    ORDER BY rowid DESC 
    LIMIT 5
''')

results = cursor.fetchall()

if results:
    print(f"Found {len(results)} command results:")
    print()
    for cmd_id, success, exec_time, output in results:
        print(f"Command ID: {cmd_id}")
        print(f"Success: {'Yes' if success else 'No'}")
        if exec_time:
            print(f"Execution Time: {exec_time}ms")
        if output:
            output_preview = output[:100] + ('...' if len(output) > 100 else '')
            print(f"Output: {output_preview}")
        print("-" * 40)
else:
    print("No command results found")

# Also check commands status
print("\n" + "=" * 80)
print("COMMAND STATUS UPDATE")
print("=" * 80)

cursor.execute('''
    SELECT id, technique, status 
    FROM commands 
    WHERE agent_id = 'MinKri_ec11c1e5' 
    ORDER BY rowid DESC 
    LIMIT 5
''')

commands = cursor.fetchall()

if commands:
    print(f"Command status:")
    for cmd_id, technique, status in commands:
        print(f"  - {technique}: {status} (ID: {cmd_id[:16]}...)")
else:
    print("No commands found")

conn.close()
