import ollama
import sqlite3

def load_manual(equipment_id):
    """Load manual content from the database using equipment_id."""
    try:
        conn = sqlite3.connect("military_manuals.db")
        cursor = conn.cursor()
        cursor.execute("SELECT manual_content FROM manuals WHERE equipment_id = ?", (equipment_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        print(f"Error: No content found for equipment ID {equipment_id}")
        return None
    except Exception as e:
        print(f"Error loading manual from database: {e}")
        return None

def extract_issue_info(issue, manual_content):
    """Extract relevant manual info based on the issue."""
    issue_keywords = {
        "failure to fire": "Issue: Failure to Fire",
        "failure to feed": "Issue: Failure to Feed",
        "clean": "Cleaning:",
    }
    for keyword, manual_section in issue_keywords.items():
        if keyword in issue.lower():
            start_idx = manual_content.lower().find(manual_section.lower())
            if start_idx != -1:
                end_idx = manual_content.find("Issue:", start_idx + 1)
                if end_idx == -1:
                    end_idx = manual_content.find("CHAPTER", start_idx + 1)
                if end_idx == -1:
                    end_idx = len(manual_content)
                return manual_content[start_idx:end_idx].strip()
    start_idx = manual_content.find("2-3. TROUBLESHOOTING")
    if start_idx != -1:
        end_idx = manual_content.find("CHAPTER 3:", start_idx + 1)
        if end_idx == -1:
            end_idx = len(manual_content)
        return manual_content[start_idx:end_idx].strip()
    return manual_content[:2000]

def get_response(issue, manual_content, equipment_name):
    """Generate a conversational response using Ollama."""
    client = ollama.Client(host='http://127.0.0.1:11434')
    relevant_info = extract_issue_info(issue, manual_content)
    prompt = (
        f"You are AiLEAN, a friendly military maintenance expert. "
        f"Respond to the user's issue conversationally, but in minimal sentences and very be straighforward. "
        f"Use this M4 Carbine manual info: {relevant_info[:2000]}... "
        f"User issue: '{issue}'. "
        f"Explain the fix step-by-step in a natural tone, without numbered lists. "
        f"Keep it breif, simple, and supportive. "
        f"Start with a few word greeting, end with breif encouragement only for the first prompt"
        f"Don't introduce yourself a second time after the user asks their question."
        f"only use a greeting after or encouraging ending for the first user input. Anything after that just give a direct response."
        f"Never tell the user to reference the manual. Your job is to replace them having to check the manual"
    )
    try:
        response = client.generate(model='llama3.2:latest', prompt=prompt, options={'timeout': 30})
        return response['response']
    except Exception as e:
        return f"Error: {e}. Try again or check the manual!"

def run_offspring_chatbot(equipment_id, equipment_name):
    """Run the chatbot for a specific manual."""
    manual_content = load_manual(equipment_id)
    if not manual_content:
        print(f"Cannot proceed without {equipment_name} manual.")
        return
    print(f"\nI'm AiLEAN, your {equipment_name} Maintenance Bot! How can I help? (e.g., 'My equipment won’t work') Or, type 'exit' to return to the main menu.")
    while True:
        try:
            issue = input("> ")
            if issue.lower() == 'exit':
                print("Returning to main menu...")
                break
            if not issue.strip():
                print(f"Please enter an issue related to {equipment_name}.")
                continue
            response = get_response(issue, manual_content, equipment_name)
            print(f"\n{response}\n")
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Try again!")

if __name__ == "__main__":
    print("This module is not meant to be run directly. Run main_chatbot.py instead.")