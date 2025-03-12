import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..agents import DynamicBotGeneratorAgent
from ..generator import GeneratedBot

logger = logging.getLogger(__name__)

class BotManager:
    """
    Master bot manager that handles creating, storing, and managing multiple bots.
    This is the main entry point for the master bot system.
    """
    def __init__(self, storage_dir: str = "generated_bots"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        self.active_bots: Dict[str, GeneratedBot] = {}
        self.bot_generator = DynamicBotGeneratorAgent()
    
    async def initialize(self):
        """Initialize the bot manager"""
        await self.bot_generator.initialize()
        await self._load_stored_bots()
    
    async def _load_stored_bots(self):
        """Load previously generated bots from storage"""
        for bot_dir in self.storage_dir.iterdir():
            if not bot_dir.is_dir():
                continue
                
            try:
                metadata_file = bot_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    
                    # Load code files
                    code = {}
                    for file_path in bot_dir.glob("code/*.*"):
                        with open(file_path, "r") as f:
                            code[file_path.name] = f.read()
                    
                    # Create GeneratedBot object
                    bot = GeneratedBot(
                        name=metadata["name"],
                        code=code,
                        conversation_flow=metadata["conversation_flow"],
                        business_rules=metadata["business_rules"]
                    )
                    
                    self.active_bots[metadata["name"]] = bot
                    logger.info(f"Loaded bot: {metadata['name']}")
            except Exception as e:
                logger.error(f"Failed to load bot {bot_dir.name}: {str(e)}")
    
    async def create_bot(self, requirements: Dict[str, Any]) -> GeneratedBot:
        """Create a new bot based on the provided requirements"""
        try:
            # Generate the bot
            bot = await self.bot_generator.generate_bot(requirements)
            
            # Store the bot
            await self._store_bot(bot, requirements)
            
            # Add to active bots
            self.active_bots[bot.name] = bot
            
            return bot
        except Exception as e:
            logger.error(f"Failed to create bot: {str(e)}")
            raise
    
    async def _store_bot(self, bot: GeneratedBot, requirements: Dict[str, Any]):
        """Store a bot to disk"""
        bot_dir = self.storage_dir / bot.name
        bot_dir.mkdir(exist_ok=True)
        
        # Store code files
        code_dir = bot_dir / "code"
        code_dir.mkdir(exist_ok=True)
        for filename, content in bot.code.items():
            with open(code_dir / filename, "w") as f:
                f.write(content)
        
        # Store metadata
        metadata = {
            "name": bot.name,
            "requirements": requirements,
            "conversation_flow": bot.conversation_flow,
            "business_rules": bot.business_rules,
            "created_at": str(datetime.now())
        }
        
        with open(bot_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    def get_bot(self, name: str) -> Optional[GeneratedBot]:
        """Get a bot by name"""
        return self.active_bots.get(name)
    
    def list_bots(self) -> List[str]:
        """List all available bots"""
        return list(self.active_bots.keys())
    
    async def update_bot(self, name: str, requirements: Dict[str, Any]) -> GeneratedBot:
        """Update an existing bot with new requirements"""
        if name not in self.active_bots:
            raise ValueError(f"Bot {name} not found")
        
        # Update requirements with the bot name
        requirements["name"] = name
        
        # Generate the updated bot
        bot = await self.bot_generator.generate_bot(requirements)
        
        # Store the updated bot
        await self._store_bot(bot, requirements)
        
        # Update active bots
        self.active_bots[name] = bot
        
        return bot
    
    def delete_bot(self, name: str) -> bool:
        """Delete a bot"""
        if name not in self.active_bots:
            return False
        
        # Remove from active bots
        del self.active_bots[name]
        
        # Delete from storage
        bot_dir = self.storage_dir / name
        if bot_dir.exists():
            import shutil
            shutil.rmtree(bot_dir)
        
        return True

# Example usage
if __name__ == "__main__":
    async def test():
        manager = BotManager()
        await manager.initialize()
        
        requirements = {
            "name": "TestBot",
            "type": "weather",
            "features": ["daily_forecast", "location_based"],
            "platform": "web",
            "apis": [{"name": "OpenWeatherMap", "version": "2.5"}],
            "language": "python",
            "async_support": True
        }
        
        bot = await manager.create_bot(requirements)
        print(f"Created bot: {bot.name}")
        print("Available bots:", manager.list_bots())
    
    asyncio.run(test()) 