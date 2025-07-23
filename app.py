# Standard Library Imports
import os
import sqlite3
import io
from datetime import datetime

# Flask Imports
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, Response

# ReportLab Imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

# Database Imports
from database import (
    get_residential_inspection_details,
    get_residential_inspections,
    init_db,
    save_residential_inspection,
    save_inspection,
    save_burial_inspection,
    get_inspections,
    get_burial_inspections,
    get_inspection_details,
    get_burial_inspection_details
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Corrected Checklist for Food Establishment Inspection Form
# Complete 45-item structure matching the official form

FOOD_CHECKLIST_ITEMS = [
    # FOOD (1-2)
    {"id": 1, "desc": "Source, Sound Condition, No Spoilage", "wt": 5},
    {"id": 2, "desc": "Original Container, Properly Labeled", "wt": 1},

    # FOOD PROTECTION (3-10)
    {"id": 3, "desc": "Potentially Hazardous Food Meets Temperature Requirements During Storage, Preparation, Display, Service, Transportation", "wt": 5},
    {"id": 4, "desc": "Facilities to Maintain Product Temperature", "wt": 4},
    {"id": 5, "desc": "Thermometers Provided and Conspicuous", "wt": 1},
    {"id": 6, "desc": "Potentially Hazardous Food Properly Thawed", "wt": 2},
    {"id": 7, "desc": "Unwrapped and Potentially Hazardous Food Not Re-Served", "wt": 4},
    {"id": 8, "desc": "Food Protection During Storage, Preparation, Display, Service, Transportation", "wt": 2},
    {"id": 9, "desc": "Handling of Food (Ice) Minimized", "wt": 1},
    {"id": 10, "desc": "In Use Food (Ice) Dispensing Utensils Properly Stored", "wt": 1},

    # FOOD EQUIPMENT & UTENSILS (11-23)
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
    {"id": 23, "desc": "Storage, Handling of Clean Equipment/Utensils", "wt": 1},

    # TOILET & HANDWASHING FACILITIES (24-25)
    {"id": 24, "desc": "Number, Convenient, Accessible, Designed, Installed", "wt": 4},
    {"id": 25, "desc": "Toilet Rooms Enclosed, Self-Closing Doors, Fixtures: Good Repair, Clean, Hand Cleanser, Sanitary Towels, Hand Drying Devices Provided, Proper Waste Receptacles", "wt": 2},

    # SOLID WASTE MANAGEMENT (26-27)
    {"id": 26, "desc": "Containers or Receptacles: Covered, Adequate Number, Insect/Rodent Proof, Frequency, Clean", "wt": 2},
    {"id": 27, "desc": "Outside Storage Area Enclosures Properly Constructed, Clean, Controlled Incineration", "wt": 1},

    # INSECT, RODENT, ANIMAL CONTROL (28)
    {"id": 28, "desc": "Evidence of Insects/Rodents - Outer Openings, Protected, No Birds, Turtles, Other Animals", "wt": 4},

    # PERSONNEL (29-31) - REMOVED OLD ITEM 32, RENUMBERED EVERYTHING AFTER
    {"id": 29, "desc": "Personnel with Infections Restricted", "wt": 5},
    {"id": 30, "desc": "Hands Washed and Clean, Good Hygienic Practices", "wt": 5},
    {"id": 31, "desc": "Clean Clothes, Hair Restraints", "wt": 2},  # INCREASED FROM 1 TO 2

    # LIGHTING (32) - RENUMBERED FROM 33
    {"id": 32, "desc": "Lighting Provided as Required, Fixtures Shielded", "wt": 1},

    # VENTILATION (33) - RENUMBERED FROM 34
    {"id": 33, "desc": "Rooms and Equipment - Venting as Required", "wt": 1},

    # DRESSING ROOMS (34) - RENUMBERED FROM 35
    {"id": 34, "desc": "Rooms Clean, Lockers Provided, Facilities Clean", "wt": 1},

    # WATER (35) - RENUMBERED FROM 36
    {"id": 35, "desc": "Water Source Safe, Hot & Cold Under Pressure", "wt": 5},

    # SEWAGE (36) - RENUMBERED FROM 37
    {"id": 36, "desc": "Sewage and Waste Water Disposal", "wt": 4},

    # PLUMBING (37-38) - RENUMBERED FROM 38-39
    {"id": 37, "desc": "Installed, Maintained", "wt": 1},
    {"id": 38, "desc": "Cross Connection, Back Siphonage, Backflow", "wt": 5},

    # FLOORS, WALLS, & CEILINGS (39-40) - RENUMBERED FROM 40-41
    {"id": 39, "desc": "Floors: Constructed, Drained, Clean, Good Repair, Covering Installation, Dustless Cleaning Methods", "wt": 1},
    {"id": 40, "desc": "Walls, Ceiling, Attached Equipment: Constructed, Good Repair, Clean Surfaces, Dustless Cleaning Methods", "wt": 1},

    # OTHER OPERATIONS (41-44) - RENUMBERED FROM 42-45
    {"id": 41, "desc": "Toxic Items Properly Stored, Labeled, Used", "wt": 5},
    {"id": 42, "desc": "Premises Maintained Free of Litter, Unnecessary Articles, Cleaning Maintenance Equipment Properly Stored, Authorized Personnel", "wt": 1},
    {"id": 43, "desc": "Complete Separation for Living/Sleeping Quarters, Laundry", "wt": 1},
    {"id": 44, "desc": "Clean, Soiled Linen Properly Stored", "wt": 1},
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

# Swimming Pool Checklist - CORRECTED WEIGHTS
SWIMMING_POOL_CHECKLIST_ITEMS = [
    {"id": "1A", "desc": "Written procedures for microbiological monitoring of pool water implemented", "wt": 5, "category": "Documentation"},
    {"id": "1B", "desc": "Microbiological results", "wt": 2.5, "category": "Documentation"},
    {"id": "1C", "desc": "Date of last testing within required frequency", "wt": 2.5, "category": "Documentation"},
    {"id": "1D", "desc": "Acceptable monitoring procedures", "wt": 5, "category": "Documentation"},
    {"id": "1E", "desc": "Daily log books and records up-to-date", "wt": 5, "category": "Documentation"},
    {"id": "1F", "desc": "Written emergency procedures established and implemented", "wt": 5, "category": "Documentation"},
    {"id": "1G", "desc": "Personal liability and accident insurance", "wt": 5, "category": "Documentation"},
    {"id": "1H", "desc": "Lifeguard/Lifesaver certification", "wt": 5, "category": "Documentation"},
    {"id": "2A", "desc": "Defects in pool construction", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2B", "desc": "Evidence of flaking paint and/or mould growth", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2C", "desc": "All surfaces of the deck and pool free from obstruction that can cause accident/injury", "wt": 5, "category": "Physical Condition"},
    {"id": "2D", "desc": "Exposed piping: - identified/colour coded", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2E", "desc": "In good repair", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2F", "desc": "Suction fittings/inlets: - in good repair", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2G", "desc": "At least two suction orifices equipped with anti-entrapment devices", "wt": 5, "category": "Physical Condition"},
    {"id": "2H", "desc": "Perimeter drains free of debris", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2I", "desc": "Pool walls and floor clean", "wt": 2.5, "category": "Physical Condition"},
    {"id": "2J", "desc": "Components of the re-circulating system maintained", "wt": 2.5, "category": "Physical Condition"},
    {"id": "3A", "desc": "Clarity", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3B", "desc": "Chlorine residual > 0.5 mg/l", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3C", "desc": "pH value within range of 7.5 and 7.8", "wt": 5, "category": "Pool Chemistry"},
    {"id": "3D", "desc": "Well supplied and equipped", "wt": 2.5, "category": "Pool Chemistry"},
    {"id": "4A", "desc": "Pool chemicals - stored safely", "wt": 5, "category": "Pool Chemicals"},
    {"id": "4B", "desc": "Dispensed automatically or in a safe manner", "wt": 2.5, "category": "Pool Chemicals"},
    {"id": "5A", "desc": "Depth markings clearly visible", "wt": 5, "category": "Safety"},
    {"id": "5B", "desc": "Working emergency phone", "wt": 5, "category": "Safety"},
    {"id": "6A", "desc": "Reaching poles with hook", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6B", "desc": "Two throwing aids", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6C", "desc": "Spine board with cervical collar", "wt": 2.5, "category": "Safety Aids"},
    {"id": "6D", "desc": "Well equipped first aid kit", "wt": 2.5, "category": "Safety Aids"},
    {"id": "7A", "desc": "Caution notices: - pool depth indications", "wt": 1, "category": "Signs and Notices"},
    {"id": "7B", "desc": "Public health notices", "wt": 1, "category": "Signs and Notices"},
    {"id": "7C", "desc": "Emergency procedures", "wt": 1, "category": "Signs and Notices"},
    {"id": "7D", "desc": "Maximum bathing load", "wt": 1, "category": "Signs and Notices"},
    {"id": "7E", "desc": "Lifeguard on duty/bathe at your own risk signs", "wt": 1, "category": "Signs and Notices"},
    {"id": "8A", "desc": "Licensed Lifeguards always on duty during pool opening hours", "wt": 2.5, "category": "Lifeguards/Lifesavers"},
    {"id": "8B", "desc": "If N/A, trained lifesavers readily available", "wt": 5, "category": "Lifeguards/Lifesavers"},
    {"id": "8C", "desc": "Number of lifeguard/lifesavers", "wt": 2.5, "category": "Lifeguards/Lifesavers"},
    {"id": "9A", "desc": "Shower, toilet and dressing rooms: - clean and disinfected as required", "wt": 5, "category": "Sanitary Facilities"},
    {"id": "9B", "desc": "Vented", "wt": 2.5, "category": "Sanitary Facilities"},
    {"id": "9C", "desc": "Well supplied and equipped", "wt": 2.5, "category": "Sanitary Facilities"},
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

@app.route('/generate_report', methods=['GET'])
def generate_report():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    metric = request.args.get('metric', 'inspections')
    timeframe = request.args.get('timeframe', 'daily')
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    if metric == 'inspections':
        query = """
            SELECT strftime('%Y-%m-%d', created_at) AS date, COUNT(*) AS count
            FROM inspections
            GROUP BY date
        """
        c.execute(query)
        results = c.fetchall()
        data = {'dates': [], 'counts': []}
        for date, count in results:
            data['dates'].append(date)
            data['counts'].append(count)
        conn.close()
        return jsonify(data)
    conn.close()
    return jsonify({'error': 'Invalid metric'}), 400

@app.route('/api/system_health', methods=['GET'])
def system_health():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    # Simulated data; replace with actual metrics
    data = {
        'uptime': 99.9,
        'db_response': 50,
        'error_rate': 0.1,
        'history': {
            'labels': ['1h', '2h', '3h', '4h', '5h'],
            'uptime': [99.8, 99.9, 99.7, 99.9, 99.9],
            'db_response': [45, 50, 55, 48, 50],
            'error_rate': [0.2, 0.1, 0.3, 0.1, 0.1]
        }
    }
    return jsonify(data)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('login'))  # Redirect to login page



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
    if 'inspector' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in.'}), 401

    conn = sqlite3.connect('inspections.db')
    cursor = conn.cursor()

    # Auto-fix database columns if needed
    try:
        cursor.execute("SELECT score_1A FROM inspections LIMIT 1")
    except sqlite3.OperationalError:
        # Columns don't exist, add them
        print("Adding missing swimming pool score columns...")
        for item in SWIMMING_POOL_CHECKLIST_ITEMS:
            try:
                cursor.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
                print(f"Added column score_{item['id']}")
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()

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

    # DEBUG: Print what we're receiving
    print("=== DEBUG: Form data received ===")
    for key, value in request.form.items():
        if key.startswith('score_'):
            print(f"{key}: {value}")

    # Collect checklist scores with correct field names
    scores = []
    total_score = 0
    max_possible_score = 0

    # Prepare individual score updates
    score_updates = {}

    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        # The form sends field names like score_1A, score_1B, etc.
        score_key = f"score_{item['id']}"
        score = float(request.form.get(score_key, 0))

        # Store for individual column updates
        score_updates[score_key] = score

        scores.append(str(score))
        total_score += score
        max_possible_score += item['wt']

        print(f"Item {item['id']}: looking for {score_key}, got {score}, weight {item['wt']}")

    # Calculate overall score as percentage - rounded to 1 decimal place
    overall_score = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
    overall_score = round(min(overall_score, 100), 1)  # Round to 1 decimal place

    # Calculate critical score (items with weight 5 are critical)
    critical_score = sum(float(request.form.get(f"score_{item['id']}", 0))
                         for item in SWIMMING_POOL_CHECKLIST_ITEMS if item['wt'] == 5)

    result = 'Pass' if overall_score >= 70 else 'Fail'

    print(f"=== SCORING DEBUG ===")
    print(f"Total Score: {total_score}")
    print(f"Max Possible: {max_possible_score}")
    print(f"Overall Score: {overall_score}%")
    print(f"Critical Score: {critical_score}")
    print(f"Result: {result}")

    # Build the INSERT query dynamically to include all score columns
    base_columns = '''establishment_name, owner, address, physical_location, 
                     type_of_establishment, inspector_name, inspection_date, form_type, result, 
                     created_at, comments, scores, overall_score, critical_score, inspector_signature, 
                     received_by, manager_date'''

    score_columns = ', '.join([f"score_{item['id']}" for item in SWIMMING_POOL_CHECKLIST_ITEMS])
    all_columns = f"{base_columns}, {score_columns}"

    base_placeholders = '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
    score_placeholders = ', '.join(['?' for _ in SWIMMING_POOL_CHECKLIST_ITEMS])
    all_placeholders = f"{base_placeholders}, {score_placeholders}"

    base_values = (
        operator, operator, address, physical_location, pool_class, inspector_id,
        date_inspection, 'Swimming Pool', result, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        inspector_comments, ','.join(scores), overall_score, critical_score,
        inspector_signature, manager_signature, manager_date
    )

    score_values = tuple(score_updates[f"score_{item['id']}"] for item in SWIMMING_POOL_CHECKLIST_ITEMS)
    all_values = base_values + score_values

    # Insert inspection into main table with all scores
    try:
        cursor.execute(f'''
            INSERT INTO inspections ({all_columns})
            VALUES ({all_placeholders})
        ''', all_values)

        inspection_id = cursor.lastrowid
        print(f"=== SUCCESS: Inspection {inspection_id} saved with all scores ===")

    except sqlite3.OperationalError as e:
        print(f"Error inserting with score columns: {e}")
        # Fallback to basic insert
        cursor.execute('''
            INSERT INTO inspections (establishment_name, owner, address, physical_location, 
            type_of_establishment, inspector_name, inspection_date, form_type, result, 
            created_at, comments, scores, overall_score, critical_score, inspector_signature, 
            received_by, manager_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', base_values)

        inspection_id = cursor.lastrowid

    # Insert inspection items
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_key = f"score_{item['id']}"
        score = float(request.form.get(score_key, 0))
        cursor.execute('''
            INSERT INTO inspection_items (inspection_id, item_id, details)
            VALUES (?, ?, ?)
        ''', (inspection_id, item['id'], str(score)))

    conn.commit()
    conn.close()

    print(f"=== FINAL SUCCESS: Inspection {inspection_id} completely saved ===")
    return jsonify({'status': 'success', 'message': 'Inspection submitted successfully'})


@app.route('/fix_swimming_pool_db')
def fix_swimming_pool_db():
    """Run this once to add missing columns to the inspections table"""
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    cursor = conn.cursor()

    # Add score columns for each checklist item
    columns_added = 0
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        try:
            cursor.execute(f'ALTER TABLE inspections ADD COLUMN score_{item["id"]} REAL DEFAULT 0')
            columns_added += 1
            print(f"Added column score_{item['id']}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Error adding score_{item['id']}: {e}")

    conn.commit()
    conn.close()
    return f"Database updated! Added {columns_added} new columns."


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

@app.route('/medical_officer')
def medical_officer():
    if 'medical_officer' not in session:
        return redirect(url_for('login'))
    return render_template('medical_officer.html')

@app.route('/dashboard')
def dashboard():
    if 'admin' in session:
        return redirect(url_for('admin'))  # Send admin users back to admin dashboard
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
    if 'inspector' not in session and 'admin' not in session:
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
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
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

import logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/burial/inspection/<int:id>')
def burial_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))
    inspection = get_burial_inspection_details(id)
    if not inspection:
        logging.error(f"No burial inspection found for id: {id}")
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
    logging.debug(f"Rendering burial inspection detail for id: {id}")
    return render_template('burial_inspection_detail.html', inspection=inspection_data)

# Replace ALL your PDF download functions with these exact form replicas


@app.route('/download_burial_pdf/<int:form_id>')
def download_burial_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    inspection = get_burial_inspection_details(form_id)
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Form Header
    y = create_form_header(p, "BURIAL SITE INSPECTION FORM", form_id, width, height)

    # Section 1: Basic Information
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "BASIC INFORMATION")
    y -= 25

    p.setFont("Helvetica", 10)
    fields = [
        ("Inspection Date:", inspection.get('inspection_date', '')),
        ("Applicant Name:", inspection.get('applicant_name', '')),
        ("Deceased Name:", inspection.get('deceased_name', '')),
        ("Burial Location:", inspection.get('burial_location', ''))
    ]

    for label, value in fields:
        p.drawString(50, y, label)
        p.line(150, y - 2, 500, y - 2)
        p.drawString(155, y, str(value))
        y -= 20

    y -= 15

    # Section 2: Site Assessment
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SITE ASSESSMENT")
    y -= 25

    p.setFont("Helvetica", 10)
    assessment_fields = [
        ("Site Description:", inspection.get('site_description', '')),
        ("Proximity to Water Source:", inspection.get('proximity_water_source', '')),
        ("Proximity to Perimeter Boundaries:", inspection.get('proximity_perimeter_boundaries', '')),
        ("Proximity to Road/Pathway:", inspection.get('proximity_road_pathway', '')),
        ("Proximity to Trees:", inspection.get('proximity_trees', '')),
        ("Proximity to Houses/Buildings:", inspection.get('proximity_houses_buildings', '')),
        ("Proposed Grave Type:", inspection.get('proposed_grave_type', ''))
    ]

    for label, value in assessment_fields:
        if y < 100:
            p.showPage()
            y = height - 50
        p.drawString(50, y, label)
        p.line(200, y - 2, 500, y - 2)
        p.drawString(205, y, str(value))
        y -= 25

    y -= 15

    # Section 3: Remarks
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "GENERAL REMARKS")
    y -= 25

    p.setFont("Helvetica", 10)
    remarks = inspection.get('general_remarks', '')
    p.rect(50, y - 40, 500, 40)

    # Handle multi-line remarks
    if remarks:
        lines = []
        words = remarks.split()
        current_line = ""
        for word in words:
            if len(current_line + word) < 70:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        for i, line in enumerate(lines[:3]):  # Max 3 lines
            p.drawString(55, y - 15 - (i * 12), line)

    y -= 60

    # Section 4: Signatures
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SIGNATURES")
    y -= 25

    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Inspector Signature:")
    p.line(150, y - 2, 300, y - 2)
    p.drawString(155, y, inspection.get('inspector_signature', ''))

    p.drawString(350, y, "Received By:")
    p.line(420, y - 2, 550, y - 2)
    p.drawString(425, y, inspection.get('received_by', ''))

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=burial_form_{form_id}.pdf'
    return response


@app.route('/download_inspection_pdf/<int:form_id>')
def download_inspection_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    c.execute("""SELECT id, establishment_name, owner, address, license_no, inspector_name, 
                 inspection_date, inspection_time, type_of_establishment, purpose_of_visit, 
                 action, result, scores, comments, inspector_signature, received_by, 
                 created_at, inspector_code, no_of_employees, food_inspected, food_condemned, 
                 form_type, overall_score, critical_score FROM inspections WHERE id = ?""", (form_id,))
    form_data = c.fetchone()

    if not form_data:
        conn.close()
        return jsonify({'error': 'Inspection not found'}), 404

    # Get checklist scores
    c.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (form_id,))
    checklist_scores = {str(row[0]): float(row[1]) if row[1] and row[1].replace('.', '', 1).isdigit() else 0.0 for row
                        in c.fetchall()}
    conn.close()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    form_type = form_data[21]  # form_type

    # Form Header
    y = create_form_header(p, f"{form_type.upper()} INSPECTION FORM", form_id, width, height)

    # Basic Information Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "ESTABLISHMENT INFORMATION")
    y -= 25

    p.setFont("Helvetica", 10)
    basic_info = [
        ("Establishment Name:", form_data[1] or ''),
        ("Owner:", form_data[2] or ''),
        ("Address:", form_data[3] or ''),
        ("License No:", form_data[4] or ''),
        ("Inspector Name:", form_data[5] or ''),
        ("Inspector Code:", form_data[17] or ''),
        ("Inspection Date:", form_data[6] or ''),
        ("Inspection Time:", form_data[7] or ''),
        ("Type of Establishment:", form_data[8] or ''),
        ("No. of Employees:", form_data[18] or ''),
        ("Purpose of Visit:", form_data[9] or ''),
        ("Action:", form_data[10] or '')
    ]

    col1_x, col2_x = 50, 320
    col_y = y

    for i, (label, value) in enumerate(basic_info):
        if i % 2 == 0:  # Left column
            x = col1_x
            y = col_y
        else:  # Right column
            x = col2_x
            y = col_y
            col_y -= 20

        p.drawString(x, y, label)
        p.line(x + 100, y - 2, x + 250, y - 2)
        p.drawString(x + 105, y, str(value))

    y = col_y - 30

    # Food specific fields
    if form_type == "Food Establishment":
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "FOOD INSPECTION DETAILS")
        y -= 25

        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Food Inspected (kg): {form_data[19] or 0}")
        p.drawString(250, y, f"Food Condemned (kg): {form_data[20] or 0}")
        y -= 30

    # Checklist Section
    if y < 300:
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "INSPECTION CHECKLIST")
    y -= 25

    # Determine which checklist to use
    if form_type == "Food Establishment":
        checklist = FOOD_CHECKLIST_ITEMS
    elif form_type == "Spirit Licence Premises":
        checklist = SPIRIT_LICENCE_CHECKLIST_ITEMS
    elif form_type == "Swimming Pool":
        checklist = SWIMMING_POOL_CHECKLIST_ITEMS
    elif form_type == "Small Hotel":
        checklist = SMALL_HOTELS_CHECKLIST_ITEMS
    else:
        checklist = []

    # Checklist table header
    p.setFont("Helvetica-Bold", 9)
    p.drawString(50, y, "Item")
    p.drawString(80, y, "Description")
    p.drawString(400, y, "Weight")
    p.drawString(450, y, "Score")
    p.drawString(500, y, "✓")
    y -= 5
    p.line(50, y, 550, y)
    y -= 15

    p.setFont("Helvetica", 8)

    for item in checklist:
        if y < 50:
            p.showPage()
            y = height - 50
            # Redraw header
            p.setFont("Helvetica-Bold", 9)
            p.drawString(50, y, "Item")
            p.drawString(80, y, "Description")
            p.drawString(400, y, "Weight")
            p.drawString(450, y, "Score")
            p.drawString(500, y, "✓")
            y -= 5
            p.line(50, y, 550, y)
            y -= 15
            p.setFont("Helvetica", 8)

        item_id = str(item['id'])
        score = checklist_scores.get(item_id, 0)

        p.drawString(50, y, item_id)

        # Handle long descriptions
        desc = item.get('desc', item.get('description', ''))
        if len(desc) > 45:
            desc = desc[:42] + "..."
        p.drawString(80, y, desc)

        p.drawString(400, y, str(item.get('wt', item.get('weight', ''))))
        p.drawString(450, y, str(score))

        # Draw checkbox
        draw_checkbox(p, 505, y - 2, checked=(score > 0))

        y -= 12

    # Scoring Section
    y -= 20
    if y < 150:
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SCORING SUMMARY")
    y -= 25

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Overall Score: {form_data[22] or 0}")
    p.drawString(200, y, f"Critical Score: {form_data[23] or 0}")
    p.drawString(350, y, f"Result: {form_data[11] or ''}")
    y -= 40

    # Comments Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "COMMENTS")
    y -= 25

    p.rect(50, y - 60, 500, 60)
    p.setFont("Helvetica", 9)

    comments = form_data[13] or ''
    if comments:
        lines = []
        words = comments.split()
        current_line = ""
        for word in words:
            if len(current_line + word) < 70:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())

        for i, line in enumerate(lines[:5]):  # Max 5 lines
            p.drawString(55, y - 15 - (i * 10), line)

    y -= 80

    # Signatures Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SIGNATURES")
    y -= 25

    p.setFont("Helvetica", 10)
    p.drawString(50, y, "Inspector Signature:")
    p.line(150, y - 2, 300, y - 2)
    p.drawString(155, y, form_data[14] or '')

    p.drawString(350, y, "Received By:")
    p.line(420, y - 2, 550, y - 2)
    p.drawString(425, y, form_data[15] or '')

    y -= 30
    p.drawString(50, y, f"Date Completed: {form_data[16] or ''}")

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers[
        'Content-Disposition'] = f'attachment; filename={form_type.lower().replace(" ", "_")}_inspection_{form_id}.pdf'
    return response


@app.route('/download_residential_pdf/<int:form_id>')
def download_residential_pdf(form_id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    details = get_residential_inspection_details(form_id)
    if not details:
        return jsonify({'error': 'Inspection not found'}), 404

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Form Header
    y = create_form_header(p, "RESIDENTIAL & NON-RESIDENTIAL INSPECTION FORM", form_id, width, height)

    # Basic Information
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "PREMISES INFORMATION")
    y -= 25
    p.setFont("Helvetica", 10)
    basic_fields = [
        ("Name of Premises:", details.get('premises_name', '')),
        ("Owner/Agent/Occupier:", details.get('owner', '')),
        ("Address:", details.get('address', '')),
        ("Inspector Name:", details.get('inspector_name', '')),
        ("Inspector Code:", details.get('inspector_code', '')),
        ("Inspection Date:", details.get('inspection_date', '')),
        ("Treatment Facility:", details.get('treatment_facility', '')),
        ("Vector:", details.get('vector', '')),
        ("On-site System:", details.get('onsite_system', '')),
        ("Building Construction Type:", details.get('building_construction_type', '')),
        ("Purpose of Visit:", details.get('purpose_of_visit', '')),
        ("Action:", details.get('action', '')),
        ("No. of Bedrooms:", details.get('no_of_bedrooms', '')),
        ("Total Population:", details.get('total_population', ''))
    ]

    col1_x, col2_x = 50, 320
    col_y = y

    for i, (label, value) in enumerate(basic_fields):
        if i % 2 == 0:
            x = col1_x
            y = col_y
        else:
            x = col2_x
            y = col_y
            col_y -= 20

        p.drawString(x, y, label)
        p.line(x + 120, y - 2, x + 250, y - 2)
        p.drawString(x + 125, y, str(value))

    y = col_y - 30

    # Checklist Section
    if y < 400:
        p.showPage()
        y = height - 50

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "INSPECTION CHECKLIST")
    y -= 25

    # Checklist categories with proper sections
    categories = {
        "BUILDING CONDITION": [1, 2, 3, 4, 5, 6, 7, 8],
        "WATER SUPPLY": [9, 10],
        "DRAINAGE": [11, 12],
        "VECTOR CONTROL - MOSQUITOES": [13, 14],
        "VECTOR CONTROL - FLIES": [15, 16],
        "VECTOR CONTROL - RODENTS": [17, 18],
        "TOILET FACILITIES": [19, 20, 21, 22],
        "SOLID WASTE": [23, 24],
        "GENERAL": [25]
    }

    checklist_scores = details.get('checklist_scores', {})

    for category, items in categories.items():
        if y < 100:
            p.showPage()
            y = height - 50

        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, category)
        y -= 20

        p.setFont("Helvetica", 8)
        for item_id in items:
            item = next((item for item in RESIDENTIAL_CHECKLIST_ITEMS if item['id'] == item_id), None)
            if item:
                score = checklist_scores.get(str(item_id), 0)

                p.drawString(70, y, f"{item_id}.")
                p.drawString(90, y, item['desc'][:50] + ("..." if len(item['desc']) > 50 else ""))
                p.drawString(400, y, f"Weight: {item['wt']}")
                p.drawString(450, y, f"Score: {score}")
                draw_checkbox(p, 505, y - 2, checked=(float(score) > 0))
                y -= 15

        y -= 10

    # Scoring Summary
    y -= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "SCORING SUMMARY")
    y -= 25

    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Overall Score: {details.get('overall_score', 0)}")
    p.drawString(200, y, f"Critical Score: {details.get('critical_score', 0)}")
    p.drawString(350, y, f"Result: {details.get('result', '')}")

    p.save()
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=residential_inspection_{form_id}.pdf'
    return response

@app.route('/view_small_hotels/<int:inspection_id>')
def view_small_hotels(inspection_id):
    if 'inspector' not in session and 'admin' not in session:
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

    c.execute('''
        SELECT item_id, details, obser, error 
        FROM inspection_items WHERE inspection_id = ?
    ''', (inspection_id,))
    items = c.fetchall()

    inspection_dict = dict(inspection)
    inspection_dict['details'] = {item['item_id']: item['details'] for item in items}
    inspection_dict['obser'] = {item['item_id']: item['obser'] for item in items}
    inspection_dict['error'] = {item['item_id']: item['error'] for item in items}

    if inspection['scores']:
        scores = [float(x) for x in inspection['scores'].split(',')]
        inspection_dict['scores'] = dict(zip([item['id'].lower() for item in SMALL_HOTELS_CHECKLIST_ITEMS], scores))
    else:
        inspection_dict['scores'] = {item['id'].lower(): 0.0 for item in SMALL_HOTELS_CHECKLIST_ITEMS}

    conn.close()
    return render_template('small_hotel_inspection_detail.html',
                          inspection=inspection_dict,
                          checklist_items=SMALL_HOTELS_CHECKLIST_ITEMS)


@app.route('/spirit_licence/inspection/<int:id>')
def spirit_licence_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    conn.row_factory = sqlite3.Row  # This allows column access by name
    c = conn.cursor()

    c.execute("""SELECT * FROM inspections 
                 WHERE id = ? AND form_type = 'Spirit Licence Premises'""", (id,))
    inspection = c.fetchone()
    conn.close()

    if inspection:
        # Parse scores safely
        scores_str = inspection['scores'] if inspection['scores'] else ''
        if scores_str:
            try:
                scores = [int(x) for x in scores_str.split(',')]
                while len(scores) < 25:
                    scores.append(0)
            except ValueError:
                scores = [0] * 25
        else:
            scores = [0] * 25

        # Helper function to safely get values from Row object
        def safe_get(row, key, default=''):
            try:
                value = row[key]
                return value if value is not None else default
            except (KeyError, IndexError):
                return default

        inspection_data = {
            'id': inspection['id'],
            'establishment_name': safe_get(inspection, 'establishment_name'),
            'owner': safe_get(inspection, 'owner'),
            'address': safe_get(inspection, 'address'),
            'license_no': safe_get(inspection, 'license_no'),
            'inspector_name': safe_get(inspection, 'inspector_name'),
            'inspection_date': safe_get(inspection, 'inspection_date'),
            'inspection_time': safe_get(inspection, 'inspection_time'),
            'type_of_establishment': safe_get(inspection, 'type_of_establishment'),
            'purpose_of_visit': safe_get(inspection, 'purpose_of_visit'),
            'action': safe_get(inspection, 'action'),
            'result': safe_get(inspection, 'result'),
            'scores': {str(i): scores[i-1] for i in range(1, 26)},
            'comments': safe_get(inspection, 'comments'),
            'inspector_signature': safe_get(inspection, 'inspector_signature'),
            'received_by': safe_get(inspection, 'received_by'),
            'overall_score': safe_get(inspection, 'overall_score', 0),
            'critical_score': safe_get(inspection, 'critical_score', 0),
            'form_type': safe_get(inspection, 'form_type'),
            'no_of_employees': safe_get(inspection, 'no_of_employees'),
            'no_with_fhc': safe_get(inspection, 'no_with_fhc', 0),
            'no_wo_fhc': safe_get(inspection, 'no_wo_fhc', 0),
            'status': safe_get(inspection, 'status'),
            'created_at': safe_get(inspection, 'created_at')
        }

        return render_template('spirit_licence_inspection_detail.html',
                              checklist=[], inspection=inspection_data)

    return "Not Found", 404


@app.route('/swimming_pool/inspection/<int:id>')
def swimming_pool_inspection_detail(id):
    if 'inspector' not in session and 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    conn.row_factory = sqlite3.Row  # This allows access by column name
    cursor = conn.cursor()

    # Select ALL columns including the individual score columns
    cursor.execute("SELECT * FROM inspections WHERE id = ? AND form_type = 'Swimming Pool'", (id,))
    inspection = cursor.fetchone()

    if not inspection:
        conn.close()
        return "Inspection not found", 404

    # Convert to dictionary for easier template access
    inspection_dict = dict(inspection)

    # Fix the overall score - round to 1 decimal place
    if inspection_dict.get('overall_score'):
        inspection_dict['overall_score'] = round(float(inspection_dict['overall_score']), 1)

    # Fix the critical score - round to 1 decimal place
    if inspection_dict.get('critical_score'):
        inspection_dict['critical_score'] = round(float(inspection_dict['critical_score']), 1)

    # Fix manager signature field mapping
    # Check different possible field names for manager signature
    manager_signature = (
            inspection_dict.get('manager_signature') or
            inspection_dict.get('received_by') or
            inspection_dict.get('manager_name') or
            ''
    )
    inspection_dict['manager_signature'] = manager_signature

    # Debug: Print what scores we have
    print(f"=== DEBUG: Swimming Pool Inspection {id} ===")
    print(f"Overall Score: {inspection_dict.get('overall_score')}")
    print(f"Manager Signature: '{manager_signature}'")
    print(f"Received By: '{inspection_dict.get('received_by')}'")

    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        score_value = inspection_dict.get(score_field, 0)
        print(f"{score_field}: {score_value}")

    # Ensure all score fields exist with proper values
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if score_field not in inspection_dict or inspection_dict[score_field] is None:
            inspection_dict[score_field] = 0.0
        else:
            # Ensure it's a float
            inspection_dict[score_field] = float(inspection_dict[score_field])

    # Also get backup scores from inspection_items table
    cursor.execute("SELECT item_id, details FROM inspection_items WHERE inspection_id = ?", (id,))
    item_scores = {row[0]: float(row[1]) if row[1] and str(row[1]).replace('.', '', 1).isdigit() else 0.0
                   for row in cursor.fetchall()}

    conn.close()

    # If individual columns don't exist, use item_scores as fallback
    for item in SWIMMING_POOL_CHECKLIST_ITEMS:
        score_field = f"score_{item['id']}"
        if inspection_dict[score_field] == 0.0 and item['id'] in item_scores:
            inspection_dict[score_field] = item_scores[item['id']]
            print(f"Using fallback for {score_field}: {item_scores[item['id']]}")

    return render_template('swimming_pool_inspection_detail.html',
                           inspection=inspection_dict,
                           checklist=SWIMMING_POOL_CHECKLIST_ITEMS)

# Debug route for session verification
@app.route('/debug_session')
def debug_session():
    return jsonify(dict(session))


def get_db_connection():
    conn = sqlite3.connect('inspections.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('inspector', 'admin', 'medical_officer')),
        email TEXT,
        is_flagged INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL,
        login_time TEXT NOT NULL,
        ip_address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
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

    # Check if email column exists in users table and add it if not
    c.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in c.fetchall()]
    if 'email' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN email TEXT')
        conn.commit()

    # Insert default users
    try:
        c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                  ('admin', 'adminpass', 'admin', 'admin@example.com'))
        c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                  ('medofficer', 'medpass', 'medical_officer', 'medofficer@example.com'))
        for i in range(1, 7):
            c.execute('INSERT OR IGNORE INTO users (username, password, role, email) VALUES (?, ?, ?, ?)',
                      (f'inspector{i}', f'pass{i}', 'inspector', f'inspector{i}@example.com'))
        conn.commit()
    except sqlite3.IntegrityError as e:
        logging.error(f"Database integrity error: {str(e)}")

    conn.close()


# Replace your existing login_post() function with this updated version

def draw_checkbox(canvas, x, y, checked=False, size=10):
    """Draw a checkbox at the specified position"""
    canvas.rect(x, y, size, size)
    if checked:
        canvas.line(x + 2, y + 2, x + size - 2, y + size - 2)
        canvas.line(x + 2, y + size - 2, x + size - 2, y + 2)


def create_form_header(canvas, form_title, form_id, width, height):
    """Create standard form header"""
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(width/2, height-40, form_title)  # Fixed: drawCentredString instead of drawCentredText
    canvas.setFont("Helvetica", 10)
    canvas.drawString(50, height-60, f"Form ID: {form_id}")
    canvas.drawString(width-150, height-60, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    canvas.line(50, height-70, width-50, height-70)
    return height-90


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    login_type = request.form['login_type']
    ip_address = request.remote_addr

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, password, role, email FROM users WHERE username = ? AND password = ?",
              (username, password))
    user = c.fetchone()

    if user and (
            (login_type == 'inspector' and user['role'] == 'inspector') or
            (login_type == 'admin' and user['role'] == 'admin') or
            (login_type == 'medical_officer' and user['role'] == 'medical_officer')):
        session['user_id'] = user['id']
        session[login_type] = True

        # Record login attempt
        c.execute(
            "INSERT INTO login_history (user_id, username, email, role, login_time, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
            (user['id'], user['username'], user['email'], user['role'],
             datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ip_address))
        conn.commit()
        conn.close()

        # Log audit event
        log_audit_event(username, 'login', ip_address, f'Successful {login_type} login')

        if login_type == 'inspector':
            return redirect(url_for('dashboard'))
        elif login_type == 'admin':
            return redirect(url_for('admin'))
        else:  # medical_officer
            return redirect(url_for('medical_officer'))

    conn.close()

    # Log failed login attempt
    log_audit_event(username, 'login_failed', ip_address, f'Failed {login_type} login attempt')

    return render_template('login.html', error='Invalid credentials')


@app.route('/parish_leaderboard')
def parish_leaderboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('parish_leaderboard.html')


@app.route('/api/parish_stats')
def get_parish_stats():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get parish statistics
    c.execute("""
        SELECT 
            parish,
            COUNT(*) as total_inspections,
            SUM(CASE WHEN result = 'Pass' OR result = 'Satisfactory' THEN 1 ELSE 0 END) as passes,
            ROUND(
                (SUM(CASE WHEN result = 'Pass' OR result = 'Satisfactory' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 1
            ) as pass_rate
        FROM (
            SELECT parish, result FROM inspections WHERE parish IS NOT NULL
            UNION ALL
            SELECT parish, result FROM residential_inspections WHERE parish IS NOT NULL
        )
        GROUP BY parish
        ORDER BY pass_rate DESC
    """)

    parish_stats = []
    for row in c.fetchall():
        parish_stats.append({
            'parish': row[0],
            'total_inspections': row[1],
            'passes': row[2],
            'failures': row[1] - row[2],
            'pass_rate': row[3]
        })

    conn.close()
    return jsonify(parish_stats)


@app.route('/api/admin/users', methods=['GET'])
def get_users():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT id, username, email, role, is_flagged FROM users WHERE role = "inspector"')
        users = [{'id': row['id'], 'username': row['username'], 'email': row['email'],
                  'role': row['role'], 'is_flagged': row['is_flagged']} for row in c.fetchall()]
        return jsonify(users)
    finally:
        conn.close()


# Add these routes to your existing app.py file
# These are the missing routes needed for your admin dashboard

@app.route('/api/admin/audit_log')
def get_audit_log():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Create audit_log table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')

        # Get audit log entries
        cursor.execute('''
            SELECT timestamp, user, action, ip_address, details 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'timestamp': row[0],
                'user': row[1],
                'action': row[2],
                'ip_address': row[3],
                'details': row[4]
            })

        # If no audit logs exist, create some sample data from login history
        if not logs:
            cursor.execute('''
                SELECT login_time, username, 'login' as action, ip_address, role 
                FROM login_history 
                ORDER BY login_time DESC 
                LIMIT 50
            ''')
            for row in cursor.fetchall():
                logs.append({
                    'timestamp': row[0],
                    'user': row[1],
                    'action': row[2],
                    'ip_address': row[3],
                    'details': f'{row[4]} login'
                })

        conn.close()
        return jsonify(logs)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/update_database_schema')
def update_schema():
    """Run this once to update your database schema"""
    if 'admin' not in session:
        return "Admin access required"

    try:
        update_database_schema()
        return "✅ Database schema updated successfully! <a href='/admin'>Back to Admin</a>"
    except Exception as e:
        return f"❌ Error updating schema: {str(e)}"

# Add these routes to your app.py file

# Replace the existing backend routes in app.py with these fixed versions

@app.route('/api/inspector/tasks', methods=['GET'])
def get_inspector_tasks():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session.get('user_id')
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Get tasks assigned to this inspector
        cursor.execute('''
            SELECT id, title, due_date, details, status, created_at
            FROM tasks 
            WHERE assignee_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'title': row[1],
                'due_date': row[2],
                'details': row[3],
                'status': row[4],
                'created_at': row[5]
            })

        conn.close()
        return jsonify({'tasks': tasks})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/<int:task_id>/update', methods=['POST'])
def update_task_status(task_id):  # Fixed parameter name to match route
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        new_status = data.get('status')
        user_id = session.get('user_id')

        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Update task status (only if assigned to this inspector)
        cursor.execute('''
            UPDATE tasks 
            SET status = ?
            WHERE id = ? AND assignee_id = ?
        ''', (new_status, task_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Task not found or not assigned to you'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/<int:task_id>/respond', methods=['POST'])
def respond_to_task(task_id):
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        response = data.get('response')  # 'accept' or 'decline'
        user_id = session.get('user_id')

        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Update task status based on response
        if response == 'accept':
            new_status = 'In Progress'
        elif response == 'decline':
            new_status = 'Declined'
        else:
            conn.close()
            return jsonify({'error': 'Invalid response'}), 400

        cursor.execute('''
            UPDATE tasks 
            SET status = ?
            WHERE id = ? AND assignee_id = ?
        ''', (new_status, task_id, user_id))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Task not found or not assigned to you'}), 404

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_status': new_status})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/inspector/tasks/unread_count', methods=['GET'])
def get_unread_task_count():
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        user_id = session.get('user_id')
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Count unread tasks (status = 'Pending')
        cursor.execute('''
            SELECT COUNT(*) 
            FROM tasks 
            WHERE assignee_id = ? AND status = 'Pending'
        ''', (user_id,))

        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({'count': count})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/inspector_performance')
def get_inspector_performance():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        time_frame = request.args.get('time_frame', 'monthly')
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Get inspector performance from your existing tables
        cursor.execute('''
            SELECT 
                inspector_name,
                COUNT(*) as completed,
                AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate,
                '30 min' as avg_time,
                0 as overdue
            FROM (
                SELECT inspector_name, result FROM inspections
                WHERE inspector_name IS NOT NULL AND inspector_name != ''
                UNION ALL
                SELECT inspector_name, result FROM residential_inspections
                WHERE inspector_name IS NOT NULL AND inspector_name != ''
            ) 
            GROUP BY inspector_name
            HAVING inspector_name IS NOT NULL
        ''')

        inspectors = []
        for row in cursor.fetchall():
            inspectors.append({
                'name': row[0] or 'Unknown',
                'completed': row[1],
                'pass_rate': round(row[2], 1) if row[2] else 0,
                'avg_time': row[3],
                'overdue': row[4]
            })

        conn.close()
        return jsonify({'inspectors': inspectors})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/alerts')
def get_alerts():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        alerts = []

        # Check for failed inspections
        cursor.execute('''
            SELECT COUNT(*) FROM (
                SELECT result FROM inspections WHERE result = 'Fail'
                UNION ALL
                SELECT result FROM residential_inspections WHERE result = 'Fail'
            )
        ''')

        failed_count = cursor.fetchone()[0]

        if failed_count > 0:
            alerts.append({
                'title': 'Failed Inspections Alert',
                'description': f'{failed_count} inspections have failed and may need follow-up',
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            })

        # Check for recent inspections
        cursor.execute('''
            SELECT COUNT(*) FROM inspections 
            WHERE date(created_at) = date('now')
        ''')

        today_count = cursor.fetchone()[0]

        if today_count > 10:
            alerts.append({
                'title': 'High Activity Alert',
                'description': f'{today_count} inspections completed today',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })

        # Check for inspectors with high workload today
        cursor.execute('''
            SELECT inspector_name, COUNT(*) as count 
            FROM inspections 
            WHERE date(created_at) = date('now') AND inspector_name IS NOT NULL
            GROUP BY inspector_name 
            HAVING count > 5
        ''')

        for row in cursor.fetchall():
            alerts.append({
                'title': 'High Workload Alert',
                'description': f'Inspector {row[0]} has {row[1]} inspections today',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            })

        conn.close()
        return jsonify(alerts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/inspection_locations')
def get_inspection_locations():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        filter_type = request.args.get('filter', 'all')
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        locations = []

        # Get locations from your existing data
        cursor.execute('''
            SELECT 
                id, 
                'Food Establishment' as form_type, 
                result as status, 
                created_at as date,
                address,
                establishment_name
            FROM inspections
            WHERE form_type = 'Food Establishment'
            UNION ALL
            SELECT 
                id, 
                'Residential' as form_type, 
                result as status, 
                created_at as date,
                address,
                premises_name
            FROM residential_inspections
            LIMIT 50
        ''')

        # Sample coordinates around Kingston, Jamaica
        base_lat = 18.0179
        base_lng = -76.8099

        for i, row in enumerate(cursor.fetchall()):
            # Generate sample coordinates (you'd replace this with actual geocoding)
            lat_offset = (i % 20 - 10) * 0.01  # Random spread
            lng_offset = (i % 15 - 7) * 0.01

            locations.append({
                'form_id': row[0],
                'form_type': row[1],
                'status': row[2] or 'Unknown',
                'date': row[3],
                'address': row[4],
                'name': row[5],
                'latitude': base_lat + lat_offset,
                'longitude': base_lng + lng_offset
            })

        if filter_type != 'all':
            locations = [loc for loc in locations if loc['status'].lower() == filter_type.lower()]

        conn.close()
        return jsonify(locations)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/reports')
def get_reports():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        metric = request.args.get('metric', 'inspections')
        timeframe = request.args.get('timeframe', 'monthly')

        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        if metric == 'inspections':
            cursor.execute('''
                SELECT 
                    form_type as type,
                    COUNT(*) as count,
                    AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate
                FROM inspections
                WHERE form_type IS NOT NULL
                GROUP BY form_type
                UNION ALL
                SELECT 
                    'Residential' as type,
                    COUNT(*) as count,
                    AVG(CASE WHEN result = 'Pass' THEN 1 ELSE 0 END) * 100 as pass_rate
                FROM residential_inspections
            ''')

            data = []
            for row in cursor.fetchall():
                data.append([row[0], row[1], f"{row[2]:.1f}%" if row[2] else "0%"])

            report = {
                'summary': f'Inspection summary for {timeframe} period',
                'headers': ['Type', 'Count', 'Pass Rate'],
                'data': data
            }

        elif metric == 'user_activity':
            cursor.execute('''
                SELECT 
                    role,
                    COUNT(*) as logins
                FROM login_history
                GROUP BY role
            ''')

            data = []
            for row in cursor.fetchall():
                data.append([row[0], row[1]])

            report = {
                'summary': f'User activity summary for {timeframe} period',
                'headers': ['Role', 'Login Count'],
                'data': data
            }

        conn.close()
        return jsonify(report)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/system_health')
def get_system_health():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        # Get actual system metrics from your database
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Calculate some real metrics
        cursor.execute('SELECT COUNT(*) FROM inspections')
        total_inspections = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        # Generate health metrics (you can replace with actual monitoring)
        health = {
            'uptime': 99.5,
            'db_response': 45,  # milliseconds
            'error_rate': 0.2,
            'history': []
        }

        # Generate sample history data
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            health['history'].append({
                'timestamp': date.isoformat(),
                'uptime': 99.5 + (i * 0.01),
                'db_response': 45 + (i * 0.5),
                'error_rate': 0.2 + (i * 0.01)
            })

        conn.close()
        return jsonify(health)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Modify the existing tasks route to include notifications
@app.route('/api/admin/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Create tasks table if it doesn't exist - updated with notification field
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                assignee_id INTEGER,
                assignee_name TEXT,
                due_date TEXT,
                details TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_notified INTEGER DEFAULT 0
            )
        ''')

        if request.method == 'GET':
            cursor.execute('''
                SELECT id, title, assignee_name, due_date, status
                FROM tasks
                ORDER BY created_at DESC
            ''')

            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'title': row[1],
                    'assignee': row[2] or 'Unassigned',
                    'due_date': row[3],
                    'status': row[4]
                })

            conn.close()
            return jsonify(tasks)

        elif request.method == 'POST':
            data = request.get_json()

            # Get assignee name from users table
            cursor.execute('SELECT username FROM users WHERE id = ?', (data['assignee'],))
            user = cursor.fetchone()
            assignee_name = user[0] if user else 'Unknown'

            cursor.execute('''
                INSERT INTO tasks (title, assignee_id, assignee_name, due_date, details, status)
                VALUES (?, ?, ?, ?, ?, 'Pending')
            ''', (data['title'], data['assignee'], assignee_name, data['due_date'], data['details']))

            conn.commit()
            conn.close()
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/inspectors')
def get_inspectors():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Get inspectors from users table
        cursor.execute('''
            SELECT id, username 
            FROM users 
            WHERE role = 'inspector'
        ''')

        inspectors = []
        for row in cursor.fetchall():
            inspectors.append({
                'id': row[0],
                'name': row[1]
            })

        conn.close()
        return jsonify(inspectors)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/security_metrics')
def get_security_metrics():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Get user counts for MFA metrics (simulated)
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "inspector"')
        total_users = cursor.fetchone()[0]

        # Simulate MFA adoption (you'd track this in your users table)
        mfa_enabled = int(total_users * 0.7)
        mfa_disabled = total_users - mfa_enabled

        # Get recent login attempts as security events
        cursor.execute('''
            SELECT login_time, username, role, ip_address
            FROM login_history 
            ORDER BY login_time DESC 
            LIMIT 10
        ''')

        events = []
        for i, row in enumerate(cursor.fetchall()):
            events.append({
                'timestamp': row[0],
                'type': 'Login Attempt',
                'user': row[1],
                'details': f'Successful {row[2]} login from {row[3]}',
                'count': i + 1
            })

        metrics = {
            'mfa_enabled': mfa_enabled,
            'mfa_disabled': mfa_disabled,
            'events': events
        }

        conn.close()
        return jsonify(metrics)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/send_message', methods=['POST'])
def send_message():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        data = request.get_json()
        message = data.get('message', '')

        # Simple auto-reply logic
        if 'hello' in message.lower():
            reply = "Hello! How can I assist you today?"
        elif 'help' in message.lower():
            reply = "I'm here to help. What do you need assistance with?"
        elif 'status' in message.lower():
            reply = "All systems are operating normally."
        else:
            reply = f"Thank you for your message: '{message}'. An admin will respond shortly."

        return jsonify({
            'success': True,
            'reply': reply
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Helper function to log audit events (add this to your login routes)
def log_audit_event(user, action, ip_address=None, details=None):
    try:
        conn = sqlite3.connect('inspections.db')
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT
            )
        ''')

        cursor.execute('''
            INSERT INTO audit_log (timestamp, user, action, ip_address, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            user,
            action,
            ip_address or request.remote_addr if request else None,
            details
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit event: {e}")

@app.route('/api/admin/login_history', methods=['GET'])
def get_login_history():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute(
            'SELECT user_id, username, email, role, login_time, ip_address FROM login_history ORDER BY login_time DESC')
        history = [{'user_id': row['user_id'], 'username': row['username'], 'email': row['email'],
                    'role': row['role'], 'login_time': row['login_time'], 'ip_address': row['ip_address']}
                   for row in c.fetchall()]
        return jsonify(history)
    finally:
        conn.close()


@app.route('/api/admin/users', methods=['POST'])
def add_user():
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([username, email, password, role]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                  (username, email, password, role))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    finally:
        conn.close()


@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')

    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET email = ?, role = ? WHERE id = ?', (email, role, user_id))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/admin/users/<int:user_id>/flag', methods=['POST'])
def flag_user(user_id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    is_flagged = data.get('is_flagged', False)

    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET is_flagged = ? WHERE id = ?', (1 if is_flagged else 0, user_id))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user = c.fetchone()
        if user and user['role'] == 'admin':
            return jsonify({'success': False, 'error': 'Cannot delete admin user'}), 403
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


# ==================================================
# STEP 1: DATABASE SCHEMA UPDATES
# Add this to your database.py or run directly
# ==================================================

import sqlite3
from datetime import datetime


def init_form_management_db():
    """Initialize form management tables"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Form Templates Table - Different types of inspection forms
    c.execute('''CREATE TABLE IF NOT EXISTS form_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        form_type TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        version TEXT DEFAULT '1.0',
        created_by TEXT
    )''')

    # Form Items Table - Individual checklist items for each form
    c.execute('''CREATE TABLE IF NOT EXISTS form_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_template_id INTEGER NOT NULL,
        item_order INTEGER NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        weight INTEGER NOT NULL,
        is_critical INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (form_template_id) REFERENCES form_templates(id)
    )''')

    # Form Categories Table - For organizing items
    c.execute('''CREATE TABLE IF NOT EXISTS form_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        display_order INTEGER DEFAULT 0
    )''')

    # Insert default categories
    default_categories = [
        ('FOOD', 'Food related items', 1),
        ('FOOD PROTECTION', 'Food protection items', 2),
        ('EQUIPMENT & UTENSILS', 'Equipment and utensils', 3),
        ('FACILITIES', 'Facility requirements', 4),
        ('PERSONNEL', 'Personnel requirements', 5),
        ('SAFETY', 'Safety requirements', 6),
        ('GENERAL', 'General requirements', 7)
    ]

    for category in default_categories:
        c.execute('INSERT OR IGNORE INTO form_categories (name, description, display_order) VALUES (?, ?, ?)', category)

    # Insert existing form templates
    existing_templates = [
        ('Food Establishment Inspection', 'Standard food safety inspection form', 'Food Establishment'),
        ('Residential & Non-Residential Inspection', 'Residential property inspection form', 'Residential'),
        ('Burial Site Inspection', 'Burial site approval inspection', 'Burial'),
        ('Spirit Licence Premises Inspection', 'Spirit licence premises inspection', 'Spirit Licence Premises'),
        ('Swimming Pool Inspection', 'Swimming pool safety inspection', 'Swimming Pool'),
        ('Small Hotels Inspection', 'Small hotels inspection form', 'Small Hotel')
    ]

    for template in existing_templates:
        c.execute('INSERT OR IGNORE INTO form_templates (name, description, form_type) VALUES (?, ?, ?)', template)

    conn.commit()
    conn.close()


# ==================================================
# STEP 2: FLASK ROUTES TO ADD TO app.py
# Add these routes to your existing app.py
# ==================================================

# Form Management Routes
@app.route('/admin/forms')
def form_management():
    """Main form management page"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get all form templates with item counts
    c.execute('''
        SELECT ft.id, ft.name, ft.description, ft.form_type, ft.active, ft.version,
               COUNT(fi.id) as item_count
        FROM form_templates ft
        LEFT JOIN form_items fi ON ft.id = fi.form_template_id AND fi.active = 1
        GROUP BY ft.id
        ORDER BY ft.name
    ''')

    forms = c.fetchall()
    conn.close()

    return render_template('form_management.html', forms=forms)


@app.route('/admin/forms/edit/<int:form_id>')
def edit_form(form_id):
    """Edit existing form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get form template
    c.execute('SELECT * FROM form_templates WHERE id = ?', (form_id,))
    form_template = c.fetchone()

    if not form_template:
        conn.close()
        return redirect(url_for('form_management'))

    # Get form items
    c.execute('''
        SELECT id, item_order, category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_id,))
    items = c.fetchall()

    # Get categories
    c.execute('SELECT name FROM form_categories ORDER BY display_order')
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('form_editor.html',
                           form_template=form_template,
                           items=items,
                           categories=categories,
                           is_edit=True)


@app.route('/admin/forms/create')
def create_form():
    """Create new form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get categories
    c.execute('SELECT name FROM form_categories ORDER BY display_order')
    categories = [row[0] for row in c.fetchall()]

    conn.close()

    return render_template('form_editor.html',
                           form_template=None,
                           items=[],
                           categories=categories,
                           is_edit=False)


@app.route('/admin/forms/save', methods=['POST'])
def save_form():
    """Save form template and items"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        form_id = data.get('form_id')
        form_name = data.get('form_name')
        form_description = data.get('form_description')
        form_type = data.get('form_type')
        items = data.get('items', [])

        conn = sqlite3.connect('inspections.db')
        c = conn.cursor()

        if form_id:  # Update existing form
            c.execute('''
                UPDATE form_templates 
                SET name = ?, description = ?, form_type = ?, version = ?
                WHERE id = ?
            ''', (form_name, form_description, form_type, '1.1', form_id))

            # Deactivate existing items
            c.execute('UPDATE form_items SET active = 0 WHERE form_template_id = ?', (form_id,))

        else:  # Create new form
            c.execute('''
                INSERT INTO form_templates (name, description, form_type, created_by)
                VALUES (?, ?, ?, ?)
            ''', (form_name, form_description, form_type, session.get('user_id', 'admin')))
            form_id = c.lastrowid

        # Insert/update items
        for item in items:
            c.execute('''
                INSERT INTO form_items 
                (form_template_id, item_order, category, description, weight, is_critical)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (form_id, item['order'], item['category'], item['description'],
                  item['weight'], 1 if item.get('critical') else 0))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'form_id': form_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/delete/<int:form_id>', methods=['POST'])
def delete_form(form_id):
    """Delete form template"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        conn = sqlite3.connect('inspections.db')
        c = conn.cursor()

        # Soft delete - just mark as inactive
        c.execute('UPDATE form_templates SET active = 0 WHERE id = ?', (form_id,))
        c.execute('UPDATE form_items SET active = 0 WHERE form_template_id = ?', (form_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/clone/<int:form_id>', methods=['POST'])
def clone_form(form_id):
    """Clone existing form template"""
    if 'admin' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        conn = sqlite3.connect('inspections.db')
        c = conn.cursor()

        # Get original form
        c.execute('SELECT name, description, form_type FROM form_templates WHERE id = ?', (form_id,))
        original = c.fetchone()

        if not original:
            return jsonify({'success': False, 'error': 'Form not found'}), 404

        # Create clone
        clone_name = f"{original[0]} (Copy)"
        c.execute('''
            INSERT INTO form_templates (name, description, form_type, created_by)
            VALUES (?, ?, ?, ?)
        ''', (clone_name, original[1], original[2], session.get('user_id', 'admin')))

        new_form_id = c.lastrowid

        # Clone items
        c.execute('''
            INSERT INTO form_items 
            (form_template_id, item_order, category, description, weight, is_critical)
            SELECT ?, item_order, category, description, weight, is_critical
            FROM form_items WHERE form_template_id = ? AND active = 1
        ''', (new_form_id, form_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'form_id': new_form_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/admin/forms/preview/<int:form_id>')
def preview_form(form_id):
    """Preview form template"""
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get form template
    c.execute('SELECT * FROM form_templates WHERE id = ?', (form_id,))
    form_template = c.fetchone()

    # Get form items grouped by category
    c.execute('''
        SELECT category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_id,))

    items = c.fetchall()

    # Group items by category
    grouped_items = {}
    for item in items:
        category = item[0]
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append({
            'description': item[1],
            'weight': item[2],
            'is_critical': item[3]
        })

    conn.close()

    return render_template('form_preview.html',
                           form_template=form_template,
                           grouped_items=grouped_items)


@app.route('/api/forms/active')
def get_active_forms():
    """Get active forms for inspector dashboard"""
    if 'inspector' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    c.execute('''
        SELECT ft.id, ft.name, ft.description, ft.form_type,
               COUNT(fi.id) as item_count
        FROM form_templates ft
        LEFT JOIN form_items fi ON ft.id = fi.form_template_id AND fi.active = 1
        WHERE ft.active = 1
        GROUP BY ft.id
        ORDER BY ft.name
    ''')

    forms = []
    for row in c.fetchall():
        forms.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'form_type': row[3],
            'item_count': row[4]
        })

    conn.close()
    return jsonify({'forms': forms})


# Add these routes to your app.py to migrate your existing checklists

@app.route('/debug/forms')
def debug_forms():
    """Debug route to check what's in the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Check templates
    c.execute('SELECT * FROM form_templates')
    templates = c.fetchall()

    # Check items
    c.execute('SELECT * FROM form_items')
    items = c.fetchall()

    conn.close()

    return f"<h2>Form Templates ({len(templates)}):</h2><pre>{templates}</pre><br><br><h2>Form Items ({len(items)}):</h2><pre>{items}</pre>"


@app.route('/admin/migrate_all_checklists')
def migrate_all_checklists():
    """Migrate all existing checklists to the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    results = []

    # 1. Migrate Food Establishment Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Food Establishment',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            # Check if items already exist
            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for food items
                categories = {
                    1: "FOOD", 2: "FOOD",
                    3: "FOOD PROTECTION", 4: "FOOD PROTECTION", 5: "FOOD PROTECTION",
                    6: "FOOD PROTECTION", 7: "FOOD PROTECTION", 8: "FOOD PROTECTION",
                    9: "FOOD PROTECTION", 10: "FOOD PROTECTION",
                    11: "EQUIPMENT & UTENSILS", 12: "EQUIPMENT & UTENSILS", 13: "EQUIPMENT & UTENSILS",
                    14: "EQUIPMENT & UTENSILS", 15: "EQUIPMENT & UTENSILS", 16: "EQUIPMENT & UTENSILS",
                    17: "EQUIPMENT & UTENSILS", 18: "EQUIPMENT & UTENSILS", 19: "EQUIPMENT & UTENSILS",
                    20: "EQUIPMENT & UTENSILS", 21: "EQUIPMENT & UTENSILS", 22: "EQUIPMENT & UTENSILS",
                    23: "EQUIPMENT & UTENSILS",
                    24: "FACILITIES", 25: "FACILITIES", 26: "FACILITIES", 27: "FACILITIES", 28: "FACILITIES",
                    29: "PERSONNEL", 30: "PERSONNEL", 31: "PERSONNEL", 32: "PERSONNEL",
                    33: "FACILITIES", 34: "FACILITIES", 35: "FACILITIES", 36: "FACILITIES", 37: "FACILITIES",
                    38: "FACILITIES", 39: "FACILITIES", 40: "FACILITIES", 41: "FACILITIES",
                    42: "SAFETY", 43: "GENERAL", 44: "GENERAL", 45: "GENERAL"
                }

                # Insert each item from FOOD_CHECKLIST_ITEMS
                for item in FOOD_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 4 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Food Establishment: Migrated {len(FOOD_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Food Establishment: Already has {existing_count} items")
        else:
            results.append("❌ Food Establishment template not found")
    except Exception as e:
        results.append(f"❌ Food Establishment migration failed: {str(e)}")

    # 2. Migrate Residential Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Residential',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for residential items
                residential_categories = {
                    1: "BUILDING CONDITION", 2: "BUILDING CONDITION", 3: "BUILDING CONDITION",
                    4: "BUILDING CONDITION", 5: "BUILDING CONDITION", 6: "BUILDING CONDITION",
                    7: "BUILDING CONDITION", 8: "BUILDING CONDITION",
                    9: "WATER SUPPLY", 10: "WATER SUPPLY",
                    11: "DRAINAGE", 12: "DRAINAGE",
                    13: "VECTOR CONTROL - MOSQUITOES", 14: "VECTOR CONTROL - MOSQUITOES",
                    15: "VECTOR CONTROL - FLIES", 16: "VECTOR CONTROL - FLIES",
                    17: "VECTOR CONTROL - RODENTS", 18: "VECTOR CONTROL - RODENTS",
                    19: "TOILET FACILITIES", 20: "TOILET FACILITIES", 21: "TOILET FACILITIES", 22: "TOILET FACILITIES",
                    23: "SOLID WASTE", 24: "SOLID WASTE",
                    25: "GENERAL"
                }

                for item in RESIDENTIAL_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = residential_categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Residential: Migrated {len(RESIDENTIAL_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Residential: Already has {existing_count} items")
        else:
            results.append("❌ Residential template not found")
    except Exception as e:
        results.append(f"❌ Residential migration failed: {str(e)}")

    # 3. Migrate Spirit Licence Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Spirit Licence Premises',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                # Define categories for spirit licence items
                spirit_categories = {
                    1: "BUILDING CONDITION", 2: "BUILDING CONDITION", 3: "BUILDING CONDITION",
                    4: "BUILDING CONDITION", 5: "BUILDING CONDITION", 6: "BUILDING CONDITION",
                    7: "BUILDING CONDITION", 8: "BUILDING CONDITION", 9: "BUILDING CONDITION",
                    10: "LIGHTING", 11: "LIGHTING",
                    12: "WASHING FACILITIES", 13: "WASHING FACILITIES", 14: "WASHING FACILITIES",
                    15: "WASHING FACILITIES",
                    16: "WATER SUPPLY", 17: "WATER SUPPLY", 18: "WATER SUPPLY",
                    19: "STORAGE", 20: "STORAGE", 21: "STORAGE", 22: "STORAGE",
                    23: "SANITARY FACILITIES", 24: "SANITARY FACILITIES", 25: "SANITARY FACILITIES",
                    26: "SANITARY FACILITIES", 27: "SANITARY FACILITIES", 28: "SANITARY FACILITIES",
                    29: "WASTE MANAGEMENT", 30: "WASTE MANAGEMENT", 31: "WASTE MANAGEMENT", 32: "WASTE MANAGEMENT",
                    33: "PEST CONTROL", 34: "PEST CONTROL"
                }

                for item in SPIRIT_LICENCE_CHECKLIST_ITEMS:
                    item_id = item['id']
                    category = spirit_categories.get(item_id, "GENERAL")
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, item_id, category, item['description'], item['wt'], is_critical))

                results.append(f"✅ Spirit Licence: Migrated {len(SPIRIT_LICENCE_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Spirit Licence: Already has {existing_count} items")
        else:
            results.append("❌ Spirit Licence template not found")
    except Exception as e:
        results.append(f"❌ Spirit Licence migration failed: {str(e)}")

    # 4. Migrate Swimming Pool Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Swimming Pool',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(SWIMMING_POOL_CHECKLIST_ITEMS):
                    category = item.get('category', 'GENERAL')
                    is_critical = 1 if item['wt'] >= 5 else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['desc'], item['wt'], is_critical))

                results.append(f"✅ Swimming Pool: Migrated {len(SWIMMING_POOL_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Swimming Pool: Already has {existing_count} items")
        else:
            results.append("❌ Swimming Pool template not found")
    except Exception as e:
        results.append(f"❌ Swimming Pool migration failed: {str(e)}")

    # 5. Migrate Small Hotels Checklist
    try:
        c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Small Hotel',))
        result = c.fetchone()

        if result:
            template_id = result[0]

            c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
            existing_count = c.fetchone()[0]

            if existing_count == 0:
                for i, item in enumerate(SMALL_HOTELS_CHECKLIST_ITEMS):
                    # Determine category based on item ID pattern
                    item_id = item['id']
                    if item_id.startswith('1'):
                        category = "DOCUMENTATION"
                    elif item_id.startswith('2'):
                        category = "PERSONNEL"
                    elif item_id.startswith('3'):
                        category = "FOOD STORAGE"
                    elif item_id.startswith('4'):
                        category = "FOOD PREPARATION"
                    elif item_id.startswith('5'):
                        category = "WASTE MANAGEMENT"
                    elif item_id.startswith('6'):
                        category = "WASTE MANAGEMENT"
                    elif item_id.startswith('8'):
                        category = "SAFETY"
                    elif item_id.startswith('9'):
                        category = "FOOD SERVICE"
                    elif item_id.startswith('10'):
                        category = "FACILITIES"
                    elif item_id.startswith('12'):
                        category = "EQUIPMENT"
                    elif item_id.startswith('13'):
                        category = "OPERATIONS"
                    elif item_id.startswith('15'):
                        category = "UTILITIES"
                    elif item_id.startswith('16'):
                        category = "UTILITIES"
                    else:
                        category = "GENERAL"

                    is_critical = 1 if item.get('critical', False) else 0

                    c.execute('''
                        INSERT INTO form_items 
                        (form_template_id, item_order, category, description, weight, is_critical)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (template_id, i + 1, category, item['description'], 2.5, is_critical))

                results.append(f"✅ Small Hotels: Migrated {len(SMALL_HOTELS_CHECKLIST_ITEMS)} items")
            else:
                results.append(f"⚠️ Small Hotels: Already has {existing_count} items")
        else:
            results.append("❌ Small Hotels template not found")
    except Exception as e:
        results.append(f"❌ Small Hotels migration failed: {str(e)}")

    conn.commit()
    conn.close()

    # Format results as HTML
    html_results = "<h1>Checklist Migration Results</h1><ul>"
    for result in results:
        html_results += f"<li>{result}</li>"
    html_results += "</ul>"
    html_results += "<br><a href='/admin/forms'>Go to Form Management</a> | <a href='/debug/forms'>Debug Database</a>"

    return html_results


@app.route('/admin/reset_database')
def reset_database():
    """Reset and reinitialize the form management database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Clear existing data
    c.execute('DELETE FROM form_items')
    c.execute('DELETE FROM form_templates')
    c.execute('DELETE FROM form_categories')

    conn.commit()
    conn.close()

    # Reinitialize
    init_form_management_db()

    return "Database reset complete! <a href='/admin/migrate_all_checklists'>Run migration now</a>"
# ==================================================
# STEP 3: UPDATE EXISTING CHECKLIST LOADING
# Replace your existing checklist variables with dynamic loading
# ==================================================

def get_form_items(form_template_id):
    """Get form items for a specific template"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    c.execute('''
        SELECT id, item_order, category, description, weight, is_critical
        FROM form_items 
        WHERE form_template_id = ? AND active = 1
        ORDER BY item_order
    ''', (form_template_id,))

    items = []
    for row in c.fetchall():
        items.append({
            'id': row[0],
            'order': row[1],
            'category': row[2],
            'desc': row[3],
            'description': row[3],  # For compatibility
            'wt': row[4],
            'weight': row[4],  # For compatibility
            'critical': bool(row[5])
        })

    conn.close()
    return items


def get_form_template_by_type(form_type):
    """Get form template by type"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    c.execute('SELECT id FROM form_templates WHERE form_type = ? AND active = 1', (form_type,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else None


@app.route('/new_form')
def new_form():
    if 'inspector' not in session:
        return redirect(url_for('login'))

    # Force use static checklist (bypassing database)
    checklist = FOOD_CHECKLIST_ITEMS

    # Default inspection data for new form (your existing code)
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

    return render_template('inspection_form.html',
                           checklist=checklist,
                           inspections=get_inspections(),
                           show_form=True,
                           establishment_data=get_establishment_data(),
                           read_only=False,
                           inspection=inspection)


@app.route('/debug/forms_check')
def debug_forms_check():
    """Debug route to check what's in the database"""
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Check templates
    c.execute('SELECT * FROM form_templates')
    templates = c.fetchall()

    # Check items
    c.execute('SELECT * FROM form_items')
    items = c.fetchall()

    conn.close()

    return f"<h2>Form Templates ({len(templates)}):</h2><pre>{templates}</pre><br><br><h2>Form Items ({len(items)}):</h2><pre>{items}</pre>"


@app.route('/admin/migrate_food_checklist')
def migrate_food_checklist():
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Get Food Establishment template ID
    c.execute('SELECT id FROM form_templates WHERE form_type = ?', ('Food Establishment',))
    result = c.fetchone()

    if not result:
        return "Food Establishment template not found"

    template_id = result[0]

    # Check if items already exist
    c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
    existing_count = c.fetchone()[0]

    if existing_count > 0:
        return f"Items already exist: {existing_count} items found"

    # Insert your 45 FOOD_CHECKLIST_ITEMS
    categories = {
        1: "FOOD", 2: "FOOD",
        3: "FOOD PROTECTION", 4: "FOOD PROTECTION", 5: "FOOD PROTECTION",
        6: "FOOD PROTECTION", 7: "FOOD PROTECTION", 8: "FOOD PROTECTION",
        9: "FOOD PROTECTION", 10: "FOOD PROTECTION",
        11: "EQUIPMENT & UTENSILS", 12: "EQUIPMENT & UTENSILS", 13: "EQUIPMENT & UTENSILS",
        14: "EQUIPMENT & UTENSILS", 15: "EQUIPMENT & UTENSILS", 16: "EQUIPMENT & UTENSILS",
        17: "EQUIPMENT & UTENSILS", 18: "EQUIPMENT & UTENSILS", 19: "EQUIPMENT & UTENSILS",
        20: "EQUIPMENT & UTENSILS", 21: "EQUIPMENT & UTENSILS", 22: "EQUIPMENT & UTENSILS",
        23: "EQUIPMENT & UTENSILS",
        24: "FACILITIES", 25: "FACILITIES", 26: "FACILITIES", 27: "FACILITIES", 28: "FACILITIES",
        29: "PERSONNEL", 30: "PERSONNEL", 31: "PERSONNEL", 32: "PERSONNEL",
        33: "FACILITIES", 34: "FACILITIES", 35: "FACILITIES", 36: "FACILITIES", 37: "FACILITIES",
        38: "FACILITIES", 39: "FACILITIES", 40: "FACILITIES", 41: "FACILITIES",
        42: "SAFETY", 43: "GENERAL", 44: "GENERAL", 45: "GENERAL"
    }

    # Insert each item from your FOOD_CHECKLIST_ITEMS
    for item in FOOD_CHECKLIST_ITEMS:
        item_id = item['id']
        category = categories.get(item_id, "GENERAL")
        is_critical = 1 if item['wt'] >= 4 else 0

        c.execute('''
            INSERT INTO form_items 
            (form_template_id, item_order, category, description, weight, is_critical)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_id, item_id, category, item['desc'], item['wt'], is_critical))

    conn.commit()
    conn.close()

    return f"Successfully migrated {len(FOOD_CHECKLIST_ITEMS)} items! <a href='/admin/forms'>Check Form Management</a>"


@app.route('/admin/migrate_remaining_fixed')
def migrate_remaining_fixed():
    if 'admin' not in session:
        return "Admin access required"

    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()
    results = []

    # 1. Migrate Residential (Template ID 2)
    try:
        template_id = 2  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            residential_categories = {
                1: "BUILDING", 2: "BUILDING", 3: "BUILDING", 4: "BUILDING", 5: "BUILDING", 6: "BUILDING", 7: "BUILDING",
                8: "BUILDING",
                9: "WATER SUPPLY", 10: "WATER SUPPLY", 11: "DRAINAGE", 12: "DRAINAGE",
                13: "VECTOR CONTROL", 14: "VECTOR CONTROL", 15: "VECTOR CONTROL", 16: "VECTOR CONTROL",
                17: "VECTOR CONTROL", 18: "VECTOR CONTROL",
                19: "TOILET FACILITIES", 20: "TOILET FACILITIES", 21: "TOILET FACILITIES", 22: "TOILET FACILITIES",
                23: "SOLID WASTE", 24: "SOLID WASTE", 25: "GENERAL"
            }
            for item in RESIDENTIAL_CHECKLIST_ITEMS:
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, item['id'], residential_categories.get(item['id'], "GENERAL"),
                           item['desc'], item['wt'], 1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Residential: {len(RESIDENTIAL_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Residential: Already migrated")
    except Exception as e:
        results.append(f"❌ Residential failed: {str(e)}")

    # 2. Migrate Spirit Licence (Template ID 4)
    try:
        template_id = 4  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SPIRIT_LICENCE_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, "GENERAL", item['description'], item['wt'], 1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Spirit Licence: {len(SPIRIT_LICENCE_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Spirit Licence: Already migrated")
    except Exception as e:
        results.append(f"❌ Spirit Licence failed: {str(e)}")

    # 3. Migrate Swimming Pool (Template ID 5)
    try:
        template_id = 5  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SWIMMING_POOL_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, item.get('category', 'GENERAL'), item['desc'], item['wt'],
                           1 if item['wt'] >= 5 else 0))
            results.append(f"✅ Swimming Pool: {len(SWIMMING_POOL_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Swimming Pool: Already migrated")
    except Exception as e:
        results.append(f"❌ Swimming Pool failed: {str(e)}")

    # 4. Migrate Small Hotels (Template ID 6)
    try:
        template_id = 6  # From your debug output
        c.execute('SELECT COUNT(*) FROM form_items WHERE form_template_id = ?', (template_id,))
        if c.fetchone()[0] == 0:
            for i, item in enumerate(SMALL_HOTELS_CHECKLIST_ITEMS):
                c.execute('''INSERT INTO form_items (form_template_id, item_order, category, description, weight, is_critical)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (template_id, i + 1, "GENERAL", item['description'], 2.5,
                           1 if item.get('critical', False) else 0))
            results.append(f"✅ Small Hotels: {len(SMALL_HOTELS_CHECKLIST_ITEMS)} items")
        else:
            results.append("⚠️ Small Hotels: Already migrated")
    except Exception as e:
        results.append(f"❌ Small Hotels failed: {str(e)}")

    conn.commit()
    conn.close()

    return "<h1>Migration Results:</h1><ul>" + "".join(
        [f"<li>{r}</li>" for r in results]) + "</ul><br><a href='/admin/forms'>Check Form Management</a>"

if __name__ == '__main__':
    init_db()
    init_form_management_db()
    app.run(debug=True, port=5001)