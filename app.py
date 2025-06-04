from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database import init_db, save_inspection, get_inspections, save_burial_inspection, get_burial_inspections
import os
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Checklist for Food Establishment Inspection Form
FOOD_CHECKLIST_ITEMS = [
    {"id": 1, "desc": "Source, Sound Condition, No Spoilage", "wt": 5},
    {"id": 2, "desc": "Original Container, Properly Labeled", "wt": 1},
    {"id": 3,
     "desc": "Potentially Hazardous Food Meets Temperature Requirements During Storage, Preparation, Display, Service, Transportation",
     "wt": 5},
    {"id": 4, "desc": "Facilities to Maintain Product Temperature", "wt": 4},
    {"id": 5, "desc": "Thermometers Provided and Conspicuous", "wt": 1},
    {"id": 6, "desc": "Potentially Hazardous Food Properly Thawed", "wt": 2},
    {"id": 7, "desc": "Unwrapped and Potentially Hazardous Food Not Re-Served", "wt": 4},
    {"id": 8, "desc": "Food Protection During Storage, Preparation, Display, Service, Transportation", "wt": 2},
    {"id": 9, "desc": "Handling of Food (Ice) Minimized", "wt": 1},
    {"id": 10, "desc": "In Use Food (Ice) Dispensing Utensils Properly Stored", "wt": 1},
    {"id": 11, "desc": "Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 2},
    {"id": 12, "desc": "Non-Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 1},
    {"id": 13, "desc": "Dishwashing Facilities Designed, Constructed, Maintained, Installed, Located, Operated",
     "wt": 2},
    {"id": 14, "desc": "Accurate Thermometers, Chemical Test Kits Provided", "wt": 1},
    {"id": 15, "desc": "Single Service Articles Storage, Dispensing", "wt": 1},
    {"id": 16, "desc": "No Re-Use of Single Serve Articles", "wt": 2},
    {"id": 17, "desc": "Pre-Flushed, Scraped, Soaked", "wt": 1},
    {"id": 18, "desc": "Wash, Rinse Water Clean, Proper Temperature", "wt": 2},
    {"id": 19,
     "desc": "Sanitization Rinse Clean, Temperature, Concentration, Exposure Time, Equipment, Utensils Sanitized",
     "wt": 4},
    {"id": 20, "desc": "Wiping Cloths Clean, Use Restricted", "wt": 1},
    {"id": 21, "desc": "Food Contact Surfaces of Equipment and Utensils Clean, Free of Abrasives, Detergents", "wt": 2},
    {"id": 22, "desc": "Non-Food Contact Surfaces of Equipment and Utensils Clean", "wt": 1},
    {"id": 23, "desc": "Storage Condition, Handled", "wt": 1},
    {"id": 24, "desc": "Number Convenient, Accessible, Designed, Install", "wt": 4},
    {"id": 25,
     "desc": "Toilet Rooms Enclosed, Self-Closing Doors, Fixtures: Good Repair, Clean, Hand Cleanser, Sanitary Towels, Hand Drying Devices Cleaned, Proper Lined Receptacles",
     "wt": 7},
    {"id": 26, "desc": "Containers or Receptacles: Covered Adequate Number, Insect/Rodent Proof, Frequency, Cleaned",
     "wt": 2},
    {"id": 27, "desc": "Outside Storage Area, Enclosures Properly Constructed, Clean, Controlled Incineration",
     "wt": 1},
    {"id": 28, "desc": "Evidence of Insects/Rodents- Outer Openings, protected, No birds, Turtles, Other animals",
     "wt": 4},
    {"id": 29, "desc": "Personnel with Infections Restricted", "wt": 5},
    {"id": 30, "desc": "Hands Washed and Clean Good Hygienic Practices", "wt": 5},
    {"id": 31, "desc": "Clean Clothes, Hair Restraints", "wt": 1},
    {"id": 32, "desc": "All employees with valid permits", "wt": 1},
    {"id": 33, "desc": "Lighting Provided as Required, Fixtures Shielded", "wt": 1},
    {"id": 34, "desc": "Rooms and Equipment - Venting as Required ", "wt": 1},
    {"id": 35, "desc": "Rooms Clean, Lockers Provided, Facilities Clean", "wt": 1},
    {"id": 36, "desc": "Water source Safe, Hot & Cold Under Pressure", "wt": 5},
    {"id": 37, "desc": "Sewage and Waste Water Disposal", "wt": 4},
    {"id": 38, "desc": "Installed, Maintained", "wt": 1},
    {"id": 39, "desc": "cross Connection, Back Siphonage, Backflow", "wt": 5},
    {"id": 40,
     "desc": "Floors Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Method",
     "wt": 1},
    {"id": 41,
     "desc": "Walls, Ceiling, Attached Equipment Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods",
     "wt": 1},
    {"id": 42, "desc": "Toxic Items Properly Stored, Labeled, Used", "wt": 5},
    {"id": 43,
     "desc": "Premises Maintained free of Liter, Unnecessary Articles, Cleaning Maintenance Equipment Properly stored, Authorized Personnel",
     "wt": 1},
    {"id": 44, "desc": "Complete Separation for living /Sleeping Quarters, Laundry", "wt": 1},
    {"id": 45, "desc": "Clean, Soiled Linen Properly Stored", "wt": 1},
]

# Checklist for Residential & Non-Residential Inspection Form
RESIDENTIAL_CHECKLIST_ITEMS = [
    {"id": 1, "desc": "Sound and clean exterior of building", "wt": 3},
    {"id": 2, "desc": "Sound and clean interior of building", "wt": 3},
    {"id": 3, "desc": "Sound and clean floors", "wt": 2},
    {"id": 4, "desc": "Sound and clean walls", "wt": 2},
    {"id": 5, "desc": "Sound and clean ceiling", "wt": 2},
    {"id": 6, "desc": "Adequate ventilation in rooms", "wt": 3},
    {"id": 7, "desc": "Sufficient lighting", "wt": 2},
    {"id": 8, "desc": "Adequate accommodation", "wt": 4},
    {"id": 9, "desc": "Potability", "wt": 6},
    {"id": 10, "desc": "Accessibility", "wt": 4},
    {"id": 11, "desc": "Graded", "wt": 4},
    {"id": 12, "desc": "Unobstructed", "wt": 6},
    {"id": 13, "desc": "No active breeding", "wt": 5},
    {"id": 14, "desc": "No potential breeding source", "wt": 5},
    {"id": 15, "desc": "No active breeding", "wt": 5},
    {"id": 16, "desc": "No potential breeding source", "wt": 5},
    {"id": 17, "desc": "No active breeding", "wt": 3},
    {"id": 18, "desc": "No potential breeding source", "wt": 3},
    {"id": 19, "desc": "Clean", "wt": 4},
    {"id": 20, "desc": "Safe and sound", "wt": 5},
    {"id": 21, "desc": "Fly/rodentproof", "wt": 4},
    {"id": 22, "desc": "Adequate health and safety provisions", "wt": 4},
    {"id": 23, "desc": "Storage", "wt": 4},
    {"id": 24, "desc": "Disposal", "wt": 4},
    {"id": 25, "desc": "Proper lairage for animals, Controlled vegetation", "wt": 4},
]

SPIRIT_LICENCE_CHECKLIST_ITEMS = [
    {'id': 1, 'description': 'Sound, clean and in good repair', 'wt': 3},
    {'id': 2, 'description': 'No smoking sign displayed at entrance to premises', 'wt': 3},
    {'id': 3, 'description': 'Walls, clean and in good repair', 'wt': 3},
    {'id': 4, 'description': 'Floors', 'wt': 3},
    {'id': 5, 'description': 'Constructed of impervious, non-slip material', 'wt': 3},
    {'id': 6, 'description': 'Clean, drained and in good repair', 'wt': 3},
    {'id': 7, 'description': 'Service counter', 'wt': 3},
    {'id': 8, 'description': 'Constructed of impervious material', 'wt': 3},
    {'id': 9, 'description': 'Designed, clean and in good repair', 'wt': 3},
    {'id': 10, 'description': 'Lighting', 'wt': 3},
    {'id': 11, 'description': 'Lighting provided as required', 'wt': 3},
    {'id': 12, 'description': 'Washing and Sanitization Facilities', 'wt': 5},
    {'id': 13, 'description': 'Fitted with at least double compartment sink', 'wt': 5},
    {'id': 14, 'description': 'Soap and sanitizer provided', 'wt': 5},
    {'id': 15, 'description': 'Equipped handwashing facility provided', 'wt': 5},
    {'id': 16, 'description': 'Water Supply', 'wt': 5},
    {'id': 17, 'description': 'Potable', 'wt': 5},
    {'id': 18, 'description': 'Piped', 'wt': 5},
    {'id': 19, 'description': 'Storage Facilities', 'wt': 5},
    {'id': 20, 'description': 'Clean and adequate storage of glasses & utensils', 'wt': 5},
    {'id': 21, 'description': 'Free of insects and other vermins', 'wt': 5},
    {'id': 22, 'description': 'Being used for its intended purpose', 'wt': 5},
    {'id': 23, 'description': 'Sanitary Facilities', 'wt': 5},
    {'id': 24, 'description': 'Toilet facility provided', 'wt': 5},
    {'id': 25, 'description': 'Adequate, accessible with lavatory basin and soap', 'wt': 5},
    {'id': 26, 'description': 'Satisfactory', 'wt': 5},
    {'id': 27, 'description': 'Urinal(s) provided', 'wt': 3},
    {'id': 28, 'description': 'Satisfactory', 'wt': 3},
    {'id': 29, 'description': 'Solid Waste Management', 'wt': 4},
    {'id': 30, 'description': 'Covered, adequate, pest proof and clean receptacles', 'wt': 4},
    {'id': 31, 'description': 'Provision made for satisfactory disposal of waste', 'wt': 3},
    {'id': 32, 'description': 'Premises free of litter and unnecessary articles', 'wt': 3},
    {'id': 33, 'description': 'Pest Control', 'wt': 5},
    {'id': 34, 'description': 'Premises free of rodents, insects and vermins', 'wt': 5}
]

# Checklist for Swimming Pool Inspection Form
SWIMMING_POOL_CHECKLIST_ITEMS = [
    {"id": "1a", "desc": "Written procedures for microbiological monitoring of pool water implemented", "wt": 5,
     "category": "Documentation"},
    {"id": "1d", "desc": "Acceptable monitoring procedures", "wt": 5, "category": "Documentation"},
    {"id": "1f", "desc": "Written emergency procedures established and implemented", "wt": 5,
     "category": "Documentation"},
    {"id": "1g", "desc": "Personal liability and accident insurance", "wt": 5, "category": "Documentation"},
    {"id": "1h", "desc": "Lifeguard/Lifesaver certification", "wt": 5, "category": "Documentation"},
    {"id": "2c", "desc": "All surfaces of the deck and pool free from obstruction that can cause accident/injury",
     "wt": 5, "category": "Physical Condition"},
    {"id": "2g", "desc": "Perimeter drains free of debris", "wt": 5, "category": "Physical Condition"},
    {"id": "3a", "desc": "Clarity", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3b", "desc": "Chlorine residual > 0.5 mg/l", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3c", "desc": "pH value within range of 7.5 and 7.8", "wt": 5, "category": "Pool Chemistry"},
    {"id": "4a", "desc": "Pool chemicals - stored safely", "wt": 5, "category": "Pool Chemicals"},
    {"id": "4b", "desc": "Dispensed automatically or in a safe manner", "wt": 5, "category": "Pool Chemicals"},
    {"id": "5b", "desc": "Vented", "wt": 5, "category": "Sanitary Facilities"},
    {"id": "6a", "desc": "Reaching poles with hook", "wt": 5, "category": "Safety"},
    {"id": "6b", "desc": "Two throwing aids", "wt": 5, "category": "Safety"},
    {"id": "6c", "desc": "Spine board with cervical collar", "wt": 5, "category": "Safety"},
    {"id": "6d", "desc": "Well equipped first aid kit", "wt": 5, "category": "Safety"},
    {"id": "7a", "desc": "Caution notices - pool depth indications", "wt": 5, "category": "Signs and Notices"},
    {"id": "7b", "desc": "Public health notices", "wt": 5, "category": "Signs and Notices"},
    {"id": "8a", "desc": "Licence/Lifeguards always on duty during pool opening hours", "wt": 5,
     "category": "Lifeguards/Lifesavers"},
    {"id": "8b", "desc": "Trained lifesavers readily available", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "9a", "desc": "Pool drained and cleaned monthly", "wt": 5, "category": "Additional Requirements"},
]


def get_establishment_data():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT establishment_name, owner, license_no, id FROM inspections")
    data = c.fetchall()
    conn.close()
    return data


@app.route('/')
def login():
    if 'inspector' in session:
        return render_template('dashboard.html', inspections=get_inspections(),
                               burial_inspections=get_burial_inspections())
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    if username == 'inspector' and password == 'password123':
        session['inspector'] = True
        return redirect(url_for('login'))
    return render_template('login.html', error='Invalid credentials')


@app.route('/logout')
def logout():
    session.pop('inspector', None)
    return redirect(url_for('login'))


@app.route('/new_form')
def new_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('inspection_form.html', checklist=FOOD_CHECKLIST_ITEMS, inspections=get_inspections(),
                           show_form=True, establishment_data=get_establishment_data())


@app.route('/new_residential_form')
def new_residential_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('residential_form.html', checklist=RESIDENTIAL_CHECKLIST_ITEMS,
                           inspections=get_inspections(),
                           show_form=True, establishment_data=get_establishment_data())


@app.route('/new_burial_form')
def new_burial_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('burial_form.html', inspections=get_inspections(),
                           burial_inspections=get_burial_inspections())


@app.route('/new_water_supply_form')
def new_water_supply_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('water_supply_form.html', checklist=WATER_SUPPLY_CHECKLIST_ITEMS,
                           inspections=get_inspections())


@app.route('/new_spirit_licence_form')
def new_spirit_licence_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('spirit_licence_form.html', checklist=SPIRIT_LICENCE_CHECKLIST_ITEMS,
                           inspections=get_inspections())


@app.route('/new_swimming_pool_form')
def new_swimming_pool_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    # Default inspection object for pre-population
    inspection = {
        'id': '',
        'establishment_name': '',
        'address': '',
        'physical_location': '',
        'type_of_establishment': '',
        'inspector_name': '',
        'inspection_date': '',
        'inspection_time': '',
        'result': '',
        'overall_score': 0,
        'critical_score': 0,
        'comments': '',
        'inspector_signature': '',
        'inspector_date': '',
        'manager_signature': '',
        'manager_date': '',
        'scores': {item['id']: 0 for item in SWIMMING_POOL_CHECKLIST_ITEMS}
    }
    return render_template('swimming_pool_form.html', checklist=SWIMMING_POOL_CHECKLIST_ITEMS, inspections=get_inspections(), inspection=inspection)

@app.route('/submit_spirit_licence', methods=['POST'])
def submit_spirit_licence():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    data = {
        'establishment_name': request.form['establishment_name'],
        'owner': request.form['owner_operator'],
        'address': request.form['address'],
        'license_no': '13697',  # Hardcoded from image
        'inspector_name': request.form['inspector_name'],
        'inspection_date': request.form['inspection_date'],
        'inspection_time': '',
        'type_of_establishment': request.form['type_of_establishment'],
        'purpose_of_visit': request.form['purpose_of_visit'],
        'action': '',
        'result': 'Pass' if (sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if
                                 int(request.form.get(f"score_{i}", 0)) > 0) >= 70 and
                             sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if
                                 SPIRIT_LICENCE_CHECKLIST_ITEMS[i - 1]['wt'] >= 4 and int(
                                     request.form.get(f"score_{i}", 0)) > 0) >= 59) else 'Fail',
        'comments': '\n'.join(
            [f"{SPIRIT_LICENCE_CHECKLIST_ITEMS[i - 1]['description']}: {request.form.get(f'comment_{i}', '')}" for i in
             range(1, 35)]),
        'inspector_signature': request.form['inspector_signature'],
        'recieved_by': request.form['received_by'],
        'scores': ','.join([request.form.get(f"score_{i}", '0') for i in range(1, 35)]),
        'form_type': 'Spirit Licence Premises',
        'no_of_employees': request.form['no_of_employees'],
        'no_with_fhc': request.form['no_with_fhc'],
        'no_wo_fhc': request.form['no_wo_fhc'],
        'status': request.form['status'],
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    overall_score = sum(
        int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if int(request.form.get(f"score_{i}", 0)) > 0)
    data['overall_score'] = overall_score
    data['critical_score'] = sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if
                                 SPIRIT_LICENCE_CHECKLIST_ITEMS[i - 1]['wt'] >= 4 and int(
                                     request.form.get(f"score_{i}", 0)) > 0)
    save_inspection(data)
    return render_template('spirit_licence_form.html', checklist=SPIRIT_LICENCE_CHECKLIST_ITEMS,
                           inspections=get_inspections(),
                           success=True)


