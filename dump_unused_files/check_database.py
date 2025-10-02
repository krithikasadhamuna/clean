import sqlite3

conn = sqlite3.connect('soc_database.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Get agent table schema
if 'agents' in tables:
    cursor.execute("PRAGMA table_info(agents)")
    columns = [(row[1], row[2]) for row in cursor.fetchall()]
    print("\nAgents table columns:", columns)
    
    # Get all agents
    cursor.execute("SELECT * FROM agents LIMIT 5")
    agents = cursor.fetchall()
    print(f"\nFound {len(agents)} agents")
    for agent in agents:
        print(f"  Agent: {agent}")

conn.close()