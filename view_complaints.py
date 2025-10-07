import sqlite3
import json

conn = sqlite3.connect("complaints.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM complaints")  # or your table name
rows = cursor.fetchall()

columns = [desc[0] for desc in cursor.description]

for row in rows:
    print(json.dumps(dict(zip(columns, row)), default=str, indent=2))

conn.close()
