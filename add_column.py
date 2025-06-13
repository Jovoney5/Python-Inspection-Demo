import sqlite3

conn = sqlite3.connect('inspections.db')
c = conn.cursor()

# Add inspector_signature column if it doesn't exist
try:
    c.execute("ALTER TABLE inspections ADD COLUMN inspector_signature TEXT DEFAULT ''")
    conn.commit()
    print("Column 'inspector_signature' added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column 'inspector_signature' already exists. No action taken.")
    else:
        print(f"Error: {e}")
finally:
    conn.close()