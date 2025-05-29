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
        return False
    equipment_name = input("Enter a name for this equipment: ").strip()
    if not equipment_name:
        print("Error: Equipment name cannot be empty.")
        return False

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
                return False
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return False

    # Save to database
    try:
        conn = sqlite3.connect("military_manuals.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO manuals (equipment_name, manual_content) VALUES (?, ?)",
            (equipment_name, text)
        )
        conn.commit()
        conn.close()
        if cursor.rowcount == 0:
            print(f"Error: A manual for '{equipment_name}' already exists.")
            return False
        print(f"Manual for '{equipment_name}' added successfully!")
        return True
    except Exception as e:
        print(f"Error adding manual to database: {e}")
        return False


def display_manuals(database):
    """Display available manuals."""
    if not database:
        print("No manuals available. Please add a manual first.")
        return False
    print("\nAvailable Manuals:")
    for i, equipment_name in enumerate(database.keys(), 1):
        print(f"{i}. {equipment_name}")
    print("\nEnter the number or the exact equipment name to select a manual.")
    return True


def main():
    """Run the main chatbot interface."""
    init_database()  # Initialize database
    print("Welcome to AiLEAN, your Universal Military Maintenance Bot!")
    print("Select a manual to troubleshoot or add a new one.")

    while True:
        try:
            database = load_manual_database()
            if not display_manuals(database):
                print("Would you like to add a new manual? (y/n)")
                if input("> ").lower() == 'y':
                    add_new_manual()
                continue

            print("\nOptions:")
            print("1. Select a manual to troubleshoot")
            print("2. Add a new manual")
            print("3. Exit")
            choice = input("> ").strip()

            if choice == "1":
                if database:
                    selection = input("Enter the number or equipment name: ").strip()
                    equipment_name = None
                    equipment_id = None
                    # Create a list of equipment names to maintain order
                    equipment_list = list(database.keys())
                    # Check if input is a number
                    try:
                        selection_num = int(selection)
                        if 1 <= selection_num <= len(database):
                            equipment_name = equipment_list[selection_num - 1]
                            equipment_id = database[equipment_name]
                    except ValueError:
                        # Input is not a number, try matching equipment name
                        if selection in database:
                            equipment_name = selection
                            equipment_id = database[equipment_name]

                    if equipment_name and equipment_id:
                        print(f"\nLaunching AiLEAN for {equipment_name}...")
                        run_offspring_chatbot(equipment_id, equipment_name)
                    else:
                        print("Invalid selection. Enter a valid number or equipment name.")
            elif choice == "2":
                add_new_manual()
            elif choice == "3":
                print("Bye!")
                break
            else:
                print("Invalid option. Choose 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Try again!")


if __name__ == "__main__":
    main()