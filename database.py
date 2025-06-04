import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  establishment_name TEXT,
                  owner TEXT,
                  address TEXT,
                  license_no TEXT,
                  inspector_name TEXT,
                  inspection_date TEXT,
                  inspection_time TEXT,
                  type_of_establishment TEXT,
                  purpose_of_visit TEXT,
                  action TEXT,
                  result TEXT,
                  scores TEXT,
                  comments TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  form_type TEXT,
                  inspector_code TEXT,
                  vector TEXT,
                  onsite_system TEXT,
                  building_construction_type TEXT,
                  no_of_bedrooms TEXT,
                  total_population TEXT,
                  physical_location TEXT,
                  inspector_signature TEXT,
                  inspector_date TEXT,
                  manager_signature TEXT,
                  manager_date TEXT)''')
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
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('''INSERT INTO inspections (establishment_name, owner, address, license_no, inspector_name, 
                 inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, 
                 scores, comments, created_at, form_type, inspector_code, vector, onsite_system, 
                 building_construction_type, no_of_bedrooms, total_population, physical_location, 
                 inspector_signature, inspector_date, manager_signature, manager_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['establishment_name'], data['owner'], data['address'], data['license_no'], data['inspector_name'],
               data['inspection_date'], data['inspection_time'], data['type_of_establishment'], data['purpose_of_visit'],
               data['action'], data['result'], ','.join(map(str, data['scores'])), data['comments'],
               data.get('created_at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), data['form_type'],
               data.get('inspector_code', ''), data.get('vector', ''), data.get('onsite_system', ''),
               data.get('building_construction_type', ''), data.get('no_of_bedrooms', ''), data.get('total_population', ''),
               data.get('physical_location', ''), data.get('inspector_signature', ''), data.get('inspector_date', ''),
               data.get('manager_signature', ''), data.get('manager_date', '')))
    conn.commit()
    conn.close()

def save_burial_inspection(data):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute('''INSERT INTO burial_site_inspections (inspection_date, applicant_name, deceased_name, burial_location, 
                site_description, proximity_water_source, proximity_perimeter_boundaries, proximity_road_pathway, 
                proximity_trees, proximity_houses_buildings, proposed_grave_type, general_remarks, 
                inspector_signature, received_by, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (data['inspection_date'], data['applicant_name'], data['deceased_name'], data['burial_location'],
               data['site_description'], data['proximity_water_source'], data['proximity_perimeter_boundaries'],
               data['proximity_road_pathway'], data['proximity_trees'], data['proximity_houses_buildings'],
               data['proposed_grave_type'], data['general_remarks'], data['inspector_signature'],
               data['received_by'], data['created_at']))
    conn.commit()
    conn.close()

def get_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, owner, license_no, created_at, result, form_type FROM inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections

def get_burial_inspections():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, deceased_name, created_at FROM burial_site_inspections")
    inspections = c.fetchall()
    conn.close()
    return inspections