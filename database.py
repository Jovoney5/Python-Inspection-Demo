import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  establishment_name TEXT,
                  address TEXT,
                  inspector_name TEXT,
                  inspection_date TEXT,
                  inspection_time TEXT,
                  type_of_establishment TEXT,
                  comments TEXT,
                  inspector_signature TEXT,
                  manager_signature TEXT,
                  manager_date TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  physical_location TEXT,
                  owner TEXT,
                  license_no TEXT,
                  no_of_employees TEXT,
                  purpose_of_visit TEXT,
                  action TEXT,
                  result TEXT,
                  food_inspected TEXT,
                  food_condemned TEXT,
                  critical_score INTEGER,
                  overall_score INTEGER,
                  received_by TEXT,
                  form_type TEXT,
                  scores TEXT,
                  inspector_code TEXT)''')

    # Inspection items table
    c.execute('''CREATE TABLE IF NOT EXISTS inspection_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  inspection_id INTEGER,
                  item_id TEXT,
                  details TEXT,
                  obser TEXT,
                  error TEXT,
                  FOREIGN KEY (inspection_id) REFERENCES inspections(id))''')

    # Burial site inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS burial_site_inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  inspection_date TEXT,
                  applicant_name TEXT,
                  deceased_name TEXT,
                  burial_location TEXT,
                  site_description TEXT,
                  proximity_water_source TEXT,
                  proximity_perimeter_boundaries TEXT,
                  proximity_road_pathway TEXT,
                  proximity_trees TEXT,
                  proximity_houses_buildings TEXT,
                  proposed_grave_type TEXT,
                  general_remarks TEXT,
                  inspector_signature TEXT,
                  received_by TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Residential inspections table
    c.execute('''CREATE TABLE IF NOT EXISTS residential_inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  premises_name TEXT,
                  owner TEXT,
                  address TEXT,
                  inspector_name TEXT,
                  inspection_date TEXT,
                  inspector_code TEXT,
                  treatment_facility TEXT,
                  vector TEXT,
                  result TEXT,
                  onsite_system TEXT,
                  building_construction_type TEXT,
                  purpose_of_visit TEXT,
                  action TEXT,
                  no_of_bedrooms TEXT,
                  total_population TEXT,
                  critical_score INTEGER,
                  overall_score INTEGER,
                  comments TEXT,
                  inspector_signature TEXT,
                  received_by TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Residential checklist scores table
    c.execute('''CREATE TABLE IF NOT EXISTS residential_checklist_scores
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  form_id INTEGER,
                  item_id INTEGER,
                  score INTEGER,
                  FOREIGN KEY (form_id) REFERENCES residential_inspections(id))''')

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL)''')

    # Insert users
    users = [
        ('inspector1', 'Insp123!secure', 'inspector'),
        ('inspector2', 'Insp456!secure', 'inspector'),
        ('inspector3', 'Insp789!secure', 'inspector'),
        ('inspector4', 'Insp012!secure', 'inspector'),
        ('inspector5', 'Insp345!secure', 'inspector'),
        ('inspector6', 'Insp678!secure', 'inspector'),
        ('admin', 'Admin901!secure', 'admin')
    ]
    c.executemany("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", users)

    # Contacts table
    c.execute('''CREATE TABLE IF NOT EXISTS contacts
                 (user_id INTEGER,
                  contact_id INTEGER,
                  PRIMARY KEY (user_id, contact_id),
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (contact_id) REFERENCES users(id))''')

    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER NOT NULL,
                  receiver_id INTEGER NOT NULL,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  is_read INTEGER DEFAULT 0,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')

    # Add is_read column if it doesn't exist
    try:
        c.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Set existing messages as read
    c.execute("UPDATE messages SET is_read = 1 WHERE is_read IS NULL")

    conn.commit()
    conn.close()

def save_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('''INSERT INTO inspections (establishment_name, address, inspector_name, inspection_date, inspection_time, 
                 type_of_establishment, no_of_employees, purpose_of_visit, action, result, food_inspected, food_condemned, 
                 critical_score, overall_score, comments, inspector_signature, received_by, form_type, scores, created_at, 
                 inspector_code, license_no, owner)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['establishment_name'], data['address'], data['inspector_name'], data['inspection_date'],
               data['inspection_time'], data['type_of_establishment'], data['no_of_employees'],
               data['purpose_of_visit'], data['action'], data['result'], data['food_inspected'],
               data['food_condemned'], data['critical_score'], data['overall_score'], data['comments'],
               data['inspector_signature'], data['received_by'], data['form_type'], data['scores'],
               data['created_at'], data['inspector_code'], data['license_no'], data['owner']))
    conn.commit()
    inspection_id = c.lastrowid
    conn.close()
    return inspection_id

