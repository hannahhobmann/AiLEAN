import sqlite3

def create_database():
    conn = sqlite3.connect("military_manuals.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manuals (
            equipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_name TEXT NOT NULL UNIQUE,
            manual_content TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_name ON manuals (equipment_name)")
    conn.commit()
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    create_database()