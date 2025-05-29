import ollama
import sqlite3
from datetime import datetime


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
    # Generic keywords for troubleshooting sections
    generic_keywords = [
        "troubleshoot",
        "troubleshooting",
        "maintenance",
        "repair",
        "issue",
        "problem",
        "failure",
        "error"
    ]
    # Search for issue-related keywords in user input
    for keyword in generic_keywords:
        if keyword in issue.lower():
            # Look for a section containing the keyword
            start_idx = manual_content.lower().find(keyword)
            if start_idx != -1:
                # Extract section up to the next major heading or end
                end_idx = manual_content.lower().find("section", start_idx + 1)
                if end_idx == -1:
                    end_idx = manual_content.lower().find("chapter", start_idx + 1)
                if end_idx == -1:
                    end_idx = len(manual_content)
                return manual_content[start_idx:end_idx].strip()
    # Fallback: Look for a troubleshooting or maintenance section
    for section in ["troubleshooting", "maintenance", "repair procedures"]:
        start_idx = manual_content.lower().find(section)
        if start_idx != -1:
            end_idx = manual_content.lower().find("section", start_idx + 1)
            if end_idx == -1:
                end_idx = manual_content.lower().find("chapter", start_idx + 1)
            if end_idx == -1:
                end_idx = len(manual_content)
            return manual_content[start_idx:end_idx].strip()
    # Default: Return first 2000 characters
    return manual_content[:2000]


def get_response(issue, manual_content, equipment_name, is_first_prompt=True):
    """Generate a conversational response using Ollama."""
    client = ollama.Client(host='http://localhost:11434')
    relevant_info = extract_issue_info(issue, manual_content)

    # Determine greeting based on time of day
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # Build prompt based on whether it's the first prompt
    if is_first_prompt:
        prompt = (
            f"You are AiLEAN, a friendly military maintenance expert. "
            f"{greeting}. "
            f"Respond to the user's issue conversationally, in minimal sentences, and very straightforward. "
            f"Use this {equipment_name} manual info: {relevant_info[:2000]}... "
            f"User issue: '{issue}'. "
            f"Explain the fix step-by-step in a natural tone, without numbered lists. "
            f"Keep it brief, simple, and supportive. "
            f"End with brief encouragement. "
            f"Only use a greeting and encouraging ending for the first prompt. "
            f"Don't introduce yourself again after the first prompt. "
            f"Never tell the user to reference the manual. Your job is to replace them having to check the manual. "
            f"Do not assume specific variants or models of the equipment unless specified by the user."
        )
    else:
        prompt = (
            f"Respond to the user's issue conversationally, in minimal sentences, and very straightforward. "
            f"Use this {equipment_name} manual info: {relevant_info[:2000]}... "
            f"User issue: '{issue}'. "
            f"Explain the fix step-by-step in a natural tone, without numbered lists. "
            f"Keep it brief, simple, and supportive. "
            f"Do not assume specific variants or models of the equipment unless specified by the user."
        )

    try:
        response = client.generate(model='llama3.2:latest', prompt=prompt, options={'timeout': 30})
        return response['response']
    except Exception as e:
        return f"Error: {e}. Try again."


def run_offspring_chatbot(equipment_id, equipment_name):
    """Run the chatbot for a specific manual."""
    manual_content = load_manual(equipment_id)
    if not manual_content:
        print(f"Cannot proceed without {equipment_name} manual.")
        return
    print(
        f"\nI'm AiLEAN, your {equipment_name} Maintenance Bot! How can I help? (e.g., 'My equipment won’t work') Or, type 'exit' to return to the main menu.")
    is_first_prompt = True
    greetings = ["good morning", "good afternoon", "good evening", "hello", "hi"]

    while True:
        try:
            issue = input("> ").strip().lower()
            if issue == 'exit':
                print("Returning to main menu...")
                break
            if not issue:
                print(f"Please enter an issue related to {equipment_name}.")
                continue
            # Check if input is a greeting
            if any(greeting in issue for greeting in greetings):
                current_hour = datetime.now().hour
                if current_hour < 12:
                    response = f"Good morning! How can I assist with your {equipment_name} today?"
                elif current_hour < 18:
                    response = f"Good afternoon! How can I assist with your {equipment_name} today?"
                else:
                    response = f"Good evening! How can I assist with your {equipment_name} today?"
                print(f"\n{response}\n")
                continue
            # Process as an issue
            response = get_response(issue, manual_content, equipment_name, is_first_prompt)
            print(f"\n{response}\n")
            is_first_prompt = False  # Disable greeting/encouragement after first prompt
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Try again!")


if __name__ == "__main__":
    print("This module is not meant to be run directly. Run main_chatbot.py instead.")