def save_burial_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    try:
        if data.get('id'):
            c.execute('''UPDATE burial_site_inspections SET 
                         inspection_date = ?, applicant_name = ?, deceased_name = ?, burial_location = ?, 
                         site_description = ?, proximity_water_source = ?, proximity_perimeter_boundaries = ?, 
                         proximity_road_pathway = ?, proximity_trees = ?, proximity_houses_buildings = ?, 
                         proposed_grave_type = ?, general_remarks = ?, inspector_signature = ?, 
                         received_by = ?, created_at = ?
                         WHERE id = ?''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                       data['id']))
        else:
            c.execute('''INSERT INTO burial_site_inspections (inspection_date, applicant_name, deceased_name, burial_location, 
                        site_description, proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway, 
                        proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks, 
                        inspector_signature, received_by, created_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
                       data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
                       data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
                       data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
                       data['received_by'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def save_residential_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    try:
        if data.get('id'):
            c.execute("""
                            UPDATE residential_inspections 
                            SET premises_name = ?, owner = ?, address = ?, inspector_name = ?,
                                inspection_date = ?, inspector_code = ?, treatment_facility = ?, vector = ?,
                                result = ?, onsite_system = ?, building_construction_type = ?, purpose_of_visit = ?,
                                action = ?, no_of_bedrooms = ?, total_population = ?, critical_score = ?,
                                overall_score = ?, comments = ?, inspector_signature = ?, received_by = ?,
                                created_at = ?
                            WHERE id = ?
                        """,
                        (data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                         data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                         data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                         data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                         data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                         data['inspector_signature'], data['received_by'],
                         data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')), data['id']))
        else:
            c.execute("""
                INSERT INTO residential_inspections (
                    premises_name, owner, address, inspector_name,
                    inspection_date, inspector_code, treatment_facility, vector, result, onsite_system,
                    building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population,
                    critical_score, overall_score, comments, inspector_signature, received_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['premises_name'], data['owner'], data['address'], data['inspector_name'],
                data['inspection_date'], data['inspector_code'], data['treatment_facility'], data['vector'],
                data['result'], data['onsite_system'], data['building_construction_type'], data['purpose_of_visit'],
                data['action'], data.get('no_of_bedrooms', ''), data.get('total_population', ''),
                data.get('critical_score', 0), data.get('overall_score', 0), data['comments'],
                data['inspector_signature'], data['received_by'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()

        inspection_id = c.lastrowid if not data.get('id') else data['id']
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        inspection_id = None
    finally:
        conn.close()
    return inspection_id

def get_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, inspector_name, inspection_date, type_of_establishment, created_at, result FROM inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_burial_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, applicant_name, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_residential_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, premises_name, inspection_date, result FROM residential_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()

    if inspection:
        if inspection[24] == 'Food Establishment':
            scores = [int(x) for x in inspection[25].split(',')] if inspection[25] else [0] * 45
            inspection_dict = {
                'id': inspection[0],
                'establishment_name': inspection[1] or '',
                'address': inspection[2] or '',
                'inspector_name': inspection[3] or '',
                'inspection_date': inspection[4] or '',
                'inspection_time': inspection[5] or '',
                'type_of_establishment': inspection[6] or '',
                'comments': inspection[7] or '',
                'inspector_signature': inspection[8] or '',
                'manager_signature': inspection[9] or '',
                'manager_date': inspection[10] or '',
                'created_at': inspection[11] or '',
                'physical_location': inspection[12] or '',
                'owner': inspection[13] or '',
                'license_no': inspection[14] or '',
                'no_of_employees': inspection[15] or '',
                'purpose_of_visit': inspection[16] or '',
                'action': inspection[17] or '',
                'result': inspection[18] or '',
                'food_inspected': inspection[19] or '',
                'food_condemned': inspection[20] or '',
                'critical_score': inspection[21] or 0,
                'overall_score': inspection[22] or 0,
                'received_by': inspection[23] or '',
                'form_type': inspection[24] or '',
                'scores': dict(zip(range(1, 46), scores)),
                'inspector_code': inspection[26] or ''
            }
        else:
            c.execute("SELECT item_id, details, obser, error FROM inspection_items WHERE inspection_id = ?", (inspection_id,))
            items = c.fetchall()
            scores = {int(item[0]): item[1] for item in items if item[1]}
            inspection_dict = {
                'id': inspection[0],
                'establishment_name': inspection[1] or '',
                'address': inspection[2] or '',
                'inspector_name': inspection[3] or '',
                'inspection_date': inspection[4] or '',
                'inspection_time': inspection[5] or '',
                'type_of_establishment': inspection[6] or '',
                'comments': inspection[7] or '',
                'inspector_signature': inspection[8] or '',
                'manager_signature': inspection[9] or '',
                'manager_date': inspection[10] or '',
                'created_at': inspection[11] or '',
                'physical_location': inspection[12] or '',
                'owner': inspection[13] or '',
                'license_no': inspection[14] or '',
                'no_of_employees': inspection[15] or '',
                'purpose_of_visit': inspection[16] or '',
                'action': inspection[17] or '',
                'result': inspection[18] or '',
                'food_inspected': inspection[19] or '',
                'food_condemned': inspection[20] or '',
                'critical_score': inspection[21] or 0,
                'overall_score': inspection[22] or 0,
                'received_by': inspection[23] or '',
                'form_type': inspection[24] or '',
                'scores': scores,
                'inspector_code': inspection[26] or ''
            }
        conn.close()
        return inspection_dict
    conn.close()
    return None

def get_burial_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()
    conn.close()
    if inspection:
        return {
            'id': inspection[0],
            'inspection_date': inspection[1] or '',
            'applicant_name': inspection[2] or '',
            'deceased_name': inspection[3] or '',
            'burial_location': inspection[4] or '',
            'site_description': inspection[5] or '',
            'proximity_water_source': inspection[6] or '',
            'proximity_perimeter_boundaries': inspection[7] or '',
            'proximity_road_pathway': inspection[8] or '',
            'proximity_trees': inspection[9] or '',
            'proximity_houses_buildings': inspection[10] or '',
            'proposed_grave_type': inspection[11] or '',
            'general_remarks': inspection[12] or '',
            'inspector_signature': inspection[13] or '',
            'received_by': inspection[14] or '',
            'created_at': inspection[15] or ''
        }
    return None

def get_residential_inspection_details(inspection_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM residential_inspections WHERE id = ?", (inspection_id,))
    inspection = c.fetchone()
    if inspection:
        c.execute("SELECT item_id, score FROM residential_checklist_scores WHERE form_id = ?", (inspection_id,))
        checklist_scores = dict(c.fetchall())
        conn.close()
        return {
            'id': inspection[0],
            'premises_name': inspection[1] or '',
            'owner': inspection[2] or '',
            'address': inspection[3] or '',
            'inspector_name': inspection[4] or '',
            'inspection_date': inspection[5] or '',
            'inspector_code': inspection[6] or '',
            'treatment_facility': inspection[7] or '',
            'vector': inspection[8] or '',
            'result': inspection[9] or '',
            'onsite_system': inspection[10] or '',
            'building_construction_type': inspection[11] or '',
            'purpose_of_visit': inspection[12] or '',
            'action': inspection[13] or '',
            'no_of_bedrooms': inspection[14] or '',
            'total_population': inspection[15] or '',
            'critical_score': inspection[16] or 0,
            'overall_score': inspection[17] or 0,
            'comments': inspection[18] or '',
            'inspector_signature': inspection[19] or '',
            'received_by': inspection[20] or '',
            'created_at': inspection[21] or '',
            'checklist_scores': checklist_scores
        }
    conn.close()
    return None

if __name__ == "__main__":
    init_db()