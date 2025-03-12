import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..clients import bootstrap_client_and_model
from .models import AIModel, ModelOptions
from ..generator import DynamicBotGenerator, GeneratedBot
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeGenerationConfig:
    language: str  # 'python', 'nodejs', 'flask'
    apis: List[Dict]
    database: Optional[str] = None
    async_support: bool = False
    error_handling: bool = True

@dataclass
class ConversationFlow:
    intents: List[str]
    responses: Dict[str, List[str]]
    fallbacks: Dict[str, str]
    context_rules: Dict[str, List[str]]

@dataclass
class BusinessRule:
    condition: str
    action: str
    alternative: Optional[str] = None
    priority: int = 1

class DynamicBotGeneratorAgent:
    def __init__(self, preferred_model: Optional[str] = None):
        self.preferred_model = preferred_model
        self.bot_generator = None
    
    async def initialize(self):
        """Initialize the bot generator with the client and model"""
        if not self.bot_generator:
            self.bot_generator = DynamicBotGenerator(self.preferred_model)
            await self.bot_generator.initialize()
    
    async def generate_bot(self, requirements: Dict) -> GeneratedBot:
        """Generate a bot based on the provided requirements"""
        try:
            # Initialize if not already initialized
            await self.initialize()
            
            # Convert requirements to include necessary fields
            enhanced_requirements = {
                **requirements,
                "language": requirements.get("language", "python"),
                "apis": requirements.get("apis", []),
                "database": requirements.get("database"),
                "async_support": requirements.get("async_support", False),
                "error_handling": requirements.get("error_handling", True)
            }
            return await self.bot_generator.generate_bot(enhanced_requirements)
        except Exception as e:
            logger.error(f"Failed to generate bot: {str(e)}")
            raise Exception(f"Failed to generate bot: {str(e)}")

# Example usage
if __name__ == "__main__":
    async def test():
        agent = DynamicBotGeneratorAgent()
        requirements = {
            "name": "WeatherBot",
            "type": "weather",
            "features": ["daily_forecast", "location_based"],
            "platform": "web",
            "apis": [{"name": "OpenWeatherMap", "version": "2.5"}],
            "language": "python",
            "async_support": True
        }
        bot = await agent.generate_bot(requirements)
        print(f"Generated bot: {bot.name}")
        print("Code files:", list(bot.code.keys()))
        print("\nFeatures:", requirements["features"])
    
    asyncio.run(test()) 