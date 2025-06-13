def update_database():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("ALTER TABLE residential_inspections ADD COLUMN received_by TEXT")
    c.execute("UPDATE residential_inspections SET received_by = 'N/A' WHERE received_by IS NULL")
    conn.commit()
    conn.close()

update_database()