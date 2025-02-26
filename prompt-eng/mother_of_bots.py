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

class MotherOfBots:
    def __init__(self):
        self.rag_pipeline, self.model = bootstrap_rag_client()
        self.child_bots: Dict[str, 'BotConfig'] = {}
        self.current_workflow: Dict[str, Dict] = {}
        
        # Create bots directory if it doesn't exist
        self.bots_dir = "generated_bots"
        os.makedirs(self.bots_dir, exist_ok=True)
        
        # Initialize Discord bot
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='!mob ', intents=intents)
        self.setup_commands()
        
    def setup_commands(self):
        @self.bot.event
        async def on_ready():
            logging.info(f'Mother of Bots is ready! Logged in as {self.bot.user.name}')

        @self.bot.command(name='create')
        async def create_bot(ctx):
            """Start the bot creation workflow"""
            user_id = str(ctx.author.id)
            self.current_workflow[user_id] = {
                'state': 'init',
                'config': BotConfig()
            }
            await ctx.send("👋 Let's create a new bot! What type of bot would you like to create? (e.g., discord, web, documentation)")

        @self.bot.command(name='commands')
        async def show_commands(ctx):
            """Show available commands"""
            help_text = """
            🤖 Mother of Bots - Available Commands:
            !mob create - Start creating a new bot
            !mob list - List your created bots
            !mob deploy <bot_name> - Deploy a bot
            !mob modify <bot_name> - Modify existing bot
            !mob delete <bot_name> - Delete a bot
            !mob commands - Show this help message
            """
            await ctx.send(help_text)

        @self.bot.command(name='list')
        async def list_bots(ctx):
            """List all created bots"""
            if not self.child_bots:
                await ctx.send("No bots have been created yet!")
                return
            
            bot_list = "\n".join([f"• {name}: {bot.purpose}" for name, bot in self.child_bots.items()])
            await ctx.send(f"Created Bots:\n{bot_list}")

        @self.bot.command(name='deploy')
        async def deploy_bot(ctx, bot_name: str):
            """Deploy a created bot"""
            try:
                if bot_name not in self.child_bots:
                    await ctx.send(f"Bot '{bot_name}' not found. Use !mob list to see available bots.")
                    return
                
                bot_config = self.child_bots[bot_name]
                deploy_code = self.deploy_bot_code(bot_name, bot_config)
                
                # Save bot code to file with UTF-8 encoding
                file_path = os.path.join(self.bots_dir, f"{bot_name}.py")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(deploy_code)
                
                # Deploy and launch the bot
                deployer = BotDeployer()
                
                if bot_config.bot_type == 'discord':
                    # For Discord bots, we need to create a new application and get token
                    await ctx.send("Please provide your Discord bot token:")
                    
                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel
                    
                    try:
                        token_msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                        token = token_msg.content
                        await token_msg.delete()  # Delete message containing token
                    except TimeoutError:
                        await ctx.send("❌ Token input timed out. Please try again.")
                        return
                    
                    deployer.deploy_bot(bot_name, bot_config.bot_type, token)
                elif bot_config.bot_type == 'web':
                    # For web bots, deploy and open browser
                    deployer.deploy_bot(bot_name, bot_config.bot_type)
                    webbrowser.open('http://localhost:5000')  # Open the web interface
                else:
                    deployer.deploy_bot(bot_name, bot_config.bot_type)
                
                # Send the deployment status
                status = deployer.get_bot_status(bot_name)
                status_msg = f"✨ Bot {bot_name} deployed successfully!\n"
                status_msg += f"Status: {status['status']}\n"
                if 'pid' in status:
                    status_msg += f"Process ID: {status['pid']}\n"
                
                if bot_config.bot_type == 'web':
                    status_msg += f"\nWeb interface opened at: http://localhost:5000"
                
                await ctx.send(status_msg)
                
                # Send the file to Discord
                with open(file_path, 'rb') as f:
                    await ctx.send(
                        f"Here's your bot code:",
                        file=discord.File(f, f"{bot_name}.py")
                    )
                
                # Send deployment instructions
                instructions = self.get_deployment_instructions(bot_config)
                await ctx.send(instructions)
                
            except Exception as e:
                logging.error(f"Deployment error: {str(e)}")
                await ctx.send(f"❌ Error deploying bot: {str(e)}")

        @self.bot.command(name='modify')
        async def modify_bot(ctx, bot_name: str):
            """Modify an existing bot"""
            if bot_name not in self.child_bots:
                await ctx.send(f"❌ Bot '{bot_name}' not found.")
                return
            
            await ctx.send(f"🤖 Modifying bot '{bot_name}'...")
            await self.process_workflow(ctx.message)

        @self.bot.command(name='delete')
        async def delete_bot(ctx, bot_name: str):
            """Delete a bot"""
            if bot_name not in self.child_bots:
                await ctx.send(f"❌ Bot '{bot_name}' not found.")
                return
            
            await ctx.send(f"🤖 Deleting bot '{bot_name}'...")
            del self.child_bots[bot_name]
            await ctx.send("✅ Bot deleted successfully!")

        @self.bot.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("❌ Unknown command. Use !mob commands to see available commands.")
            else:
                logging.error(f"Command error: {str(error)}")
                await ctx.send(f"❌ An error occurred: {str(error)}")

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            user_id = str(message.author.id)
            if user_id in self.current_workflow:
                await self.process_workflow(message)
            
            await self.bot.process_commands(message)

    async def process_workflow(self, message):
        """Process bot creation workflow"""
        user_id = str(message.author.id)
        workflow = self.current_workflow[user_id]
        
        try:
            if workflow['state'] == 'init':
                bot_type = message.content.lower()
                if bot_type not in ['discord', 'web', 'documentation']:
                    await message.channel.send("Please choose a valid bot type: discord, web, or documentation")
                    return
                
                workflow['config'].bot_type = bot_type
                workflow['state'] = 'purpose'
                await message.channel.send("What's the main purpose of this bot? (e.g., technical support, coding assistance, documentation helper)")
                
            elif workflow['state'] == 'purpose':
                workflow['config'].purpose = message.content
                workflow['state'] = 'personality'
                await message.channel.send("How should the bot's personality be? (e.g., professional, friendly, technical)")
                
            elif workflow['state'] == 'personality':
                workflow['config'].personality = message.content
                workflow['state'] = 'model_selection'
                model = self.select_model(workflow['config'])
                workflow['config'].model = model
                await message.channel.send(f"I've selected {model} as the best model for your bot. Would you like to proceed? (yes/no)")
                
            elif workflow['state'] == 'model_selection':
                if message.content.lower() == 'yes':
                    workflow['state'] = 'finalize'
                    bot_config = workflow['config']
                    bot_name = f"bot_{len(self.child_bots)}"
                    self.child_bots[bot_name] = bot_config
                    
                    deploy_code = self.deploy_bot_code(bot_name, bot_config)
                    
                    await message.channel.send(f"✨ Your bot has been created! Use `!mob deploy {bot_name}` to get the deployment code.")
                    del self.current_workflow[user_id]
                elif message.content.lower() == 'no':
                    await message.channel.send("Please specify which model you'd prefer:")
                    workflow['state'] = 'model_selection'
                else:
                    await message.channel.send("Please answer 'yes' or 'no'")
                    
        except Exception as e:
            logging.error(f"Workflow error: {str(e)}")
            await message.channel.send(f"❌ An error occurred in the workflow: {str(e)}")
            del self.current_workflow[user_id]

    def get_available_models(self) -> list:
        """Fetch available models from the API"""
        try:
            cfg = config_factory()
            host = cfg["chatbot_api_host"]
            bearer = cfg["bearer"]

            # First try Ollama endpoint
            try:
                url = f"http://{host}/api/tags"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data["models"]]
            except:
                # Try OpenWebUI endpoint
                url = f"https://{host}/api/models"
                headers = {
                    "Authorization": f"Bearer {bearer}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return [model["name"] for model in data["data"]]
                
            return []
        except Exception as e:
            logging.error(f"Error fetching models: {str(e)}")
            return []

    def select_model(self, config: 'BotConfig') -> str:
        """Select appropriate model based on bot configuration"""
        try:
            available_models = self.get_available_models()
            if not available_models:
                logging.warning("No models available from API, using first available model")
                return available_models[0] if available_models else "neural-chat:7b"

            purpose = config.purpose.lower()
            
            # Select based on purpose from available models
            if 'cod' in purpose or 'program' in purpose:
                # Look for coding-specialized models first
                for model in available_models:
                    model_lower = model.lower()
                    if any(name in model_lower for name in ['code', 'deepseek', 'wizard']):
                        return model
            elif 'document' in purpose or 'knowledge' in purpose:
                # Look for models good at knowledge tasks
                for model in available_models:
                    model_lower = model.lower()
                    if any(name in model_lower for name in ['mixtral', 'llama']):
                        return model

            # If no specialized model found or for general purpose, 
            # return the first available model
            return available_models[0]

        except Exception as e:
            logging.error(f"Error selecting model: {str(e)}")
            return available_models[0] if available_models else "neural-chat:7b"

    def deploy_bot_code(self, bot_name: str, config: 'BotConfig') -> str:
        """Generate complete deployment code for a bot"""
        if config.bot_type == 'discord':
            return self.generate_discord_deployment(bot_name, config)
        elif config.bot_type == 'web':
            return self.generate_web_deployment(bot_name, config)
        else:
            return self.generate_basic_deployment(bot_name, config)

    def generate_discord_deployment(self, bot_name: str, config: 'BotConfig') -> str:
        # Get configuration
        cfg = config_factory()
        api_host = cfg.get("chatbot_api_host")
        bearer_token = cfg.get("bearer")

        return f'''
import discord
from discord.ext import commands
import logging
import requests
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
class BotConfig:
    BOT_NAME = "{bot_name}"
    MODEL = "{config.model}"
    PERSONALITY = "{config.personality}"
    API_HOST = "{api_host}"
    BEARER_TOKEN = "{bearer_token}"

class ChatAPI:
    @staticmethod
    async def get_response(message: str) -> str:
        """Get response from AI model API"""
        try:
            headers = {{
                "Authorization": f"Bearer {{BotConfig.BEARER_TOKEN}}",
                "Content-Type": "application/json"
            }}
            
            # First try OpenWebUI endpoint
            url = f"https://{{BotConfig.API_HOST}}/api/chat/completions"
            payload = {{
                "messages": [
                    {{"role": "system", "content": f"You are {{BotConfig.PERSONALITY}}. Respond accordingly."}},
                    {{"role": "user", "content": message}}
                ],
                "model": BotConfig.MODEL,
                "stream": False
            }}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            
            # If OpenWebUI fails, try Ollama endpoint
            url = f"http://{{BotConfig.API_HOST}}/api/chat"
            payload = {{
                "model": BotConfig.MODEL,
                "messages": [
                    {{"role": "system", "content": f"You are {{BotConfig.PERSONALITY}}. Respond accordingly."}},
                    {{"role": "user", "content": message}}
                ]
            }}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['message']['content']
            
            raise Exception(f"API request failed with status code: {{response.status_code}}")
            
        except Exception as e:
            logger.error(f"Error calling AI API: {{str(e)}}")
            return f"Error: {{str(e)}}"

class {config.get_class_name()}(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!')
        
    async def on_ready(self):
        logger.info(f'{{self.user.name}} is ready! Using model: {{BotConfig.MODEL}}')
        
    @commands.command()
    async def chat(self, ctx, *, message: str):
        """Chat with the AI model"""
        try:
            async with ctx.typing():  # Show typing indicator
                response = await ChatAPI.get_response(message)
            await ctx.send(response)
        except Exception as e:
            logger.error(f"Error in chat command: {{str(e)}}")
            await ctx.send(f"❌ An error occurred: {{str(e)}}")
    
    @commands.command()
    async def info(self, ctx):
        """Show bot information"""
        embed = discord.Embed(
            title=f"{{BotConfig.BOT_NAME}} Info",
            color=discord.Color.blue()
        )
        embed.add_field(name="Model", value=BotConfig.MODEL)
        embed.add_field(name="Personality", value=BotConfig.PERSONALITY)
        embed.add_field(name="Type", value="Discord Bot")
        await ctx.send(embed=embed)

def main():
    try:
        bot = {config.get_class_name()}()
        bot.run('YOUR_TOKEN')
    except Exception as e:
        logger.error(f"Failed to start bot: {{str(e)}}")
        raise

if __name__ == "__main__":
    main()
'''

    def generate_web_deployment(self, bot_name: str, config: 'BotConfig') -> str:
        # Get configuration
        cfg = config_factory()
        api_host = cfg.get("chatbot_api_host")
        bearer_token = cfg.get("bearer")

        return f'''
from flask import Flask, request, jsonify, render_template_string
import logging
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Configuration
class BotConfig:
    BOT_NAME = "{bot_name}"
    MODEL = "{config.model}"
    PERSONALITY = "{config.personality}"
    API_HOST = "{api_host}"
    BEARER_TOKEN = "{bearer_token}"

class ChatAPI:
    @staticmethod
    def get_response(message: str) -> str:
        """Get response from AI model API"""
        try:
            headers = {{
                "Authorization": f"Bearer {{BotConfig.BEARER_TOKEN}}",
                "Content-Type": "application/json"
            }}
            
            # First try OpenWebUI endpoint
            url = f"https://{{BotConfig.API_HOST}}/api/chat/completions"
            payload = {{
                "messages": [
                    {{"role": "system", "content": f"You are {{BotConfig.PERSONALITY}}. Respond accordingly."}},
                    {{"role": "user", "content": message}}
                ],
                "model": BotConfig.MODEL,
                "stream": False
            }}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            
            # If OpenWebUI fails, try Ollama endpoint
            url = f"http://{{BotConfig.API_HOST}}/api/chat"
            payload = {{
                "model": BotConfig.MODEL,
                "messages": [
                    {{"role": "system", "content": f"You are {{BotConfig.PERSONALITY}}. Respond accordingly."}},
                    {{"role": "user", "content": message}}
                ]
            }}
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                return response.json()['message']['content']
            
            raise Exception(f"API request failed with status code: {{response.status_code}}")
            
        except Exception as e:
            logger.error(f"Error calling AI API: {{str(e)}}")
            return f"Error: {{str(e)}}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{{{ bot_name }}}} - Chat Interface</title>
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }}
        .chat-container {{ margin-top: 20px; }}
        #chat-messages {{ height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }}
        .message {{ margin-bottom: 10px; }}
        .user-message {{ color: blue; }}
        .bot-message {{ color: green; }}
    </style>
</head>
<body>
    <h1>{{{{ bot_name }}}} ({{{{ personality }}}})</h1>
    <div class="chat-container">
        <div id="chat-messages"></div>
        <input type="text" id="message-input" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        async function sendMessage() {{
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += '<div class="message user-message">You: ' + message + '</div>';
            messageInput.value = '';
            
            try {{
                const response = await fetch('/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: message}})
                }});
                const data = await response.json();
                messagesDiv.innerHTML += '<div class="message bot-message">Bot: ' + data.response + '</div>';
            }} catch (error) {{
                messagesDiv.innerHTML += '<div class="message error">Error: ' + error.message + '</div>';
            }}
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}

        document.getElementById('message-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') sendMessage();
        }});
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                bot_name=BotConfig.BOT_NAME,
                                personality=BotConfig.PERSONALITY)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message', '')
        response = ChatAPI.get_response(message)
        return jsonify({{'response': response}})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {{str(e)}}")
        return jsonify({{'error': str(e)}}), 500

if __name__ == '__main__':
    app.run(debug=True)
'''

    def get_deployment_instructions(self, config: 'BotConfig') -> str:
        """Get deployment instructions based on bot type"""
        if config.bot_type == 'discord':
            return """
📝 Deployment Instructions:
1. Install required packages: `pip install discord.py`
2. Create a Discord application at https://discord.com/developers/applications
3. Create a bot for your application and copy the token
4. Replace 'YOUR_TOKEN' in the code with your bot token
5. Run the bot: `python bot_name.py`
"""
        elif config.bot_type == 'web':
            return """
📝 Deployment Instructions:
1. Install required packages: `pip install flask`
2. Run the web server: `python bot_name.py`
3. Open http://localhost:5000 in your browser
"""
        else:
            return """
📝 Deployment Instructions:
1. Import the bot class in your code
2. Create an instance of the bot
3. Call the chat method with your messages
"""

    def run(self):
        """Start the Mother of Bots"""
        try:
            config = config_factory()
            token = config.get("discord_token")
            if not token:
                raise ValueError("Discord token not found in config")
            self.bot.run(token)
        except Exception as e:
            logging.error(f"Failed to start bot: {str(e)}")
            raise

class BotConfig:
    def __init__(self):
        self.bot_type: str = ""
        self.purpose: str = ""
        self.personality: str = ""
        self.model: str = ""
        
    def get_class_name(self) -> str:
        return f"CustomBot_{self.bot_type.capitalize()}"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        mob = MotherOfBots()
        mob.run()
    except Exception as e:
        logging.error(f"Critical error: {str(e)}") 