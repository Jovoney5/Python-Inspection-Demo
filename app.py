from datetime import datetime
from database import get_residential_inspection_details, get_residential_inspections, init_db, save_residential_inspection, save_inspection, save_burial_inspection, get_inspections, get_burial_inspections, get_inspection_details, get_burial_inspection_details
from database import get_inspection_details
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import sqlite3
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Checklist for Food Establishment Inspection Form
FOOD_CHECKLIST_ITEMS = [
    {"id": 1, "desc": "Source, Sound Condition, No Spoilage", "wt": 5},
    {"id": 2, "desc": "Original Container, Properly Labeled", "wt": 1},
    {"id": 3, "desc": "Potentially Hazardous Food Meets Temperature Requirements During Storage, Preparation, Display, Service, Transportation", "wt": 5},
    {"id": 4, "desc": "Facilities to Maintain Product Temperature", "wt": 4},
    {"id": 5, "desc": "Thermometers Provided and Conspicuous", "wt": 1},
    {"id": 6, "desc": "Potentially Hazardous Food Properly Thawed", "wt": 2},
    {"id": 7, "desc": "Unwrapped and Potentially Hazardous Food Not Re-Served", "wt": 4},
    {"id": 8, "desc": "Food Protection During Storage, Preparation, Display, Service, Transportation", "wt": 2},
    {"id": 9, "desc": "Handling of Food (Ice) Minimized", "wt": 1},
    {"id": 10, "desc": "In Use Food (Ice) Dispensing Utensils Properly Stored", "wt": 1},
    {"id": 11, "desc": "Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 2},
    {"id": 12, "desc": "Non-Food Contact Surfaces Designed, Constructed, Maintained, Installed, Located", "wt": 1},
    {"id": 13, "desc": "Dishwashing Facilities Designed, Constructed, Maintained, Installed, Located, Operated", "wt": 2},
    {"id": 14, "desc": "Accurate Thermometers, Chemical Test Kits Provided", "wt": 1},
    {"id": 15, "desc": "Single Service Articles Storage, Dispensing", "wt": 1},
    {"id": 16, "desc": "No Re-Use of Single Serve Articles", "wt": 2},
    {"id": 17, "desc": "Pre-Flushed, Scraped, Soaked", "wt": 1},
    {"id": 18, "desc": "Wash, Rinse Water Clean, Proper Temperature", "wt": 2},
    {"id": 19, "desc": "Sanitization Rinse Clean, Temperature, Concentration, Exposure Time, Equipment, Utensils Sanitized", "wt": 4},
    {"id": 20, "desc": "Wiping Cloths Clean, Use Restricted", "wt": 1},
    {"id": 21, "desc": "Food Contact Surfaces of Equipment and Utensils Clean, Free of Abrasives, Detergents", "wt": 2},
    {"id": 22, "desc": "Non-Food Contact Surfaces of Equipment and Utensils Clean", "wt": 1},
    {"id": 23, "desc": "Storage Condition, Handled", "wt": 1},
    {"id": 24, "desc": "Number Convenient, Accessible, Designed, Install", "wt": 4},
    {"id": 25, "desc": "Toilet Rooms Enclosed, Self-Closing Doors, Fixtures: Good Repair, Clean, Hand Cleanser, Sanitary Towels, Hand Drying Devices Cleaned, Proper Lined Receptacles", "wt": 5},
    {"id": 26, "desc": "Containers or Receptacles: Covered Adequate Number, Insect/Rodent Proof, Frequency, Cleaned", "wt": 2},
    {"id": 27, "desc": "Outside Storage Area, Enclosures Properly Constructed, Clean, Controlled Incineration", "wt": 1},
    {"id": 28, "desc": "Evidence of Insects/Rodents- Outer Openings, protected, No birds, Turtles, Other animals", "wt": 4},
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
    {"id": 40, "desc": "Floors Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Method", "wt": 1},
    {"id": 41, "desc": "Walls, Ceiling, Attached Equipment Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods", "wt": 1},
    {"id": 42, "desc": "Toxic Items Properly Stored, Labeled, Used", "wt": 5},
    {"id": 43, "desc": "Premises Maintained free of Liter, Unnecessary Articles, Cleaning Maintenance Equipment Properly stored, Authorized Personnel", "wt": 1},
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

# Swimming Pool Checklist
SWIMMING_POOL_CHECKLIST_ITEMS = [
    {"id": "1a", "desc": "Written procedures for microbiological monitoring of pool water implemented", "wt": 5, "category": "Documentation"},
    {"id": "1b", "desc": "Microbiological results", "wt": 5, "category": "Documentation"},
    {"id": "1c", "desc": "Date of last testing within required frequency", "wt": 5, "category": "Documentation"},
    {"id": "1d", "desc": "Acceptable monitoring procedures", "wt": 5, "category": "Documentation"},
    {"id": "1e", "desc": "Daily log books and records up-to-date", "wt": 5, "category": "Documentation"},
    {"id": "1f", "desc": "Written emergency procedures established and implemented", "wt": 5, "category": "Documentation"},
    {"id": "1g", "desc": "Personal liability and accident insurance", "wt": 5, "category": "Documentation"},
    {"id": "1h", "desc": "Lifeguard/Lifesaver certification", "wt": 5, "category": "Documentation"},
    {"id": "2a", "desc": "Defects in pool construction", "wt": 5, "category": "Physical Condition"},
    {"id": "2b", "desc": "Evidence of flaking paint and/or mould growth", "wt": 5, "category": "Physical Condition"},
    {"id": "2c", "desc": "All surfaces of the deck and pool free from obstruction that can cause accident/injury", "wt": 5, "category": "Physical Condition"},
    {"id": "2d", "desc": "Exposed piping: - identified/colour coded", "wt": 5, "category": "Physical Condition"},
    {"id": "2e", "desc": "In good repair", "wt": 5, "category": "Physical Condition"},
    {"id": "2f", "desc": "Suction fittings/inlets: - in good repair", "wt": 5, "category": "Physical Condition"},
    {"id": "2g", "desc": "At least two suction orifices equipped with anti-entrapment devices", "wt": 5, "category": "Physical Condition"},
    {"id": "2h", "desc": "Perimeter drains free of debris", "wt": 5, "category": "Physical Condition"},
    {"id": "2i", "desc": "Pool walls and floor clean", "wt": 5, "category": "Physical Condition"},
    {"id": "2j", "desc": "Components of the re-circulating system maintained", "wt": 5, "category": "Physical Condition"},
    {"id": "3a", "desc": "Clarity", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3b", "desc": "Chlorine residual > 0.5 mg/l", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3c", "desc": "pH value within range of 7.5 and 7.8", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3d", "desc": "Well supplied and equipped", "wt": 5, "category": "Pool Chemistry"},
    {"id": "4a", "desc": "Pool chemicals - stored safely", "wt": 5, "category": "Pool Chemicals"},
    {"id": "4b", "desc": "Dispensed automatically or in a safe manner", "wt": 5, "category": "Pool Chemicals"},
    {"id": "5a", "desc": "Depth markings clearly visible", "wt": 5, "category": "Safety"},
    {"id": "5b", "desc": "Working emergency phone", "wt": 5, "category": "Safety"},
    {"id": "6a", "desc": "Reaching poles with hook", "wt": 5, "category": "Safety Aids"},
    {"id": "6b", "desc": "Two throwing aids", "wt": 5, "category": "Safety Aids"},
    {"id": "6c", "desc": "Spine board with cervical collar", "wt": 5, "category": "Safety Aids"},
    {"id": "6d", "desc": "Well equipped first aid kit", "wt": 5, "category": "Safety Aids"},
    {"id": "7a", "desc": "Caution notices: - pool depth indications", "wt": 5, "category": "Signs and Notices"},
    {"id": "7b", "desc": "Public health notices", "wt": 5, "category": "Signs and Notices"},
    {"id": "7c", "desc": "Emergency procedures", "wt": 5, "category": "Signs and Notices"},
    {"id": "7d", "desc": "Maximum bathing load", "wt": 5, "category": "Signs and Notices"},
    {"id": "7e", "desc": "Lifeguard on duty/bathe at your own risk signs", "wt": 5, "category": "Signs and Notices"},
    {"id": "8a", "desc": "Licensed Lifeguards always on duty during pool opening hours", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "8b", "desc": "If N/A, trained lifesavers readily available", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "8c", "desc": "Number of lifeguard/lifesavers", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "9a", "desc": "Shower, toilet and dressing rooms: - clean and disinfected as required", "wt": 5, "category": "Sanitary Facilities"},
    {"id": "9b", "desc": "Vented", "wt": 5, "category": "Sanitary Facilities"},
    {"id": "9c", "desc": "Well supplied and equipped", "wt": 5, "category": "Sanitary Facilities"},
]

# Define checklist items (40 items, 28 critical)
SMALL_HOTELS_CHECKLIST_ITEMS = [
    {"id": "1a", "description": "Action plan for foodborne illness", "critical": False},
    {"id": "1b", "description": "Food Handlers permits", "critical": False},
    {"id": "1c", "description": "Policy to restrict sick employees", "critical": False},
    {"id": "1d", "description": "Waste disposal policy", "critical": False},
    {"id": "1e", "description": "Cleaning schedule", "critical": False},
    {"id": "1f", "description": "Material safety data sheet", "critical": False},
    {"id": "1g", "description": "Hazardous chemicals record", "critical": False},
    {"id": "1h", "description": "Food suppliers list", "critical": False},
    {"id": "2a", "description": "Protective garments", "critical": True},
    {"id": "2b", "description": "Hands free of jewellery", "critical": False},
    {"id": "2c", "description": "Hair restraints", "critical": False},
    {"id": "2d", "description": "Nails clean", "critical": False},
    {"id": "2e", "description": "Hands washed", "critical": True},
    {"id": "3a", "description": "Approved source", "critical": True},
    {"id": "3b", "description": "Correct stocking procedures", "critical": False},
    {"id": "3c", "description": "Food stored off floor", "critical": False},
    {"id": "3d", "description": "No animals in store", "critical": True},
    {"id": "3e", "description": "Products free of infestation", "critical": False},
    {"id": "3f", "description": "No pesticides in food stores", "critical": True},
    {"id": "3g", "description": "Refrigeration condition", "critical": False},
    {"id": "3h", "description": "Refrigerated foods < 4°C", "critical": True},
    {"id": "3i", "description": "Frozen foods -18°C", "critical": True},
    {"id": "4a", "description": "Foods thawed properly", "critical": True},
    {"id": "4b", "description": "No cross-contamination during prep", "critical": True},
    {"id": "4c", "description": "No cross-contamination in coolers", "critical": True},
    {"id": "4d", "description": "Foods cooled properly", "critical": True},
    {"id": "4e", "description": "Manual dishwashing", "critical": True},
    {"id": "4f", "description": "Food surfaces sanitized", "critical": False},
    {"id": "5a", "description": "Waste container design", "critical": True},
    {"id": "5c", "description": "Waste containers emptied", "critical": True},
    {"id": "6a", "description": "Vermin-proof waste containers", "critical": True},
    {"id": "8a", "description": "Hazardous materials labelled", "critical": True},
    {"id": "8b", "description": "Hazardous materials stored safely", "critical": True},
    {"id": "9a", "description": "Food protected during transport", "critical": True},
    {"id": "9b", "description": "Dishes labelled", "critical": True},
    {"id": "9c", "description": "Food protected from contamination", "critical": True},
    {"id": "10a", "description": "Hand washing facility installed", "critical": True},
    {"id": "10b", "description": "Hand washing equipped", "critical": True},
    {"id": "12b", "description": "Food surfaces smooth", "critical": True},
    {"id": "12c", "description": "Utensils stored properly", "critical": True},
    {"id": "13a", "description": "Employee traffic pattern", "critical": True},
    {"id": "13b", "description": "Product flow safe", "critical": True},
    {"id": "15a", "description": "Approved sewage system", "critical": True},
    {"id": "16a", "description": "Water source approved", "critical": True},
    {"id": "16b", "description": "Water quality satisfactory", "critical": True},
]
# ... (Other checklists omitted as per your request; paste them back if needed)

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
        return render_template('dashboard.html', inspections=get_inspections(), burial_inspections=get_burial_inspections())
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    login_type = request.form['login_type']

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, username, password, role FROM users WHERE username = ? AND password = ?",
              (username, password))
    user = c.fetchone()
    conn.close()

    if user and (
            (login_type == 'inspector' and user[3] == 'inspector') or (login_type == 'admin' and user[3] == 'admin')):
        session['user_id'] = user[0]
        session[login_type] = True
        if login_type == 'inspector':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('admin'))
    return render_template('login.html', error='Invalid credentials')


@app.route('/admin')
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, form_type, inspector_name, created_at, establishment_name, result
        FROM inspections
        WHERE form_type IN ('Food Establishment', 'Spirit Licence Premises', 'Swimming Pool', 'Small Hotel')
        UNION
        SELECT id, 'Residential' AS form_type, inspector_name, created_at, premises_name, result
        FROM residential_inspections
        UNION
        SELECT id, 'Burial' AS form_type, '' AS inspector_name, created_at, applicant_name, 'Completed' AS result
        FROM burial_site_inspections
    """)
    forms = c.fetchall()
    conn.close()
    return render_template('admin.html', forms=forms)


@app.route('/admin_metrics', methods=['GET'])
def admin_metrics():
    form_type = request.args.get('form_type', 'all')
    time_frame = request.args.get('time_frame', 'daily')
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    if form_type == 'all':
        query = """
            SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
            FROM (
                SELECT created_at, result FROM inspections
                WHERE form_type IN ('Food Establishment', 'Spirit Licence Premises', 'Swimming Pool', 'Small Hotel')
                UNION
                SELECT created_at, result FROM residential_inspections
                UNION
                SELECT created_at, 'Completed' AS result FROM burial_site_inspections
            )
            GROUP BY date, result
        """
    else:
        if form_type == 'Residential':
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
                FROM residential_inspections
                GROUP BY date, result
            """
        elif form_type == 'Burial':
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, 'Completed' AS result, COUNT(*) AS count
                FROM burial_site_inspections
                GROUP BY date, result
            """
        else:
            query = """
                SELECT strftime('%Y-%m-%d', created_at) AS date, result, COUNT(*) AS count
                FROM inspections
                WHERE form_type = ?
                GROUP BY date, result
            """
            c.execute(query, (form_type,))
            results = c.fetchall()
            conn.close()
            return jsonify(process_metrics(results, time_frame))

    c.execute(query)
    results = c.fetchall()
    conn.close()
    return jsonify(process_metrics(results, time_frame))


def process_metrics(results, time_frame):
    data = {'dates': [], 'pass': [], 'fail': []}
    date_format = '%Y-%m-%d' if time_frame == 'daily' else '%Y-%m' if time_frame == 'monthly' else '%Y'

    for date, result, count in results:
        formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime(date_format)
        if formatted_date not in data['dates']:
            data['dates'].append(formatted_date)
            data['pass'].append(0)
            data['fail'].append(0)

        idx = data['dates'].index(formatted_date)
        if result == 'Pass' or result == 'Completed':
            data['pass'][idx] += count
        else:
            data['fail'][idx] += count

    return data

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect to login page

@app.route('/new_form')
def new_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    # Default inspection data for new form
    inspection = {
        'id': '',
        'establishment_name': '',
        'owner': '',
        'address': '',
        'license_no': '',
        'inspector_name': '',
        'inspector_code': '',
        'inspection_date': '',
        'inspection_time': '',
        'type_of_establishment': '',
        'no_of_employees': '',
        'purpose_of_visit': '',
        'action': '',
        'result': '',
        'food_inspected': 0.0,
        'food_condemned': 0.0,
        'critical_score': 0,
        'overall_score': 0,
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {},
        'created_at': ''
    }
    return render_template('inspection_form.html', checklist=FOOD_CHECKLIST_ITEMS, inspections=get_inspections(), show_form=True, establishment_data=get_establishment_data(), read_only=False, inspection=inspection)


@app.route('/new_residential_form')
def new_residential_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('residential_form.html', checklist=RESIDENTIAL_CHECKLIST_ITEMS, inspections=get_residential_inspections(), show_form=True, establishment_data=get_establishment_data())

@app.route('/new_burial_form')
def new_burial_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspection_id = request.args.get('id')
    if inspection_id:
        conn = sqlite3.connect('inspections.db')
        c = conn.cursor()
        c.execute("SELECT * FROM burial_site_inspections WHERE id = ?", (inspection_id,))
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
            return render_template('burial_form.html', inspection=inspection_data)
    return render_template('burial_form.html', inspection=None)

@app.route('/new_water_supply_form')
def new_water_supply_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    return render_template('water_supply_form.html', checklist=[], inspections=get_inspections())

@app.route('/new_spirit_licence_form')
def new_spirit_licence_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    # Default inspection data for new form
    inspection = {
        'id': '',
        'establishment_name': '',
        'owner': '',
        'address': '',
        'license_no': '13697',  # Default license number per submit route
        'inspector_name': session.get('inspector', 'Inspector'),
        'inspection_date': datetime.now().strftime('%Y-%m-%d'),
        'inspection_time': '',
        'type_of_establishment': 'Spirit Licence Premises',
        'no_of_employees': '',
        'no_with_fhc': '',
        'no_wo_fhc': '',
        'status': '',
        'purpose_of_visit': '',
        'action': '',
        'result': '',
        'critical_score': 0,
        'overall_score': 0,
        'comments': '',
        'inspector_signature': '',
        'received_by': '',
        'scores': {},
        'created_at': ''
    }
    return render_template('spirit_licence_form.html', checklist=SPIRIT_LICENCE_CHECKLIST_ITEMS, inspections=get_inspections(), show_form=True, establishment_data=get_establishment_data(), read_only=False, inspection=inspection)

@app.route('/new_swimming_pool_form')
def new_swimming_pool_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
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
        'scores': {}
    }
    return render_template('swimming_pool_form.html', checklist=SWIMMING_POOL_CHECKLIST_ITEMS, inspections=get_inspections(), inspection=inspection)

@app.route('/new_small_hotels_form')
def new_small_hotels_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('small_hotels_form.html', checklist_items=SMALL_HOTELS_CHECKLIST_ITEMS, today=today)


@app.route('/submit_spirit_licence', methods=['POST'])
def submit_spirit_licence():
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401
    data = {
        'establishment_name': request.form.get('establishment_name', ''),
        'owner': request.form.get('owner_operator', ''),
        'address': request.form.get('address', ''),
        'license_no': '13697',
        'inspector_name': request.form.get('inspector_name', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'inspection_time': '',
        'type_of_establishment': request.form.get('type_of_establishment', 'Spirit Licence Premises'),
        'purpose_of_visit': request.form.get('purpose_of_visit', ''),
        'action': '',
        'result': 'Pass' if (sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if int(request.form.get(f"score_{i}", 0)) > 0) >= 70 and
                             sum(int(request.form.get(f"score_{i}", 0)) for i in [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 33, 34] if int(request.form.get(f"score_{i}", 0)) > 0) >= 59) else 'Fail',
        'comments': '\n'.join([f"{i}: {request.form.get(f'comment_{i}', '')}" for i in range(1, 35)]),
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', ''),
        'scores': ','.join([request.form.get(f"score_{i}", '0') for i in range(1, 35)]),
        'form_type': 'Spirit Licence Premises',
        'no_of_employees': request.form.get('no_of_employees', ''),
        'no_with_fhc': request.form.get('no_with_fhc', ''),
        'no_wo_fhc': request.form.get('no_wo_fhc', ''),
        'status': request.form.get('status', ''),
        'food_inspected': 0.0,
        'food_condemned': 0.0,
        'inspector_code': '',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    overall_score = sum(int(request.form.get(f"score_{i}", 0)) for i in range(1, 35) if int(request.form.get(f"score_{i}", 0)) > 0)
    data['overall_score'] = overall_score
    critical_score = sum(int(request.form.get(f"score_{i}", 0)) for i in [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 33, 34] if int(request.form.get(f"score_{i}", 0)) > 0)
    data['critical_score'] = critical_score
    try:
        inspection_id = save_inspection(data)
        conn = sqlite3.connect('inspections.db')
        c = conn.cursor()
        for item in SPIRIT_LICENCE_CHECKLIST_ITEMS:
            score = request.form.get(f"score_{item['id']}", '0')
            c.execute("INSERT INTO inspection_items (inspection_id, item_id, details) VALUES (?, ?, ?)",
                      (inspection_id, item['id'], score))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Submit Successfully'})
    except sqlite3.Error as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/spirit_licence/inspection/<int:id>')
def spirit_licence_inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, created_at, form_type, no_of_employees, no_with_fhc, no_wo_fhc, status FROM inspections WHERE id = ?", (id,))
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
            'scores': dict(zip(range(1, 35), scores)),
            'comments': inspection[13],
            'inspector_signature': inspection[5],
            'received_by': inspection[2],
            'overall_score': sum(score for score in scores if score > 0),
            'critical_score': sum(score for i, score in enumerate(scores, 1) if 0 and score > 0),
            'form_type': inspection[15],
            'no_of_employees': inspection[16],
            'no_with_fhc': inspection[17],
            'no_wo_fhc': inspection[18],
            'status': inspection[19],
            'created_at': inspection[14]
        }
        return render_template('spirit_licence_inspection_detail.html', checklist=[], inspection=inspection_data)
    return "Not Found", 404


@app.route('/submit/<form_type>', methods=['POST'])
def submit_form(form_type):
    if 'inspector' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 403
    try:
        if form_type == 'inspection':
            data = {
                'establishment_name': request.form.get('establishment_name'),
                'address': request.form.get('address'),
                'owner': request.form.get('owner'),
                'license_no': request.form.get('license_no'),
                'inspector_name': request.form.get('inspector_name'),
                'inspector_code': request.form.get('inspector_code'),
                'inspection_date': request.form.get('inspection_date'),
                'inspection_time': request.form.get('inspection_time'),
                'type_of_establishment': request.form.get('type_of_establishment'),
                'no_of_employees': request.form.get('no_of_employees'),
                'purpose_of_visit': request.form.get('purpose_of_visit'),
                'action': request.form.get('action'),
                'food_inspected': request.form.get('food_inspected'),
                'food_condemned': request.form.get('food_condemned'),
                'critical_score': int(request.form.get('critical_score', 0)),
                'overall_score': int(request.form.get('overall_score', 0)),
                'result': request.form.get('result'),
                'comments': request.form.get('comments'),
                'scores': ','.join([request.form.get(f'score_{item["id"]}', '0') for item in FOOD_CHECKLIST_ITEMS]),
                'inspector_signature': request.form.get('inspector_signature'),
                'received_by': request.form.get('received_by'),
                'form_type': 'Food Establishment',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            inspection_id = save_inspection(data)

            conn = sqlite3.connect('inspections.db')
            c = conn.cursor()
            for item in FOOD_CHECKLIST_ITEMS:
                score = request.form.get(f'score_{item["id"]}', '0')
                c.execute("INSERT INTO inspection_items (inspection_id, item_id, details) VALUES (?, ?, ?)",
                          (inspection_id, item["id"], score))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Form submitted', 'inspection_id': inspection_id})
        return jsonify({'success': False, 'error': 'Invalid form type'}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/submit_residential', methods=['POST'])
def submit_residential():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    data = {
        'premises_name': request.form['premises_name'],
        'owner': request.form['owner'],
        'address': request.form['address'],
        'inspector_name': request.form['inspector_name'],
        'inspection_date': request.form['inspection_date'],
        'inspector_code': request.form['inspector_code'],
        'treatment_facility': request.form['treatment_facility'],
        'vector': request.form['vector'],
        'result': request.form['result'],
        'onsite_system': request.form['onsite_system'],
        'building_construction_type': request.form.get('building_construction_type', ''),
        'purpose_of_visit': request.form['purpose_of_visit'],
        'action': request.form['action'],
        'no_of_bedrooms': request.form.get('no_of_bedrooms', ''),
        'total_population': request.form.get('total_population', ''),
        'critical_score': int(request.form['critical_score']),
        'overall_score': int(request.form['overall_score']),
        'comments': request.form.get('comments', ''),
        'inspector_signature': request.form['inspector_signature'],
        'received_by': request.form.get('received_by', ''),
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    inspection_id = save_residential_inspection(data)

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    for item in RESIDENTIAL_CHECKLIST_ITEMS:
        score = request.form.get(f'score_{item["id"]}', '0')
        c.execute("INSERT INTO residential_checklist_scores (form_id, item_id, score) VALUES (?, ?, ?)",
                  (inspection_id, item["id"], score))
    conn.commit()
    conn.close()

    return render_template('residential_form.html', checklist=RESIDENTIAL_CHECKLIST_ITEMS, inspections=get_residential_inspections(), show_form=True, establishment_data=get_establishment_data(), success=True)


@app.route('/submit_burial', methods=['POST'])
def submit_burial():
    if 'inspector' not in session:
        return jsonify({'message': 'Unauthorized: Please log in'}), 401
    data = {
        'id': request.form.get('id', ''),
        'inspection_date': request.form.get('inspection_date', ''),
        'applicant_name': request.form.get('applicant_name', ''),
        'deceased_name': request.form.get('deceased_name', ''),
        'burial_location': request.form.get('burial_location', ''),
        'site_description': request.form.get('site_description', ''),
        'proximity_water_source': request.form.get('proximity_water_source', ''),
        'proximity_perimeter_boundaries': request.form.get('proximity_perimeter_boundaries', ''),
        'proximity_road_pathway': request.form.get('proximity_road_pathway', ''),
        'proximity_trees': request.form.get('proximity_trees', ''),
        'proximity_houses_buildings': request.form.get('proximity_houses_buildings', ''),
        'proposed_grave_type': request.form.get('proposed_grave_type', ''),
        'general_remarks': request.form.get('general_remarks', ''),
        'inspector_signature': request.form.get('inspector_signature', ''),
        'received_by': request.form.get('received_by', '')
    }
    inspection_id = save_burial_inspection(data)
    return jsonify({'message': 'Submit successfully'})

@app.route('/submit_swimming_pools', methods=['POST'])
def submit_swimming_pools():
    conn = sqlite3.connect('inspections.db')
    cursor = conn.cursor()

    # Extract form data
    operator = request.form.get('operator')
    date_inspection = request.form.get('date_inspection')
    inspector_id = request.form.get('inspector_id')
    pool_class = request.form.get('pool_class')
    address = request.form.get('address')
    physical_location = request.form.get('physical_location')
    inspector_comments = request.form.get('inspector_comments')
    inspector_signature = request.form.get('inspector_signature')
    inspector_date = request.form.get('inspector_date')
    manager_signature = request.form.get('manager_signature')
    manager_date = request.form.get('manager_date')

    # Collect checklist scores
    scores = []
    checklist_scores = {}
    total_score = 0
    critical_score = 0
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_key = f"score_{item['id'].upper()}"
        score = float(request.form.get(score_key, 0))
        checklist_scores[item['id'].lower()] = score
        scores.append(str(score))
        total_score += score
        if item['wt'] == 5:
            critical_score += score

    # Calculate overall score
    max_score = sum(item['wt'] for item in SWIMMING_POOL_CHECKLIST_ITEMS)
    overall_score = min((total_score / max_score) * 100, 100)
    result = 'Pass' if overall_score >= 70 else 'Fail'

    # Insert inspection
    cursor.execute('''
        INSERT INTO inspections (establishment_name, owner, address, physical_location, 
        type_of_establishment, inspector_name, inspection_date, form_type, result, 
        created_at, comments, scores, overall_score, critical_score, inspector_signature, 
        received_by, manager_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        operator, operator, address, physical_location, pool_class, inspector_id,
        date_inspection, 'Swimming Pool', result, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        inspector_comments, ','.join(scores), overall_score, critical_score,
        inspector_signature, manager_signature, manager_date
    ))

    inspection_id = cursor.lastrowid

    # Insert inspection items
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        cursor.execute('''
            INSERT INTO inspection_items (inspection_id, item_id, details)
            VALUES (?, ?, ?)
        ''', (inspection_id, item['id'].lower(), str(checklist_scores[item['id'].lower()])))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Inspection submitted successfully'})


@app.route('/swimming_pool/inspection/<int:id>')
def swimming_pool_inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, establishment_name, owner, address, inspector_name, inspection_date, inspection_time, 
               type_of_establishment, physical_location, result, scores, comments, inspector_signature, 
               received_by, created_at, overall_score, critical_score, manager_date
        FROM inspections WHERE id = ? AND form_type = 'Swimming Pool'
    """, (id,))
    inspection = c.fetchone()
    c.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (id,))
    checklist_scores = {row[0].lower(): float(row[1]) if row[1].replace('.', '', 1).isdigit() else 0.0 for row in c.fetchall()}
    conn.close()
    if inspection:
        scores = [float(x) for x in inspection[10].split(',')] if inspection[10] else [0] * len(SWIMMING_POOL_CHECKLIST_ITEMS)
        inspection_data = {
            'id': inspection[0],
            'establishment_name': inspection[1] or '',
            'owner': inspection[2] or '',
            'address': inspection[3] or '',
            'inspector_name': inspection[4] or '',
            'inspection_date': inspection[5] or '',
            'inspection_time': inspection[6] or '',
            'type_of_establishment': inspection[7] or '',
            'physical_location': inspection[8] or '',
            'result': inspection[9] or '',
            'scores': dict(zip([item['id'].lower() for item in SWIMMING_POOL_CHECKLIST_ITEMS], scores)),
            'comments': inspection[11] or '',
            'inspector_signature': inspection[12] or '',
            'received_by': inspection[13] or '',
            'created_at': inspection[14] or '',
            'overall_score': float(inspection[15]) if inspection[15] else 0.0,
            'critical_score': float(inspection[16]) if inspection[16] else 0.0,
            'manager_date': inspection[17] or '',
            'checklist_scores': checklist_scores
        }
        return render_template('swimming_pool_inspection_detail.html',
                              inspection=inspection_data,
                              checklist=SWIMMING_POOL_CHECKLIST_ITEMS)
    return "Inspection not found", 404


