import ollama
import os

def load_manual(file_path):
    """Load the maintenance manual."""
    if not os.path.exists(file_path):
        print(f"Error: '{file_path}' not found in {os.getcwd()}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading manual: {e}")
        return None

def get_response(issue, manual_content):
    """Generate a response using Ollama."""
    client = ollama.Client(host='http://127.0.0.1:11434')
    prompt = (
        f"You are a friendly AI assistant for military maintenance workers. "
        f"Based on this M4 Carbine manual excerpt: {manual_content[:1000]}... "
        f"User issue: '{issue}'. "
        f"Provide 3-5 clear, numbered steps to fix the issue in under 80 words. "
        f"Use simple language and start with a short greeting."
    )
    try:
        response = client.generate(model='llama3.2:latest', prompt=prompt, options={'timeout': 30})
        return response['response']
    except Exception as e:
        return f"Sorry, I hit an issue: {e}. Check the manual or try again."

def main():
    manual_file = "m4_manual.txt"
    manual_content = load_manual(manual_file)
    if not manual_content:
        return
    print("Welcome to the M4 Maintenance Bot! Enter an issue (e.g., 'My M4 won’t fire') or 'exit' to quit.")
    while True:
        issue = input("What's the problem? ")
        if issue.lower() == 'exit':
            print("Goodbye!")
            break
        response = get_response(issue, manual_content)
        print(f"\n{response}\n")

if __name__ == "__main__":
    main()