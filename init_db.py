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
    
    # 2. Users / Staff Table (Corrected columns to match streamlit_app.py perfectly)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
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
        name TEXT,
        grade TEXT,
        amount REAL,
        channel TEXT,
        reference TEXT,
        allocation TEXT,
        date_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # 5. Co-Curricular Gallery Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS co_curricular (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caption TEXT,
        image_blob BLOB
    )""")
    
    # 6. Teachers Directory Detail Table (For profile pictures)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        username TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        photo BLOB
    )""")
    
    # 🔐 Seed Primary System Administration Access Profiles
    cursor.execute("""
        INSERT OR REPLACE INTO users (username, full_name, password, role)
        VALUES ('Admin', 'Elijah Aloyo (System Admin)', ?, 'Admin')
    """, (hash_password("Admin@2026"),))
    
    cursor.execute("""
        INSERT OR REPLACE INTO users (username, full_name, password, role)
        VALUES ('Hellen', 'Madam Hellen Akinyi Maisori', ?, 'Admin')
    """, (hash_password("Kea@2026"),))
    
    # 👨‍🏫 Seed Complete Staff Profiles (Including your newly added teachers)
    # Format: (Username/First Name, Full Name, Password, System Role)
    default_teachers = [
        # Original Staff Members
        ("Eliars", "Mr. Eliars Opondo", "Kea@2026", "Subject Teacher"),
        ("Lucas", "Mr. Lucas Onyango", "Kea@2026", "Class Teacher"),
        ("Omwanda", "Mr. Vincent Omwanda", "Kea@2026", "Subject Teacher"),
        ("Grace", "Madam Grace Otieno", "Kea@2026", "Subject Teacher"),
        ("EliasA", "Mr. Elias Achiyo", "Kea@2026", "Subject Teacher"),
        ("Valentine", "Mr. Valentine Tiberius", "Kea@2026", "Subject Teacher"),
        
        # Newly Added Faculty Staff Members
        ("Alfred", "Mr. Alfred Ndira", "Kea@2026", "Subject Teacher"),
        ("Salmon", "Mr. Salmon Orem", "Kea@2026", "Subject Teacher"),
        ("Charles", "Mr. Charles Onyango", "Kea@2026", "Subject Teacher"),
        ("Herbert", "Mr. Herbert Ochieng", "Kea@2026", "Subject Teacher"),
        ("Aaron", "Mr. Aaron Baracks Obondo", "Kea@2026", "Subject Teacher")
    ]
    
    for user, full_name, pwd, sys_role in default_teachers:
        # Populate main security log entries
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, full_name, password, role)
            VALUES (?, ?, ?, ?)
        """, (user, full_name, hash_password(pwd), sys_role))
        
        # Populate metadata table for profile photo attachments
        cursor.execute("""
            INSERT OR IGNORE INTO teachers (username, name)
            VALUES (?, ?)
        """, (user, full_name))
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("🎯 Database successfully updated and seeded with new faculty credentials!")
