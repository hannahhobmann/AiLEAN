import ollama
import os
import PyPDF2

def load_manual(file_path):
    """Load the maintenance manual from a PDF."""
    if not os.path.exists(file_path):
        print(f"Error: '{file_path}' not found in {os.getcwd()}")
        return None
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            if not text:
                print("Error: No text extracted from PDF")
                return None
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
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

def get_response(issue, manual_content):
    """Generate a conversational response using Ollama."""
    client = ollama.Client(host='http://127.0.0.1:11434')
    relevant_info = extract_issue_info(issue, manual_content)
    prompt = (
        f"You are AiLEAN, a friendly military maintenance expert. "
        f"Respond to the user's issue conversationally. "
        f"Use this M4 Carbine manual info: {relevant_info[:2000]}... "
        f"User issue: '{issue}'. "
        f"Explain the fix step-by-step in a natural tone, without numbered lists. "
        f"Keep it under 100 words, simple, and supportive. "
        f"Start with a few word greeting, end with breif encouragement."
    )
    try:
        response = client.generate(model='llama3.2:latest', prompt=prompt, options={'timeout': 30})
        return response['response']
    except Exception as e:
        return f"Error: {e}. Try again or check the manual!"

def main():
    """Run the chatbot with error handling."""
    manual_file = "m4_manual.pdf"
    manual_content = load_manual(manual_file)
    if not manual_content:
        print("Cannot proceed without manual. Please ensure 'm4_manual.pdf' is in the project directory.")
        return
    print("I'm AilEAN, your M4 Maintenance Bot! How can I help with your M4? (e.g., 'My M4 won’t fire') Or, you can type 'exit' to quit.")
    while True:
        try:
            issue = input("What's the problem? ")
            if issue.lower() == 'exit':
                print("Bye!")
                break
            if not issue.strip():
                print("Please enter an issue, like 'My M4 won’t fire'.")
                continue
            response = get_response(issue, manual_content)
            print(f"\n{response}\n")
        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Oops, something went wrong: {e}. Try again!")

if __name__ == "__main__":
    main()
