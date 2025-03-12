#!/usr/bin/env python
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Enable test mode
os.environ["TEST_MODE"] = "true"

from prompt_eng.manager import MasterBot

async def test_create_bot():
    """Test creating a bot with the Master Bot"""
    print("Initializing Master Bot...")
    master_bot = MasterBot(storage_dir="test_bots", use_llm=True)
    await master_bot.initialize()
    
    print("\n===== Testing bot creation flow =====")
    
    # Start the conversation
    print("\nUSER: Create a new bot")
    response = await master_bot.process_message("Create a new bot")
    print(f"BOT: {response}")
    
    # Select bot type
    print("\nUSER: Customer service bot")
    response = await master_bot.process_message("Customer service bot")
    print(f"BOT: {response}")
    
    # Provide bot name
    print("\nUSER: SupportHelper")
    response = await master_bot.process_message("SupportHelper")
    print(f"BOT: {response}")
    
    # Add features
    print("\nUSER: ticket creation, FAQ search")
    response = await master_bot.process_message("ticket creation, FAQ search")
    print(f"BOT: {response}")
    
    # Confirm creation
    print("\nUSER: yes")
    response = await master_bot.process_message("yes")
    print(f"BOT: {response}")
    
    print("\n===== Testing bot listing =====")
    
    # List bots
    print("\nUSER: List my bots")
    response = await master_bot.process_message("List my bots")
    print(f"BOT: {response}")
    
    print("\n===== Testing bot details =====")
    
    # Get bot details
    print("\nUSER: Tell me about SupportHelper")
    response = await master_bot.process_message("Tell me about SupportHelper")
    print(f"BOT: {response}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_create_bot()) 