@app.route('/submit_small_hotels', methods=['POST'])
def submit_small_hotels():
    if 'inspector' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.form
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Calculate scores
    scores = []
    critical_score = 0
    overall_score = 0
    for item in SMALL_HOTELS_CHECKLIST_ITEMS:
        item_id = item['id'].lower()
        error = data.get(f'error_{item_id}', '0').strip()
        score = 2.5 if error == '0' else 0
        scores.append(score)
        if item['critical']:
            critical_score += score
        overall_score += score

    # Insert inspection
    c.execute('''
        INSERT INTO inspections (establishment_name, address, physical_location, inspector_name, 
                                inspection_date, comments, result, overall_score, critical_score, 
                                created_at, form_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    ''', (
        data.get('establishment_name'), data.get('address'), data.get('physical_location'),
        data.get('inspector_name'), data.get('inspection_date'), data.get('comments'),
        data.get('result'), overall_score, critical_score, 'Small Hotel'
    ))
    inspection_id = c.lastrowid

    # Insert checklist items
    for item in SMALL_HOTELS_CHECKLIST_ITEMS:
        item_id = item['id'].lower()
        c.execute('''
            INSERT INTO inspection_items (inspection_id, item_id, obser, error)
            VALUES (?, ?, ?, ?)
        ''', (
            inspection_id, item_id, data.get(f'obser_{item_id}', ''),
            data.get(f'error_{item_id}', '0')
        ))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Inspection submitted successfully"})


