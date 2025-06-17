import sqlite3

conn = sqlite3.connect('inspections.db')
c = conn.cursor()
c.execute("PRAGMA table_info(messages)")
columns = c.fetchall()
print("Messages table columns:", [col[1] for col in columns])
conn.close()