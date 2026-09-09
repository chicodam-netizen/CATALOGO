import sqlite3
import json

DB_FILE = 'metadata.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS glossary (
            schema_name TEXT,
            table_name TEXT,
            column_name TEXT,
            business_name TEXT,
            description TEXT,
            domain_values TEXT,
            classification TEXT,
            is_mandatory BOOLEAN,
            is_unique BOOLEAN,
            PRIMARY KEY (schema_name, table_name, column_name)
        )
    ''')
    conn.commit()
    conn.close()

def save_metadata(schema_name, table_name, column_name, data: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO glossary 
        (schema_name, table_name, column_name, business_name, description, domain_values, classification, is_mandatory, is_unique)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(schema_name, table_name, column_name) DO UPDATE SET
            business_name=excluded.business_name,
            description=excluded.description,
            domain_values=excluded.domain_values,
            classification=excluded.classification,
            is_mandatory=excluded.is_mandatory,
            is_unique=excluded.is_unique
    ''', (
        schema_name, table_name, column_name,
        data.get('business_name'),
        data.get('description'),
        data.get('domain_values'),
        data.get('classification'),
        data.get('is_mandatory'),
        data.get('is_unique')
    ))
    conn.commit()
    conn.close()

def get_metadata(schema_name, table_name, column_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT business_name, description, domain_values, classification, is_mandatory, is_unique
        FROM glossary
        WHERE schema_name=? AND table_name=? AND column_name=?
    ''', (schema_name, table_name, column_name))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'business_name': row[0],
            'description': row[1],
            'domain_values': row[2],
            'classification': row[3],
            'is_mandatory': bool(row[4]),
            'is_unique': bool(row[5])
        }
    return None

def get_all_metadata(schema_name, table_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT column_name, business_name, description, domain_values, classification, is_mandatory, is_unique
        FROM glossary
        WHERE schema_name=? AND table_name=?
    ''', (schema_name, table_name))
    rows = cursor.fetchall()
    conn.close()
    
    res = {}
    for row in rows:
        res[row[0]] = {
            'business_name': row[1],
            'description': row[2],
            'domain_values': row[3],
            'classification': row[4],
            'is_mandatory': bool(row[5]),
            'is_unique': bool(row[6])
        }
    return res

# Initialize on module load
init_db()
