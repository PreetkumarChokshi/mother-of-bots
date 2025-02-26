import discord
from discord.ext import commands
import logging
from clients import bootstrap_client_and_model, ChatbotClientFactory
from config import config_factory
from bot_deployer import BotDeployer
import json
import os
import webbrowser
from models import AIModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMotherOfBots:
    def __init__(self):
        # Initialize Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Initialize client with phi-4
        config = config_factory()
        self.client = ChatbotClientFactory.create_client(config)
        
        # Store created bots
        self.bots_dir = "generated_bots"
        os.makedirs(self.bots_dir, exist_ok=True)
        
        # Store user creation states
        self.user_states = {}
        
        self.setup_commands()
    
    def setup_commands(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Mother of Bots is ready! Logged in as {self.bot.user.name}')
            print(f'Bot is ready! Logged in as {self.bot.user.name}')

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            user_id = str(message.author.id)
            
            # Handle ongoing bot creation conversation
            if user_id in self.user_states:
                await self.handle_creation_flow(message)
                return

            await self.bot.process_commands(message)

        @self.bot.command(name='create')
        async def create_bot(ctx):
            """Start bot creation through natural language"""
            user_id = str(ctx.author.id)
            self.user_states[user_id] = {
                'state': 'description',
                'data': {}
            }
            await ctx.send("👋 Tell me what kind of bot you want to create! Describe its purpose and functionality.")

    async def handle_creation_flow(self, message):
        """Handle the bot creation conversation flow"""
        user_id = str(message.author.id)
        
        try:
            # Check if user state exists before accessing
            if user_id not in self.user_states:
                return
                
            state = self.user_states[user_id]
            
            if state['state'] == 'description':
                # Store the bot description
                state['data']['description'] = message.content
                
                # Get available models
                models = self.client.get_models()
                model_names = [model.name for model in models]
                
                # Create model selection message
                models_text = "\n".join([f"• {name}" for name in model_names])
                await message.channel.send(
                    f"Great! I'll help create that bot. Which model would you like to use?\n\n"
                    f"Available models:\n{models_text}\n\n"
                    f"Type the model name or 'auto' to let me choose the best model."
                )
                state['state'] = 'model_selection'
                
            elif state['state'] == 'model_selection':
                model_choice = message.content.strip()
                
                try:
                    # Handle model selection
                    if model_choice.lower() == 'auto':
                        # Use the description to select appropriate model
                        _, model = bootstrap_client_and_model(prompt=state['data']['description'])
                        state['data']['model'] = model.name
                    else:
                        state['data']['model'] = model_choice
                    
                    # Determine bot type from description
                    description = state['data']['description'].lower()
                    if 'web' in description or 'website' in description or 'interface' in description:
                        bot_type = 'web'
                    else:
                        bot_type = 'discord'
                    
                    # Generate bot name
                    bot_name = f"bot_{len(os.listdir(self.bots_dir))}"
                    
                    # Create and deploy the bot
                    await self.create_and_deploy_bot(
                        message.channel,
                        bot_name,
                        bot_type,
                        state['data']['description'],
                        state['data']['model']
                    )
                finally:
                    # Always clean up the user state
                    if user_id in self.user_states:
                        del self.user_states[user_id]
                
        except Exception as e:
            await message.channel.send(f"❌ An error occurred: {str(e)}")
            # Clean up user state in case of error
            if user_id in self.user_states:
                del self.user_states[user_id]

    async def create_and_deploy_bot(self, channel, bot_name: str, bot_type: str, description: str, model_name: str):
        """Create and deploy a bot based on the given parameters"""
        try:
            # Generate bot code using an available model
            system_prompt = """You are an expert bot creator. Generate Python code for a bot based on the description.
            The code should be complete and ready to run. Use the specified model and bot type."""
            
            user_prompt = f"""Create a {bot_type} bot with these details:
            Description: {description}
            Model: {model_name}
            Bot Type: {bot_type}
            
            The bot should use the existing infrastructure and follow the same patterns as other bots."""
            
            # Get available models first
            available_models = self.client.get_models()
            if not available_models:
                raise ValueError("No models available from the API")
            
            # Use the first available model for code generation
            generation_model = available_models[0]
            logger.info(f"Using model {generation_model.name} for code generation")
            
            # Get bot code using the available model
            self.client.set_system_prompt(system_prompt)
            _, bot_code = self.client.chat_completion(user_prompt, model=generation_model)
            
            # Save bot code with UTF-8 encoding
            file_path = os.path.join(self.bots_dir, f"{bot_name}.py")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bot_code)
            
            # Deploy the bot
            deployer = BotDeployer()
            
            if bot_type == 'discord':
                await channel.send("Please provide your Discord bot token:")
                
                def check(m):
                    # Fix: Use channel directly without referencing message
                    return m.author.id == channel.last_message.author.id and m.channel == channel if hasattr(channel, 'last_message') else False
                
                try:
                    token_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                    token = token_msg.content
                    try:
                        await token_msg.delete()
                    except discord.errors.Forbidden:
                        # If we can't delete the message, just continue
                        pass
                    deployer.deploy_bot(bot_name, bot_type, token)
                except TimeoutError:
                    await channel.send("❌ Token input timed out. Please try again.")
                    return
                
            else:  # web bot
                deployer.deploy_bot(bot_name, bot_type)
                webbrowser.open('http://localhost:5000')
            
            # Get deployment status
            status = deployer.get_bot_status(bot_name)
            
            # Send success message
            success_msg = f"✨ Bot {bot_name} has been created and deployed!\n"
            success_msg += f"Status: {status['status']}\n"
            if 'pid' in status:
                success_msg += f"Process ID: {status['pid']}\n"
            
            if bot_type == 'web':
                success_msg += f"\nWeb interface opened at: http://localhost:5000"
            
            await channel.send(success_msg)
            
        except Exception as e:
            logger.error(f"Error creating bot: {str(e)}")
            await channel.send(f"❌ Error creating bot: {str(e)}")

    def run(self):
        """Start the Mother of Bots"""
        try:
            config = config_factory()
            token = config.get("discord_token")
            if not token:
                raise ValueError("Discord token not found in config")
            self.bot.run(token)
        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise

if __name__ == "__main__":
    mob = SimpleMotherOfBots()
    mob.run() 