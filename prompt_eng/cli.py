#!/usr/bin/env python
import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from prompt_eng.manager import MasterBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("master_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def interactive_mode(storage_dir: str = "generated_bots", use_llm: bool = True):
    """Run the master bot in interactive mode"""
    print("Starting Master Bot in interactive mode...")
    print("Initializing...")
    
    # Initialize the master bot
    master_bot = MasterBot(storage_dir, use_llm=use_llm)
    await master_bot.initialize()
    
    print("\nWelcome to Master Bot!")
    print("This bot can help you create and manage other bots.")
    if use_llm:
        print("LLM-powered mode: Enhanced natural language understanding is enabled.")
    else:
        print("Rule-based mode: Using predefined patterns for understanding your requests.")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'help' to see available commands.")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nThank you for using Master Bot. Goodbye!")
                break
            
            # Process the message
            if user_input:
                response = await master_bot.process_message(user_input)
                print(f"\nMaster Bot: {response}")
            
        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting...")
            break
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Master Bot CLI - Create and manage bots through a simple interface")
    parser.add_argument(
        "--storage-dir", 
        type=str, 
        default="generated_bots",
        help="Directory to store generated bots"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with mock responses"
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM-powered mode (use rule-based processing only)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        # Also set debug level for important modules
        logging.getLogger("prompt_eng.clients").setLevel(logging.DEBUG)
        logging.getLogger("prompt_eng.config").setLevel(logging.DEBUG)
        logging.getLogger("prompt_eng.generator").setLevel(logging.DEBUG)
    
    # Set config path if provided
    if args.config:
        os.environ["CONFIG_PATH"] = args.config
        print(f"Using config file: {args.config}")
    
    # Set test mode if enabled
    if args.test_mode:
        os.environ["TEST_MODE"] = "true"
        print("Running in test mode with mock responses")
    
    # Create storage directory if it doesn't exist
    os.makedirs(args.storage_dir, exist_ok=True)
    
    # Run in interactive mode
    asyncio.run(interactive_mode(args.storage_dir, use_llm=not args.no_llm))

if __name__ == "__main__":
    main() 