@app.route('/dashboard')
def dashboard():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspections = get_inspections()
    return render_template('dashboard.html', inspections=inspections)

@app.route('/stats')
def get_stats():
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM inspections")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Food Establishment'")
    food = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM residential_inspections")
    residential = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM burial_site_inspections")
    burial = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Spirit Licence Premises'")
    spirit_licence = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Swimming Pool'")
    swimming_pool = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM inspections WHERE form_type = 'Small Hotel'")
    small_hotels = c.fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'food': food,
        'residential': residential,
        'burial': burial,
        'spirit_licence': spirit_licence,
        'swimming_pool': swimming_pool,
        'small_hotels': small_hotels
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
        if query in (establishment_name or '').lower() or query in (owner or '').lower() or query in (license_no or '').lower():
            suggestions.append({'text': f"{establishment_name} (Owner: {owner}, License: {license_no})", 'id': id, 'type': 'food'})
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

    if not form_type or form_type == 'all':
        c.execute("""
            SELECT id, establishment_name, created_at, result, form_type 
            FROM inspections 
            WHERE form_type IN ('Food Establishment', 'Residential & Non-Residential', 'Water Supply', 'Spirit Licence Premises', 'Swimming Pool', 'Small Hotel')
            AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(address) LIKE ?)
            UNION
            SELECT id, applicant_name AS establishment_name, created_at, 'Completed' AS result, 'Burial Site' AS form_type
            FROM burial_site_inspections
            WHERE LOWER(applicant_name) LIKE ? OR LOWER(deceased_name) LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        records = c.fetchall()
        for record in records:
            forms.append({
                'id': record[0],
                'establishment_name': record[1],
                'created_at': record[2],
                'result': record[3] or '',
                'type': record[4]
            })
    else:
        if form_type == 'food':
            c.execute(
                "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Food Establishment' AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'establishment_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'type': 'food'})
        elif form_type == 'residential':
            c.execute(
                "SELECT id, premises_name, created_at, result, owner FROM residential_inspections WHERE (LOWER(premises_name) LIKE ? OR LOWER(owner) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'premises_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'owner': record[4], 'type': 'residential'})
        elif form_type == 'burial':
            c.execute(
                "SELECT id, applicant_name, deceased_name, created_at, 'Completed' AS status FROM burial_site_inspections WHERE LOWER(applicant_name) LIKE ? OR LOWER(deceased_name) LIKE ?",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({
                    'id': record[0],
                    'applicant_name': record[1],
                    'deceased_name': record[2],
                    'created_at': record[3],
                    'status': record[4],
                    'type': 'burial'
                })
        elif form_type == 'water_supply':
            c.execute(
                "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Water Supply' AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'establishment_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'type': 'water_supply'})
        elif form_type == 'spirit_licence':
            c.execute(
                "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Spirit Licence Premises' AND (LOWER(establishment_name) LIKE ? OR LOWER(owner) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'establishment_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'type': 'spirit_licence'})
        elif form_type == 'swimming_pool':
            c.execute(
                "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Swimming Pool' AND (LOWER(establishment_name) LIKE ? OR LOWER(address) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'establishment_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'type': 'swimming_pool'})
        elif form_type == 'small_hotels':
            c.execute(
                "SELECT id, establishment_name, created_at, result FROM inspections WHERE form_type = 'Small Hotel' AND (LOWER(establishment_name) LIKE ? OR LOWER(address) LIKE ?)",
                (f'%{query}%', f'%{query}%'))
            records = c.fetchall()
            for record in records:
                forms.append({'id': record[0], 'establishment_name': record[1], 'created_at': record[2],
                              'result': record[3] or '', 'type': 'small_hotels'})

    conn.close()
    return jsonify({'forms': forms})

@app.route('/search_residential', methods=['GET'])
def search_residential():
    if 'inspector' not in session:
        return redirect(url_for('login'))
    query = request.args.get('term', '').lower()
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("""
        SELECT id, premises_name, owner, created_at, result 
        FROM residential_inspections 
        WHERE LOWER(premises_name) LIKE ? OR LOWER(owner) LIKE ? OR LOWER(created_at) LIKE ?
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    records = c.fetchall()
    suggestions = [{'id': row[0], 'premises_name': row[1], 'owner': row[2], 'created_at': row[3], 'result': row[4]} for row in records]
    conn.close()
    return jsonify({'suggestions': suggestions})


@app.route('/inspection/<int:id>')
def inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, created_at, form_type, inspector_code, no_of_employees, food_inspected, food_condemned FROM inspections WHERE id = ?", (id,))
    inspection = c.fetchone()
    conn.close()

    if inspection:
        scores = [int(x) for x in inspection[12].split(',')] if inspection[12] else [0] * 45
        inspection_data = {
            'id': inspection[0],
            'establishment_name': inspection[1] or '',
            'owner': inspection[2] or '',
            'address': inspection[3] or '',
            'license_no': inspection[4] or '',
            'inspector_name': inspection[5] or '',
            'inspection_date': inspection[6] or '',
            'inspection_time': inspection[7] or '',
            'type_of_establishment': inspection[8] or '',
            'purpose_of_visit': inspection[9] or '',
            'action': inspection[10] or '',
            'result': inspection[11] or '',
            'scores': dict(zip(range(1, 46), scores)),
            'comments': inspection[13] or '',
            'inspector_signature': inspection[5] or '',
            'received_by': inspection[2] or '',
            'overall_score': sum(score for score in scores if score > 0),
            'critical_score': sum(score for item, score in zip(FOOD_CHECKLIST_ITEMS, scores) if item.get('wt', 0) >= 4 and score > 0),
            'inspector_code': inspection[16] or '',
            'no_of_employees': inspection[17] or '',
            'food_inspected': float(inspection[18]) if inspection[18] else 0.0,
            'food_condemned': float(inspection[19]) if inspection[19] else 0.0,
            'form_type': inspection[15],
            'created_at': inspection[14] or ''
        }
        return render_template('inspection_detail.html', inspection=inspection_data, checklist=FOOD_CHECKLIST_ITEMS)
    return "Inspection not found", 404

@app.route('/residential/inspection/<int:form_id>')
def residential_inspection(form_id):
    details = get_residential_inspection_details(form_id)
    if details:
        premises_name = details['premises_name']
        owner = details['owner']
        address = details['address']
        inspector_name = details['inspector_name']
        inspection_date = details['inspection_date']
        inspector_code = details['inspector_code']
        treatment_facility = details['treatment_facility']
        vector = details['vector']
        result = details['result']
        onsite_system = details['onsite_system']
        building_construction_type = details['building_construction_type']
        purpose_of_visit = details['purpose_of_visit']
        action = details['action']
        no_of_bedrooms = details['no_of_bedrooms']
        total_population = details['total_population']
        critical_score = details['critical_score']
        overall_score = details['overall_score']
        comments = details['comments']
        inspector_signature = details['inspector_signature']
        received_by = details['received_by']
        created_at = details['created_at']
        checklist_scores = details['checklist_scores']
    else:
        premises_name = owner = address = inspector_name = inspection_date = inspector_code = treatment_facility = vector = result = onsite_system = building_construction_type = purpose_of_visit = action = no_of_bedrooms = total_population = comments = inspector_signature = received_by = created_at = 'N/A'
        critical_score = overall_score = 0
        checklist_scores = {item['id']: '0' for item in RESIDENTIAL_CHECKLIST_ITEMS}
    return render_template('residential_inspection_details.html',
                          form_id=form_id,
                          premises_name=premises_name,
                          owner=owner,
                          address=address,
                          inspector_name=inspector_name,
                          inspection_date=inspection_date,
                          inspector_code=inspector_code,
                          treatment_facility=treatment_facility,
                          vector=vector,
                          result=result,
                          onsite_system=onsite_system,
                          building_construction_type=building_construction_type,
                          purpose_of_visit=purpose_of_visit,
                          action=action,
                          no_of_bedrooms=no_of_bedrooms,
                          total_population=total_population,
                          critical_score=critical_score,
                          overall_score=overall_score,
                          comments=comments,
                          inspector_signature=inspector_signature,
                          received_by=received_by,
                          created_at=created_at,
                          checklist=RESIDENTIAL_CHECKLIST_ITEMS,
                          checklist_scores=checklist_scores)


@app.route('/inspection/inspection/<int:form_id>')
def inspection_inspection(form_id):
    details = get_inspection_details(form_id)
    if details:
        establishment_name = details['establishment_name']
        owner = details['owner']
        address = details['address']
        license_no = details['license_no']
        inspector_name = details['inspector_name']
        inspection_date = details['inspection_date']
        inspection_time = details['inspection_time']
        type_of_establishment = details['type_of_establishment']
        purpose_of_visit = details['purpose_of_visit']
        action = details['action']
        result = details['result']
        food_inspected = details['food_inspected']
        food_condemned = details['food_condemned']
        critical_score = details['critical_score']
        overall_score = details['overall_score']
        comments = details['comments']
        inspector_signature = details['inspector_signature']
        received_by = details['received_by']
        created_at = details['created_at']
        scores = details['scores']
    else:
        establishment_name = owner = address = license_no = inspector_name = inspection_date = inspection_time = type_of_establishment = purpose_of_visit = action = result = food_inspected = food_condemned = comments = inspector_signature = received_by = created_at = 'N/A'
        critical_score = overall_score = 0
        scores = {item['id']: '0' for item in FOOD_CHECKLIST_ITEMS}
    return render_template('inspection_detail.html',
                          form_id=form_id,
                          establishment_name=establishment_name,
                          owner=owner,
                          address=address,
                          license_no=license_no,
                          inspector_name=inspector_name,
                          inspection_date=inspection_date,
                          inspection_time=inspection_time,
                          type_of_establishment=type_of_establishment,
                          purpose_of_visit=purpose_of_visit,
                          action=action,
                          result=result,
                          food_inspected=food_inspected,
                          food_condemned=food_condemned,
                          critical_score=critical_score,
                          overall_score=overall_score,
                          comments=comments,
                          inspector_signature=inspector_signature,
                          received_by=received_by,
                          created_at=created_at,
                          checklist=FOOD_CHECKLIST_ITEMS,
                          scores=scores)

@app.route('/download_inspection_pdf/<int:form_id>')
def download_inspection_pdf(form_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, inspector_signature, received_by, created_at, inspector_code, no_of_employees, food_inspected, food_condemned FROM inspections WHERE id = ?", (form_id,))
    form_data = c.fetchone()
    conn.close()

    if form_data:
        id, establishment_name, owner, address, license_no, inspector_name, inspection_date, inspection_time, type_of_establishment, purpose_of_visit, action, result, scores, comments, inspector_signature, received_by, created_at, inspector_code, no_of_employees, food_inspected, food_condemned = form_data
        response = make_response()
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=inspection_details_{form_id}.pdf'

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, f"Inspection Form - ID: {id}")
        p.drawString(100, 700, f"Establishment: {establishment_name}")
        p.drawString(100, 650, f"Owner: {owner}")
        p.drawString(100, 600, f"Date Completed: {created_at}")
        p.drawString(100, 550, f"Result: {result}")
        p.showPage()
        p.save()
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        return Response(pdf_data, headers=response.headers)
    return "PDF generation failed", 500

@app.route('/burial/inspection/<int:id>')
def burial_inspection_detail(id):
    if 'inspector' not in session:
        return redirect(url_for('login'))
    inspection = get_burial_inspection_details(id)
    if not inspection:
        return "Not Found", 404
    inspection_data = {
        'id': inspection['id'],
        'inspection_date': inspection['inspection_date'],
        'applicant_name': inspection['applicant_name'],
        'deceased_name': inspection['deceased_name'],
        'burial_location': inspection['burial_location'],
        'site_description': inspection['site_description'],
        'proximity_water_source': inspection['proximity_water_source'],
        'proximity_perimeter_boundaries': inspection['proximity_perimeter_boundaries'],
        'proximity_road_pathway': inspection['proximity_road_pathway'],
        'proximity_trees': inspection['proximity_trees'],
        'proximity_houses_buildings': inspection['proximity_houses_buildings'],
        'proposed_grave_type': inspection['proposed_grave_type'],
        'general_remarks': inspection['general_remarks'],
        'inspector_signature': inspection['inspector_signature'],
        'received_by': inspection['received_by'],
        'created_at': inspection['created_at']
    }
    return render_template('burial_inspection_detail.html', inspection=inspection_data)

@app.route('/download_residential_pdf/<int:form_id>')
def download_residential_pdf(form_id):
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("SELECT premises_name, owner, address, inspector_name, inspection_date, inspector_code, treatment_facility, vector, result, onsite_system, building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population, critical_score, overall_score, comments, inspector_signature, received_by, created_at FROM residential_inspections WHERE id = ?", (form_id,))
    form_data = c.fetchone()
    conn.close()

    if form_data:
        premises_name, owner, address, inspector_name, inspection_date, inspector_code, treatment_facility, vector, result, onsite_system, building_construction_type, purpose_of_visit, action, no_of_bedrooms, total_population, critical_score, overall_score, comments, inspector_signature, received_by, created_at = form_data
        response = make_response()
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=residential_inspection_details_{form_id}.pdf'

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, f"Residential Inspection Form - ID: {form_id}")
        p.drawString(100, 700, f"Name of Premises: {premises_name}")
        p.drawString(100, 650, f"Owner/Agent/Occupier: {owner}")
        p.drawString(100, 600, f"Date Completed: {created_at}")
        p.drawString(100, 550, f"Result: {result}")
        p.showPage()
        p.save()
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        return Response(pdf_data, headers=response.headers)
    return "PDF generation failed", 500