@app.route('/spirit_licence/inspection/<int:id>')
def spirit_licence_inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute(
        "SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, created_at, form_type, no_of_employees, no_with_fhc, no_wo_fhc, status FROM inspections WHERE id = ?",
        (id,))
    inspection = c.fetchone()
    conn.close()
    if inspection:
        scores = [int(x) for x in inspection[12].split(',')]
        inspection_data = {
            'id': inspection[0],
            'establishment_name': inspection[1],
            'owner': inspection[2],
            'address': inspection[3],
            'license_no': inspection[4],
            'inspector_name': inspection[5],
            'inspection_date': inspection[6],
            'inspection_time': inspection[7],
            'type_of_establishment': inspection[8],
            'purpose_of_visit': inspection[9],
            'action': inspection[10],
            'result': inspection[11],
            'scores': dict(zip([item['id'] for item in SPIRIT_LICENCE_CHECKLIST_ITEMS], scores)),
            'comments': inspection[13],
            'inspector_signature': inspection[5],
            'recieved_by': inspection[1],
            'overall_score': sum(score for score in scores if score > 0),
            'critical_score': sum(
                score for item, score in zip(SPIRIT_LICENCE_CHECKLIST_ITEMS, scores) if item['wt'] >= 4 and score > 0),
            'form_type': inspection[15],
            'no_of_employees': inspection[16],
            'no_with_fhc': inspection[17],
            'no_wo_fhc': inspection[18],
            'status': inspection[19],
            'created_at': inspection[14]
        }
        return render_template('spirit_licence_inspection_detail.html', checklist=SPIRIT_LICENCE_CHECKLIST_ITEMS,
                               inspection=inspection_data)
    return "Not Found", 404


