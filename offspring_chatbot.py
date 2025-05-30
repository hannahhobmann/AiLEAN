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
    """Extract relevant manual info based on the user's question or issue."""
    issue_lower = issue.lower()

    # Comprehensive equipment-related terms for different types of manuals
    equipment_terms = {
        # Aircraft terms
        'specifications': ['wingspan', 'length', 'height', 'weight', 'dimensions', 'specs', 'specifications'],
        'engine': ['engine', 'propeller', 'power plant', 'turboprop', 'horsepower', 'rpm'],
        'landing gear': ['landing', 'gear', 'touchdown', 'approach', 'wheels', 'struts'],
        'flight operations': ['takeoff', 'departure', 'climb', 'cruise', 'descent', 'flight'],
        'fuel system': ['fuel', 'gas', 'tank', 'consumption', 'capacity', 'gallons'],
        'electrical': ['electrical', 'power', 'battery', 'generator', 'voltage', 'amperage'],
        'hydraulic': ['hydraulic', 'fluid', 'pressure', 'pump'],
        'navigation': ['navigation', 'nav', 'compass', 'gps', 'instruments'],
        'communication': ['communication', 'radio', 'comm', 'frequency'],
        'cargo': ['cargo', 'load', 'weight', 'payload', 'capacity'],
        'flight controls': ['controls', 'rudder', 'elevator', 'aileron', 'flaps'],
        'instruments': ['instruments', 'gauges', 'display', 'panel', 'cockpit'],
        'systems': ['system', 'oxygen', 'ods', 'breathing', 'life support', 'environmental'],

        # Weapon/Vehicle terms
        'ammunition': ['ammo', 'ammunition', 'rounds', 'magazine', 'cartridge'],
        'barrel': ['barrel', 'muzzle', 'rifling', 'bore'],
        'trigger': ['trigger', 'firing', 'safety', 'selector'],
        'maintenance': ['cleaning', 'lubrication', 'inspection', 'service'],

        # General mechanical terms
        'operation': ['operation', 'operating', 'function', 'how to', 'procedure'],
        'performance': ['performance', 'capability', 'range', 'speed', 'rate']
    }

    # Find relevant content based on what the user is asking about
    found_content = []

    for category, keywords in equipment_terms.items():
        for keyword in keywords:
            if keyword in issue_lower:
                # Search for this keyword in the manual
                search_positions = []
                start_pos = 0

                # Find all occurrences of this keyword
                while True:
                    pos = manual_content.lower().find(keyword, start_pos)
                    if pos == -1:
                        break
                    search_positions.append(pos)
                    start_pos = pos + 1

                # Extract content around each occurrence
                for pos in search_positions:
                    # Get surrounding context
                    start_idx = max(0, pos - 300)
                    end_idx = min(len(manual_content), pos + 1200)

                    # Try to find natural boundaries (paragraphs, sections)
                    section_start = manual_content.rfind('\n\n', start_idx, pos)
                    if section_start != -1:
                        start_idx = section_start + 2

                    section_end = manual_content.find('\n\n', pos, end_idx)
                    if section_end != -1:
                        end_idx = section_end

                    extracted = manual_content[start_idx:end_idx].strip()
                    if len(extracted) > 50 and extracted not in found_content:
                        found_content.append(extracted)

    # If we found specific content, return the most relevant pieces
    if found_content:
        # Combine the most relevant sections (up to 3000 characters)
        combined_content = '\n\n'.join(found_content)
        return combined_content[:3000]

    # If the user indicates a problem, look for troubleshooting content
    problem_indicators = [
        'not working', 'broken', 'failed', 'error', 'problem', 'issue',
        'malfunction', 'stuck', 'jammed', 'won\'t start', 'won\'t turn',
        'leaking', 'smoking', 'overheating', 'strange noise', 'vibration',
        'fix', 'repair', 'troubleshoot'
    ]

    has_problem = any(indicator in issue_lower for indicator in problem_indicators)

    if has_problem:
        # Look for troubleshooting sections
        troubleshooting_keywords = [
            "troubleshoot", "troubleshooting", "maintenance", "repair",
            "failure", "malfunction", "corrective action", "fault", "defect"
        ]

        for keyword in troubleshooting_keywords:
            start_idx = manual_content.lower().find(keyword)
            if start_idx != -1:
                end_idx = manual_content.lower().find("section", start_idx + 1)
                if end_idx == -1:
                    end_idx = manual_content.lower().find("chapter", start_idx + 1)
                if end_idx == -1:
                    end_idx = min(len(manual_content), start_idx + 2000)

                return manual_content[start_idx:end_idx].strip()

    # If nothing specific found, return general information from the beginning
    return manual_content[:2000]


def get_response(issue, manual_content, equipment_name, conversation_history, is_first_prompt=True):
    """Generate a conversational response using Ollama."""
    client = ollama.Client(host='http://localhost:11434')
    relevant_info = extract_issue_info(issue, manual_content)

    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    history_text = ""
    if conversation_history:
        history_text = "Previous conversation:\n"
        for user_issue, bot_response in conversation_history[-3:]:
            history_text += f"User: {user_issue}\nBot: {bot_response}\n"

    if is_first_prompt:
        prompt = (
            f"You are AiLEAN, a friendly military maintenance expert. "
            f"{greeting}. "
            f"Respond to the user's issue conversationally, in minimal sentences, and very straightforward. "
            f"Use this {equipment_name} manual info: {relevant_info[:2000]}... "
            f"{history_text}"
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
            f"{history_text}"
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
    conversation_history = []

    while True:
        try:
            issue = input("> ").strip().lower()
            if issue == 'exit':
                print("Returning to main menu...")
                break
            if not issue:
                print(f"Please enter an issue related to {equipment_name}.")
                continue
            # Check if input is exactly a greeting
            if issue in greetings:
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
            response = get_response(issue, manual_content, equipment_name, conversation_history, is_first_prompt)
            print(f"\n{response}\n")
            conversation_history.append((issue, response))
            is_first_prompt = False
        except KeyboardInterrupt:
            print("\nReturning to main menu...")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Try again!")


if __name__ == "__main__":
    print("This module is not meant to be run directly. Run main_chatbot.py instead.")