@app.route('/view_small_hotels/<int:inspection_id>')
def view_small_hotels(inspection_id):
    if 'inspector' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT id, establishment_name, address, physical_location, inspector_name, 
               inspection_date, type_of_establishment, comments, result, overall_score, 
               critical_score, created_at, owner, license_no, purpose_of_visit, action, 
               food_inspected, food_condemned, inspector_code, no_of_employees, scores
        FROM inspections WHERE id = ? AND form_type = 'Small Hotel'
    ''', (inspection_id,))
    inspection = c.fetchone()

    if not inspection:
        conn.close()
        return "Inspection not found", 404

    # Fetch checklist items
    c.execute('''
        SELECT item_id, details, obser, error 
        FROM inspection_items WHERE inspection_id = ?
    ''', (inspection_id,))
    items = c.fetchall()

    # Structure inspection data
    inspection_dict = dict(inspection)
    inspection_dict['details'] = {item['item_id']: item['details'] for item in items}
    inspection_dict['obser'] = {item['item_id']: item['obser'] for item in items}
    inspection_dict['error'] = {item['item_id']: item['error'] for item in items}

    # Parse scores if available
    if inspection['scores']:
        scores = [float(x) for x in inspection['scores'].split(',')]
        inspection_dict['scores'] = dict(zip([item['id'].lower() for item in SMALL_HOTELS_CHECKLIST_ITEMS], scores))
    else:
        inspection_dict['scores'] = {item['id'].lower(): 0.0 for item in SMALL_HOTELS_CHECKLIST_ITEMS}

    conn.close()

    return render_template('small_hotel_inspection_detail.html',
                           inspection=inspection_dict,
                           checklist_items=SMALL_HOTELS_CHECKLIST_ITEMS)



def get_db_connection():
    conn = sqlite3.connect('inspections.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('inspector', 'admin'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (recipient_id) REFERENCES users(id)
    )''')
    # Insert default users if not exist
    try:
        c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', 'adminpass', 'admin'))
        for i in range(1, 7):
            c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)', (f'inspector{i}', f'pass{i}', 'inspector'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user_role = c.fetchone()['role']
        if user_role == 'admin':
            c.execute('SELECT id, username FROM users WHERE role = "inspector" AND id != ?', (user_id,))
        else:  # inspector
            c.execute('SELECT id, username FROM users WHERE role = "admin" AND id != ?', (user_id,))
        users = [{'id': row['id'], 'username': row['username']} for row in c.fetchall()]
        return jsonify(users)
    finally:
        conn.close()

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user_role = c.fetchone()['role']
        if user_role == 'inspector':
            c.execute('''SELECT u.id, u.username, 
                         (SELECT COUNT(*) FROM messages m WHERE m.recipient_id = ? AND m.sender_id = u.id AND m.is_read = 0) AS unread_count
                         FROM users u WHERE u.role = "admin" AND u.id != ?''', (user_id, user_id))
        else:  # admin
            c.execute('''SELECT u.id, u.username, 
                         (SELECT COUNT(*) FROM messages m WHERE m.recipient_id = ? AND m.sender_id = u.id AND m.is_read = 0) AS unread_count
                         FROM users u WHERE u.role = "inspector" AND u.id != ?''', (user_id, user_id))
        contacts = [{'id': row['id'], 'username': row['username'], 'unread_count': row['unread_count']} for row in c.fetchall()]
        return jsonify(contacts)
    finally:
        conn.close()

