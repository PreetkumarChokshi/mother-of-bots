import asyncio
import sys
import os
import json
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from prompt_eng.agents import DynamicBotGeneratorAgent

async def test_weather_bot():
    """Test generating a weather bot"""
    print("\nTesting Weather Bot Generation...")
    
    # Define test requirements
    requirements = {
        "name": "WeatherBot",
        "type": "weather",
        "features": [
            "daily_forecast",
            "location_based",
            "alerts"
        ],
        "platform": "web",
        "apis": [
            {
                "name": "OpenWeatherMap",
                "version": "2.5",
                "endpoints": [
                    "current",
                    "forecast", 
                    "alerts"
                ]
            }
        ],
        "language": "python",
        "async_support": True,
        "database": "sqlite",
        "ui_preferences": {
            "design": "modern",
            "theme": "light",
            "components": [
                "search",
                "forecast_display",
                "alerts_panel"
            ]
        },
        "error_handling": True
    }
    
    # Set test mode
    os.environ["TEST_MODE"] = "true"
    
    # Create agent and generate bot
    agent = DynamicBotGeneratorAgent("test_model")
    bot = await agent.generate_bot(requirements)
    
    # Print results
    print(f"Generated bot: {bot.name}")
    print(f"Code files: {list(bot.code.keys())}")
    print(f"Conversation flow: {json.dumps(bot.conversation_flow, indent=2)}")
    print(f"Business rules: {json.dumps(bot.business_rules, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_weather_bot()) 