import discord
from discord.ext import commands
import logging
from clients import bootstrap_client_and_model
from models import ModelOptions
from model_orchestrator import ModelOrchestrator

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detail
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create bot instance with specific intents
intents = discord.Intents.default()
intents.message_content = True  # We need this for reading message content
intents.guilds = True          # For guild/server info
intents.messages = True        # For message events

bot = commands.Bot(command_prefix='!', intents=intents)

# Store current model and options
current_model = "phi-2:latest"
model_options = ModelOptions()

# Initialize orchestrator as a global instance
orchestrator = ModelOrchestrator()

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    logger.info('Guild names:')
    for guild in bot.guilds:
        logger.info(f'- {guild.name} (ID: {guild.id})')
    print(f'Bot is ready! Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return

    logger.debug(f'Message received: {message.content}')
    
    # Check for greetings
    greetings = ['hi', 'hello', 'hey', 'hola', 'greetings']
    if message.content.lower() in greetings:
        help_text = ("👋 Hello! I'm an AI assistant. Here's how you can interact with me:\n"
                    "• `!chat <message>` - Chat with me\n"
                    "• `!model` - See current AI model\n"
                    "• `!models` - List available models\n"
                    "• `!commands` - See all commands")
        await message.channel.send(help_text)
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    logger.error(f'Command error: {str(error)}')
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("❌ Command not found. Use !commands to see available commands.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")

@bot.command(name='chat')
async def chat(ctx, *, message):
    """Chat with the AI model"""
    try:
        # Show typing indicator
        async with ctx.typing():
            # Create workflow context
            workflow_ctx = {
                "workflow/id": f"discord_{ctx.message.id}",
                "workflow/input": message,
                "prompt": message,
                "channel_id": ctx.channel.id,
                "user_id": ctx.author.id
            }
            
            # Process with orchestrator
            response = await orchestrator.process(workflow_ctx)
            
            # Create embed response
            embed = discord.Embed(
                title="AI Response",
                description=response,
                color=discord.Color.blue()
            )
            
            # Add model info if available
            if "workflow/target_model" in workflow_ctx:
                model_name = workflow_ctx["workflow/target_model"]
            elif "workflow/suggested_models" in workflow_ctx:
                model_name = ", ".join(workflow_ctx["workflow/suggested_models"])
            else:
                model_name = "default"
                
            embed.set_footer(text=f"Model: {model_name}")
            
            await ctx.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name='model')
async def change_model(ctx, new_model=None):
    """Change or display current model"""
    global current_model
    
    if new_model:
        try:
            # Test if model exists
            client, model = bootstrap_client_and_model(preferred_model=new_model)
            current_model = new_model
            await ctx.send(f"✅ Switched to model: {model.name}")
        except Exception as e:
            await ctx.send(f"❌ Error changing model: {str(e)}")
    else:
        # Show current model
        client, model = bootstrap_client_and_model(preferred_model=current_model)
        await ctx.send(f"Current model: {model.name}")

@bot.command(name='models')
async def list_models(ctx):
    """List available models"""
    try:
        client, _ = bootstrap_client_and_model()
        models = client.get_models()
        
        # Create embed with model list
        embed = discord.Embed(
            title="Available Models",
            color=discord.Color.blue()
        )
        
        for model in models:
            embed.add_field(
                name=model.name,
                value=f"Size: {model.parameter_size}",
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error listing models: {str(e)}")

@bot.command(name='commands')
async def show_commands(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are the available commands:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="!chat <message>",
        value="Chat with the AI model",
        inline=False
    )
    embed.add_field(
        name="!model [model_name]",
        value="Change or display current model",
        inline=False
    )
    embed.add_field(
        name="!models",
        value="List available models",
        inline=False
    )
    embed.add_field(
        name="!commands",
        value="Show this help message",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Add your Discord token to config.cfg
def get_discord_token():
    from config import config_factory
    config = config_factory()
    return config.get("discord_token")

def main():
    token = get_discord_token()
    if not token:
        logger.error("Discord token not found in config.cfg")
        return
    
    logger.info("Token found, attempting to start bot...")
    try:
        bot.run(token)
    except discord.LoginFailure as e:
        logger.error(f"Failed to login: {str(e)}")
        logger.error("Please check your token in config.cfg")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        logger.error("Full error:", exc_info=True)

if __name__ == "__main__":
    main() 