import logging
from clients import bootstrap_client_and_model
from list_models import list_available_models

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def chat_with_ai():
    """
    Simple terminal-based chat interface
    """
    print("\n=== AI Chat Terminal ===")
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'help' to see example prompts")
    print("Type 'models' to see and select available models")
    print("===========================\n")

    current_model = "phi4:latest"  # default model

    while True:
        # Get user input
        prompt = input("\nYou: ").strip()
        
        # Check for exit commands
        if prompt.lower() in ['quit', 'exit']:
            print("\nGoodbye! 👋")
            break
            
        # Check for help command
        if prompt.lower() == 'help':
            print("\nExample prompts:")
            print("1. Write a Python function to sort a list")
            print("2. Tell me a creative story about space")
            print("3. Explain quantum computing")
            print("4. Solve this math problem: 3x + 5 = 14")
            continue
            
        # Check for models command
        if prompt.lower() == 'models':
            list_available_models()  # Show available models
            new_model = input("\nEnter model name or press Enter to keep current model: ").strip()
            if new_model:
                current_model = new_model
                print(f"\nSwitched to model: {current_model}")
            continue
            
        if not prompt:
            print("Please enter a prompt!")
            continue

        try:
            # Use selected model
            client, model = bootstrap_client_and_model(preferred_model=current_model)
            
            print(f"\nUsing model: {model.name}")
            print("Generating response...\n")

            elapsed_time, response = client.chat_completion(prompt, model, None)

            print("AI: ", response)
            print(f"Response time: {elapsed_time:.2f}ms")
            print("\n" + "="*50)

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    chat_with_ai() 