@app.route('/submit', methods=['POST'])
def submit():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    data = {
        'establishment_name': request.form['establishment_name'],
        'owner': request.form['owner'],
        'address': request.form['address'],
        'license_no': request.form['license_no'],
        'inspector_name': request.form['inspector_name'],
        'inspection_date': request.form['inspection_date'],
        'inspection_time': request.form['inspection_time'],
        'type_of_establishment': request.form['type_of_establishment'],
        'purpose_of_visit': request.form['purpose_of_visit'],
        'action': request.form['action'],
        'result': 'Pass' if (sum(int(request.form.get(f"score_{item['id']}", 0)) for item in FOOD_CHECKLIST_ITEMS if
                                 int(request.form.get(f"score_{item['id']}", 0)) > 0) >= 70 and
                             sum(int(request.form.get(f"score_{item['id']}", 0)) for item in FOOD_CHECKLIST_ITEMS if
                                 item['wt'] >= 4 and int(
                                     request.form.get(f"score_{item['id']}", 0)) > 0) >= 59) else 'Fail',
        'comments': request.form['comments'],
        'inspector_signature': request.form['inspector_signature'],
        'recieved_by': request.form['recieved_by'],
        'scores': [],
        'form_type': 'Food Establishment',
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    overall_score = 0
    for item in FOOD_CHECKLIST_ITEMS:
        score = int(request.form.get(f"score_{item['id']}", 0))
        data['scores'].append(score)
        if score > 0:
            overall_score += score
    data['overall_score'] = overall_score
    data['critical_score'] = sum(
        score for item, score in zip(FOOD_CHECKLIST_ITEMS, data['scores']) if item['wt'] >= 4 and score > 0)
    save_inspection(data)
    return render_template('inspection_form.html', checklist=FOOD_CHECKLIST_ITEMS, inspections=get_inspections(),
                           show_form=True, success=True, establishment_data=get_establishment_data())


@app.route('/submit_residential', methods=['POST'])
def submit_residential():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    data = {
        'establishment_name': request.form['premises_name'],
        'owner': request.form['owner'],
        'address': request.form['address'],
        'license_no': '',
        'inspector_name': request.form['inspector_name'],
        'inspection_date': request.form['inspection_date'],
        'inspection_time': '',
        'type_of_establishment': request.form['treatment_facility'],
        'purpose_of_visit': request.form['purpose_of_visit'],
        'action': request.form['action'],
        'result': 'Pass' if (sum(
            int(request.form.get(f"score_{item['id']}", 0)) for item in RESIDENTIAL_CHECKLIST_ITEMS if
            int(request.form.get(f"score_{item['id']}", 0)) > 0) >= 70 and
                             sum(int(request.form.get(f"score_{item['id']}", 0)) for item in RESIDENTIAL_CHECKLIST_ITEMS
                                 if item['wt'] >= 4 and int(
                                 request.form.get(f"score_{item['id']}", 0)) > 0) >= 59) else 'Fail',
        'comments': request.form['comments'],
        'inspector_signature': request.form['inspector_signature'],
        'recieved_by': request.form['recieved_by'],
        'scores': [],
        'form_type': 'Residential & Non-Residential',
        'inspector_code': request.form.get('inspector_code', ''),
        'vector': request.form.get('vector', ''),
        'onsite_system': request.form.get('onsite_system', ''),
        'building_construction_type': request.form.get('building_construction_type', ''),
        'no_of_bedrooms': request.form.get('no_of_bedrooms', ''),
        'total_population': request.form.get('total_population', ''),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    overall_score = 0
    for item in RESIDENTIAL_CHECKLIST_ITEMS:
        score = int(request.form.get(f"score_{item['id']}", 0))
        data['scores'].append(score)
        if score > 0:
            overall_score += score
    data['overall_score'] = overall_score
    data['critical_score'] = sum(
        score for item, score in zip(RESIDENTIAL_CHECKLIST_ITEMS, data['scores']) if item['wt'] >= 4 and score > 0)
    save_inspection(data)
    return render_template('residential_form.html', checklist=RESIDENTIAL_CHECKLIST_ITEMS,
                           inspections=get_inspections(),
                           show_form=True, success=True, establishment_data=get_establishment_data())


@app.route('/submit_burial', methods=['POST'])
def submit_burial():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    data = {
        'inspection_date': request.form['inspection_date'],
        'applicant_name': request.form['applicant_name'],
        'deceased_name': request.form['deceased_name'],
        'burial_location': request.form['burial_location'],
        'site_description': request.form['site_description'],
        'proximity_water_source': request.form['proximity_water_source'] or '0',
        'proximity_perimeter_boundaries': request.form['proximity_perimeter_boundaries'] or '0',
        'proximity_road_pathway': request.form['proximity_road_pathway'] or '0',
        'proximity_trees': request.form['proximity_trees'] or '0',
        'proximity_houses_buildings': request.form['proximity_houses_buildings'] or '0',
        'proposed_grave_type': request.form['proposed_grave_type'],
        'general_remarks': request.form['general_remarks'] or '',
        'inspector_signature': request.form['inspector_signature'],
        'received_by': request.form['received_by'],
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'form_type': 'Burial Site'
    }
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
    return render_template('burial_form.html', inspections=get_inspections(),
                           burial_inspections=get_burial_inspections(),
                           success=True)


@app.route('/submit_swimming_pools', methods=['POST'])
def submit_swimming_pools():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Collect form data
    data = {
        'establishment_name': request.form['operator'],
        'owner': '',
        'address': request.form['address'],
        'license_no': '',
        'inspector_name': request.form['inspector_id'],  # Using inspector_id as inspector_name for consistency
        'inspection_date': request.form['date_inspection'],
        'inspection_time': datetime.datetime.now().strftime('%H:%M:%S'),
        'type_of_establishment': request.form['pool_class'],
        'purpose_of_visit': '',
        'action': '',
        'result': '',
        'scores': [],
        'comments': request.form['inspector_comments'],
        'form_type': 'Swimming Pool',
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'physical_location': request.form['physical_location'],
        'inspector_signature': request.form['inspector_signature'],
        'inspector_date': request.form['inspector_date'],
        'manager_signature': request.form['manager_signature'],
        'manager_date': request.form['manager_date'],
    }

    # Calculate scores
    overall_score = 0
    critical_score = 0
    scores_dict = {}

    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        item_id = item['id']
        yes_key = f"result_{item_id}_yes"
        no_key = f"result_{item_id}_no"

        score = 0
        if yes_key in request.form:
            score = item['wt']
            overall_score += score
            if item['wt'] >= 5:  # All critical items have weight 5
                critical_score += score
        scores_dict[item_id] = score

    data['scores'] = [scores_dict.get(item['id'], 0) for item in SWIMMING_POOL_CHECKLIST_ITEMS]
    data['overall_score'] = overall_score
    data['critical_score'] = critical_score
    data['result'] = 'Pass' if (
                overall_score >= 70 and critical_score >= 55) else 'Fail'  # Adjusted threshold for 22 items

    # Save to database
    save_inspection(data)
    return render_template('swimming_pool_form.html', checklist=SWIMMING_POOL_CHECKLIST_ITEMS,
                           inspections=get_inspections(), success=True)


@app.route('/stats')
def stats():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspections = get_inspections()
    burial_inspections = get_burial_inspections()
    return jsonify({
        'total': len(inspections) + len(burial_inspections),
        'food': len([i for i in inspections if i['form_type'] == 'Food Establishment']),
        'residential': len([i for i in inspections if i['form_type'] == 'Residential & Non-Residential']),
        'burial': len(burial_inspections),
        'spirit_licence': len([i for i in inspections if i['form_type'] == 'Spirit Licence Premises']),
        'swimming_pool': len([i for i in inspections if i['form_type'] == 'Swimming Pool'])
    })


@app.route('/search', methods=['GET'])
def search():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '').lower()
    data = get_establishment_data()
    burial_data = []
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, applicant_name, deceased_name FROM burial_site_inspections")
    burial_records = c.fetchall()
    conn.close()
    suggestions = []
    for establishment_name, owner, license_no, id in data:
        if query in (establishment_name or '').lower() or query in (owner or '').lower() or query in (
                license_no or '').lower():
            suggestions.append(
                {'text': f"{establishment_name} (Owner: {owner}, License: {license_no})", 'id': id, 'type': 'food'})
    for id, applicant_name, deceased_name in burial_records:
        if query in (applicant_name or '').lower() or query in (deceased_name or '').lower():
            suggestions.append({'text': f"{deceased_name} (Applicant: {applicant_name})", 'id': id, 'type': 'burial'})
    return jsonify({'suggestions': suggestions})


@app.route('/search_forms', methods=['GET'])
def search_forms():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    query = request.args.get('query', '').lower()
    form_type = request.args.get('type', '')
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    forms = []

    if form_type == 'food':
        c.execute(
            "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Food Establishment' AND (establishment_name LIKE ? OR owner LIKE ?)",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3]
            })
    elif form_type == 'residential':
        c.execute(
            "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Residential & Non-Residential' AND (establishment_name LIKE ? OR owner LIKE ?)",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3]
            })
    elif form_type == 'burial':
        c.execute(
            "SELECT id, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections WHERE deceased_name LIKE ? OR applicant_name LIKE ?",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'deceased_name': record[1],
                'created_at': record[2],
                'status': record[3]
            })
    elif form_type == 'water_supply':
        c.execute(
            "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Water Supply' AND (establishment_name LIKE ? OR owner LIKE ?)",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3]
            })
    elif form_type == 'spirit_licence':
        c.execute(
            "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Spirit Licence Premises' AND (establishment_name LIKE ? OR owner LIKE ?)",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3]
            })
    elif form_type == 'swimming_pool':
        c.execute(
            "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Swimming Pool' AND (establishment_name LIKE ? OR address LIKE ?)",
            (f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3]
            })

    conn.close()
    return jsonify({'forms': forms})


