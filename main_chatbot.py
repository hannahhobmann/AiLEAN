import sqlite3
import os
import PyPDF2
from offspring_chatbot import run_offspring_chatbot


def init_database():
    """Initialize SQLite database for manuals."""
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


def load_manual_database():
    """Load available manuals from the database."""
    try:
        conn = sqlite3.connect("military_manuals.db")
        cursor = conn.cursor()
        cursor.execute("SELECT equipment_id, equipment_name FROM manuals")
        manuals = cursor.fetchall()
        conn.close()
        return {row[1]: row[0] for row in manuals}
    except Exception as e:
        print(f"Error loading manual database: {e}")
        return {}


def add_new_manual():
    """Prompt user to upload a PDF and add it to the database."""
    print("\nTo add a new manual, provide the PDF file path and a name for it.")
    file_path = input("Enter the full path to the PDF file: ").strip()
    if not os.path.exists(file_path) or not file_path.lower().endswith(".pdf"):
        print("Error: Invalid PDF file path or not a PDF.")
        return None

    equipment_name = input("Enter a name for this equipment: ").strip()
    if not equipment_name:
        print("Error: Equipment name cannot be empty.")
        return None

    # Extract text from PDF
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            if not text:
                print("Error: No text extracted from PDF.")
                return None
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

    # Save to database
    try:
        conn = sqlite3.connect("military_manuals.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO manuals (equipment_name, manual_content) VALUES (?, ?)",
            (equipment_name, text)
        )
        conn.commit()
        if cursor.rowcount == 0:
            conn.close()
            print(f"Error: A manual for '{equipment_name}' already exists.")
            return None

        # Get the ID of the newly inserted manual
        cursor.execute("SELECT equipment_id FROM manuals WHERE equipment_name = ?", (equipment_name,))
        equipment_id = cursor.fetchone()[0]
        conn.close()

        print(f"Manual for '{equipment_name}' added successfully!")
        return equipment_id, equipment_name
    except Exception as e:
        print(f"Error adding manual to database: {e}")
        return None


def display_available_manuals(database):
    """Display available manuals in a numbered list."""
    if not database:
        print("No manuals currently available.")
        return

    print("\nAvailable Manuals:")
    for i, equipment_name in enumerate(database.keys(), 1):
        print(f"{i}. {equipment_name}")


def get_user_choice(database):
    """Get user's choice for manual selection or adding new manual."""
    print("\nOptions:")
    print("• Type the name of an existing manual to select it")
    print("• Type 'add' to upload a new manual")
    print("• Type 'exit' to quit")

    choice = input("\n> ").strip()

    if choice.lower() == 'exit':
        return 'exit', None, None
    elif choice.lower() == 'add':
        return 'add', None, None
    else:
        # Check if it's a manual name or number
        equipment_list = list(database.keys())

        # Try to match by number first
        try:
            selection_num = int(choice)
            if 1 <= selection_num <= len(database):
                equipment_name = equipment_list[selection_num - 1]
                equipment_id = database[equipment_name]
                return 'select', equipment_id, equipment_name
        except ValueError:
            pass

        # Try to match by name (case-insensitive)
        for equipment_name in database.keys():
            if choice.lower() == equipment_name.lower():
                equipment_id = database[equipment_name]
                return 'select', equipment_id, equipment_name

        # No match found
        return 'invalid', None, None


def main():
    """Run the main chatbot interface."""
    init_database()
    print("Welcome to AiLEAN, your Universal Military Maintenance Bot!")

    while True:
        try:
            # Load current database
            database = load_manual_database()

            # Display available manuals
            display_available_manuals(database)

            # Get user choice
            action, equipment_id, equipment_name = get_user_choice(database)

            if action == 'exit':
                print("Goodbye!")
                break
            elif action == 'select':
                print(f"\nLaunching AiLEAN for {equipment_name}...")
                run_offspring_chatbot(equipment_id, equipment_name)
            elif action == 'add':
                result = add_new_manual()
                if result:
                    equipment_id, equipment_name = result
                    print(f"\nLaunching AiLEAN for {equipment_name}...")
                    run_offspring_chatbot(equipment_id, equipment_name)
            elif action == 'invalid':
                print("Invalid selection. Please try again.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Please try again!")


if __name__ == "__main__":
    main()