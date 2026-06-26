import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_database():
    conn = sqlite3.connect("school_data.db")
    cursor = conn.cursor()
    
    # 1. Students Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        adm_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        assessment_no TEXT NOT NULL,
        grade TEXT NOT NULL
    )""")
    
    # 2. Users / Staff Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        designation TEXT NOT NULL,
        photo BLOB
    )""")
    
    # 3. Academic Marks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marks (
        adm_no TEXT,
        grade TEXT,
        mathematics REAL DEFAULT 0,
        english REAL DEFAULT 0,
        kiswahili REAL DEFAULT 0,
        integrated_science REAL DEFAULT 0,
        agriculture REAL DEFAULT 0,
        pretechnical_studies REAL DEFAULT 0,
        social_studies REAL DEFAULT 0,
        religious_education REAL DEFAULT 0,
        cas REAL DEFAULT 0,
        PRIMARY KEY (adm_no, grade),
        FOREIGN KEY(adm_no) REFERENCES students(adm_no) ON DELETE CASCADE
    )""")
    
    # 4. Fee Payments Collection Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adm_no TEXT,
        amount REAL,
        channel TEXT,
        payer TEXT,
        payment_for TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(adm_no) REFERENCES students(adm_no) ON DELETE CASCADE
    )""")
    
    # 5. Termly Global Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS global_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('opening_date', '2026-09-01')")
    cursor.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('closing_date', '2026-11-28')")
    
    # 6. Newsletter Notices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS newsletter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        date_posted DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # 7. School Contact Settings & Photo Media Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_info (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cursor.execute("INSERT OR IGNORE INTO contact_info (key, value) VALUES ('map_embed', 'https://www.google.com/maps/embed')")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS co_curricular (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caption TEXT,
        image_blob BLOB
    )""")
    
    # Seed Primary System Administration Access Profiles
    cursor.execute("""
        INSERT OR REPLACE INTO users (username, full_name, password_hash, designation)
        VALUES ('Admin', 'Elijah Aloyo (System Admin)', ?, 'Head of Institution (HOI)')
    """, (hash_password("Admin@2026"),))
    
    cursor.execute("""
        INSERT OR REPLACE INTO users (username, full_name, password_hash, designation)
        VALUES ('Hellen', 'Madam Hellen Akinyi Maisori', ?, 'Head of Institution (HOI)')
    """, (hash_password("Kea@2026"),))
    
    # Seed Default Staff Profiles
    default_teachers = [
        ("Eliars", "Mr. Eliars Opondo", "Kea@2026", "Teacher"),
        ("Lucas", "Mr. Lucas Onyango", "Kea@2026", "Senior teacher"),
        ("Omwanda", "Mr. Vincent Omwanda", "Kea@2026", "Senior teacher"),
        ("Grace", "Madam Grace Otieno", "Kea@2026", "Teacher"),
        ("EliasA", "Mr. Elias Achiyo", "Kea@2026", "Junior Teacher"),
        ("Valentine", "Mr. Valentine Tiberius", "Kea@2026", "Junior Teacher")
    ]
    
    for user, name, pwd, desig in default_teachers:
        cursor.execute("INSERT OR IGNORE INTO users (username, full_name, password_hash, designation) VALUES (?, ?, ?, ?)",
                       (user, name, hash_password(pwd), desig))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