@app.route('/inspection/<int:id>')
def inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute(
        "SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, created_at, form_type, inspector_code, vector, onsite_system, building_construction_type, no_of_bedrooms, total_population, no_of_employees, no_with_fhc, no_wo_fhc, status FROM inspections WHERE id = ?",
        (id,))
    inspection = c.fetchone()
    if inspection:
        checklist_items = FOOD_CHECKLIST_ITEMS if inspection[
                                                      15] == 'Food Establishment' else RESIDENTIAL_CHECKLIST_ITEMS if \
        inspection[15] == 'Residential & Non-Residential' else SPIRIT_LICENCE_CHECKLIST_ITEMS if inspection[
                                                                                                     15] == 'Spirit Licence Premises' else WATER_SUPPLY_CHECKLIST_ITEMS if \
        inspection[15] == 'Water Supply' else SWIMMING_POOL_CHECKLIST_ITEMS
        scores = [int(x) for x in inspection[12].split(',')]
        inspection_data = {
            'id': inspection[0],
            'establishment_name': inspection[1],
            'owner': inspection[2],
            'address': inspection[3],
            'license_no': inspection[4],
            'inspector_name': inspection[5],
            'inspection_date': inspection[6],
            'inspection_time': inspection[7],
            'type_of_establishment': inspection[8],
            'purpose_of_visit': inspection[9],
            'action': inspection[10],
            'result': inspection[11],
            'scores': dict(zip([item['id'] for item in checklist_items], scores)),
            'comments': inspection[13],
            'inspector_signature': inspection[5],
            'recieved_by': inspection[1],
            'overall_score': sum(score for score in scores if score > 0),
            'critical_score': sum(
                score for item, score in zip(checklist_items, scores) if item['wt'] >= 4 and score > 0),
            'food_inspected': 0.0,
            'food_condemned': 0.0,
            'form_type': inspection[15],
            'inspector_code': inspection[16] if len(inspection) > 16 else '',
            'vector': inspection[17] if len(inspection) > 17 else '',
            'onsite_system': inspection[18] if len(inspection) > 18 else '',
            'building_construction_type': inspection[19] if len(inspection) > 19 else '',
            'no_of_bedrooms': inspection[20] if len(inspection) > 20 else '',
            'total_population': inspection[21] if len(inspection) > 21 else '',
            'no_of_employees': inspection[22] if len(inspection) > 22 else '',
            'no_with_fhc': inspection[23] if len(inspection) > 23 else '',
            'no_wo_fhc': inspection[24] if len(inspection) > 24 else '',
            'status': inspection[25] if len(inspection) > 25 else '',
            'created_at': inspection[14],
            'physical_location': inspection[3] if len(inspection) > 3 else '',  # Fallback to address
            'inspector_date': '',
            'manager_signature': '',
            'manager_date': ''
        }
        template = 'inspection_detail.html' if inspection[15] in ['Food Establishment', 'Residential & Non-Residential',
                                                                  'Water Supply'] else 'spirit_licence_inspection_detail.html' if \
        inspection[15] == 'Spirit Licence Premises' else 'swimming_pool_inspection_detail.html'
        return render_template(template, checklist=checklist_items, inspection=inspection_data)
    else:
        c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (id,))
        inspection = c.fetchone()
        conn.close()
        if inspection:
            inspection_data = {
                'id': inspection[0],
                'inspection_date': inspection[1],
                'applicant_name': inspection[2],
                'deceased_name': inspection[3],
                'burial_location': inspection[4],
                'site_description': inspection[5],
                'proximity_water_source': inspection[6],
                'proximity_perimeter_boundaries': inspection[7],
                'proximity_road_pathway': inspection[8],
                'proximity_trees': inspection[9],
                'proximity_houses_buildings': inspection[10],
                'proposed_grave_type': inspection[11],
                'general_remarks': inspection[12],
                'inspector_signature': inspection[13],
                'received_by': inspection[14],
                'created_at': inspection[15]
            }
            return render_template('burial_inspection_detail.html', inspection=inspection_data)
        return "Not Found", 404


@app.route('/burial/inspection/<int:id>')
def burial_inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (id,))
    inspection = c.fetchone()
    conn.close()
    if not inspection:
        return "Not Found", 404
    inspection_data = {
        'id': inspection[0],
        'inspection_date': inspection[1],
        'applicant_name': inspection[2],
        'deceased_name': inspection[3],
        'burial_location': inspection[4],
        'site_description': inspection[5],
        'proximity_water_source': inspection[6],
        'proximity_perimeter_boundaries': inspection[7],
        'proximity_road_pathway': inspection[8],
        'proximity_trees': inspection[9],
        'proximity_houses_buildings': inspection[10],
        'proposed_grave_type': inspection[11],
        'general_remarks': inspection[12],
        'inspector_signature': inspection[13],
        'received_by': inspection[14],
        'created_at': inspection[15]
    }
    return render_template('burial_inspection_detail.html', inspection=inspection_data)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)