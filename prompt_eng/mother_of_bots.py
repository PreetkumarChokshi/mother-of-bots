from typing import Dict, List, Optional
import discord
from discord.ext import commands
from clients import bootstrap_rag_client
from models import ModelOptions, AIModel
from rag import RAGPipeline
import logging
from config import config_factory
import json
import os
import requests
from bot_deployer import BotDeployer
import webbrowser
import asyncio
from analysis.context_builder import ContextBuilder
from generator.bot_generator import DynamicBotGenerator
from orchestration.orchestrator import SystemOrchestrator
from orchestration.state_manager import StateManager
import configparser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.cfg')
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Config file not found at {config_path}")
config.read(config_path)

# Add debug logging
logger.info(f"Config file path: {config_path}")
logger.info(f"Available sections: {config.sections()}")
logger.info(f"Default section keys: {list(config['DEFAULT'].keys()) if 'DEFAULT' in config.sections() else 'No DEFAULT section'}")

class MotherOfBots(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!mob ', intents=intents)
        
        # Initialize components
        self.context_builder = ContextBuilder()
        self.bot_generator = DynamicBotGenerator()
        self.orchestrator = SystemOrchestrator()
        self.state_manager = StateManager()
        
        # Add commands
        self.add_commands()
        
    async def setup_hook(self):
        # Start orchestrator
        await self.orchestrator.start()
        
    def add_commands(self):
        @self.command(name='create')
        async def create_bot(ctx, *, description: str):
            """Create a new bot from description"""
            try:
                # Build context
                bot_context = self.context_builder.build(description)
                
                # Generate bot
                bot = await self.bot_generator.generate_bot(
                    requirements=bot_context.requirements,
                    name=f"bot_{len(self.state_manager.states)}"
                )
                
                await ctx.send(f"Bot created successfully!\nType: {bot_context.intent}\nComplexity: {bot_context.complexity}\nEstimated time: {bot_context.estimated_time}")
                
            except Exception as e:
                logger.error(f"Bot creation failed: {str(e)}")
                await ctx.send(f"Failed to create bot: {str(e)}")
        
        @self.command(name='list')
        async def list_bots(ctx):
            """List all created bots"""
            bots = self.state_manager.states
            if not bots:
                await ctx.send("No bots created yet!")
                return
                
            bot_list = "\n".join([
                f"Bot {bot_id}: {state.status}" 
                for bot_id, state in bots.items()
            ])
            await ctx.send(f"Created bots:\n{bot_list}")
        
        @self.command(name='chat')
        async def chat(ctx, *, message: str):
            """Chat with the AI model"""
            try:
                # Here you would integrate with your LLM API
                response = "I am the Mother of Bots. How can I help you create bots today?"
                await ctx.send(response)
            except Exception as e:
                await ctx.send(f"Error: {str(e)}")

    async def on_ready(self):
        logger.info(f"Mother of Bots is ready!")
        
    async def close(self):
        await self.orchestrator.stop()
        await super().close()

def main():
    bot = MotherOfBots()
    bot.run(config['DEFAULT']['discord_token'])

if __name__ == "__main__":
    main() 