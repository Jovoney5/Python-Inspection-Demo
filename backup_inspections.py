import sqlite3

conn = sqlite3.connect('inspections.db')
c = conn.cursor()
c.execute("SELECT * FROM inspections")
with open('inspections_backup.csv', 'w') as f:
    column_names = [description[0] for description in c.description]
    f.write(','.join(column_names) + '\n')
    for row in c.fetchall():
        f.write(','.join(str(item) for item in row) + '\n')
conn.close()
print("Backup created as 'inspections_backup.csv'")