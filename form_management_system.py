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