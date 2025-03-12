import os
import logging
import gradio as gr
from typing import Dict, List, Optional, Tuple
import asyncio
from datetime import datetime

from analysis.context_builder import ContextBuilder, BotContext
from generator.bot_generator import DynamicBotGenerator
from bot_deployer import BotDeployer
from clients import bootstrap_client_and_model
from models import ModelOptions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MotherOfBots:
    def __init__(self):
        # Initialize components
        self.context_builder = ContextBuilder()
        self.bot_generator = DynamicBotGenerator()
        self.bot_deployer = BotDeployer()
        
        # Initialize chat client with Qwen2 model
        self.client, self.model = bootstrap_client_and_model(preferred_model="qwen2")
        self.chat_history = []
        
        # Set system prompt for Mother of Bots
        self.client.set_system_prompt(
            "You are Mother of Bots, an advanced AI system that can create custom bots based on natural language descriptions. "
            "Help users design and deploy bots by asking clarifying questions about their requirements. "
            "When ready to create a bot, use the command: !CREATE_BOT with the full specification."
        )
    
    async def chat(self, message: str) -> str:
        """Process user message and generate response"""
        # LLM INTEGRATION POINT: Main chat interface uses the configured model
        _, response = self.client.chat_completion(message, self.model, ModelOptions())
        
        # Check if bot creation is requested
        if "!CREATE_BOT" in response:
            # Extract bot specification
            spec_start = response.find("!CREATE_BOT") + len("!CREATE_BOT")
            spec_end = response.find("!END_SPEC") if "!END_SPEC" in response else len(response)
            bot_spec = response[spec_start:spec_end].strip()
            
            # Create the bot
            bot_name, bot_type = await self.create_bot(bot_spec)
            
            # Add creation confirmation to response
            response = response.replace("!CREATE_BOT" + bot_spec, 
                f"I've created your bot named '{bot_name}' of type '{bot_type}'! You can find it in the deployed_bots directory.")
        
        return response
    
    async def create_bot(self, description: str) -> Tuple[str, str]:
        """Create a bot from description"""
        try:
            # Build context from description
            logger.info(f"Building context for bot: {description[:50]}...")
            bot_context = self.context_builder.build(description)
            
            # Generate bot name based on intent and features
            bot_name = f"{bot_context.intent.lower().replace(' ', '_')}_{datetime.now().strftime('%m%d%H%M')}"
            
            # Generate bot code
            logger.info(f"Generating bot code for {bot_name}...")
            bot = await self.bot_generator.generate_bot(
                requirements=bot_context.requirements,
                name=bot_name
            )
            
            # Deploy the bot
            logger.info(f"Deploying bot {bot_name}...")
            self.bot_deployer.deploy_bot(
                bot_name=bot_name,
                bot_type=bot_context.intent,
                token=bot_context.requirements.get("token", None)
            )
            
            # Launch the bot
            logger.info(f"Launching bot {bot_name}...")
            self.bot_deployer.launch_bot(bot_name, bot_context.intent)
            
            return bot_name, bot_context.intent
            
        except Exception as e:
            logger.error(f"Bot creation failed: {str(e)}")
            raise
    
    def create_ui(self):
        """Create Gradio UI for Mother of Bots"""
        with gr.Blocks(title="Mother of Bots", theme=gr.themes.Soft()) as ui:
            gr.Markdown("# 🤖 Mother of Bots")
            gr.Markdown("Describe the bot you want to create, and I'll build it for you!")
            
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Describe the bot you want to create...", lines=3)
            clear = gr.Button("Clear")
            
            async def user(message, history):
                return "", history + [[message, None]]
            
            async def bot(history):
                message = history[-1][0]
                response = await self.chat(message)
                history[-1][1] = response
                return history
            
            msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot, chatbot, chatbot
            )
            clear.click(lambda: None, None, chatbot, queue=False)
            
        return ui

def main():
    mother = MotherOfBots()
    ui = mother.create_ui()
    ui.launch(share=True)

if __name__ == "__main__":
    main() 