@app.route('/api/messages', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    recipient_id = data.get('receiver_id')  # Frontend sends 'receiver_id'
    content = data.get('content')
    if not recipient_id or not content:
        return jsonify({'error': 'Missing recipient_id or content'}), 400
    sender_id = session['user_id']
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (sender_id,))
        sender_role = c.fetchone()['role']
        c.execute('SELECT role FROM users WHERE id = ?', (recipient_id,))
        recipient = c.fetchone()
        if not recipient:
            return jsonify({'error': 'Invalid recipient'}), 400
        recipient_role = recipient['role']
        if (sender_role == 'inspector' and recipient_role != 'admin') or (sender_role == 'admin' and recipient_role != 'inspector'):
            return jsonify({'error': 'Invalid recipient for your role'}), 403
        timestamp = datetime.utcnow().isoformat()
        c.execute('INSERT INTO messages (sender_id, recipient_id, content, timestamp, is_read) VALUES (?, ?, ?, ?, ?)',
                  (sender_id, recipient_id, content, timestamp, 0))
        conn.commit()
        message_id = c.lastrowid
        return jsonify({
            'id': message_id,
            'sender_id': sender_id,
            'recipient_id': recipient_id,
            'content': content,
            'timestamp': timestamp,
            'is_read': 0
        }), 201
    except sqlite3.IntegrityError as e:
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/messages/<int:contact_id>', methods=['GET'])
def get_messages(contact_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user_role = c.fetchone()['role']
        c.execute('SELECT role FROM users WHERE id = ?', (contact_id,))
        contact = c.fetchone()
        if not contact:
            return jsonify({'error': 'Invalid contact'}), 400
        contact_role = contact['role']
        if (user_role == 'inspector' and contact_role != 'admin') or (user_role == 'admin' and contact_role != 'inspector'):
            return jsonify({'error': 'Invalid contact for your role'}), 403
        c.execute('''SELECT id, sender_id, recipient_id, content, timestamp, is_read,
                     CASE WHEN sender_id = ? THEN 1 ELSE 0 END AS is_sent
                     FROM messages
                     WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?)
                     ORDER BY timestamp ASC''',
                  (user_id, user_id, contact_id, contact_id, user_id))
        messages = [
            {
                'id': row['id'],
                'sender_id': row['sender_id'],
                'recipient_id': row['recipient_id'],
                'content': row['content'],
                'timestamp': row['timestamp'],
                'is_read': row['is_read'],
                'is_sent': row['is_sent']
            } for row in c.fetchall()
        ]
        c.execute('UPDATE messages SET is_read = 1 WHERE recipient_id = ? AND sender_id = ? AND is_read = 0',
                  (user_id, contact_id))
        conn.commit()
        return jsonify(messages)
    except sqlite3.OperationalError as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
