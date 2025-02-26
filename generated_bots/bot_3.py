 Here is an example of a simple Discord bot written in Python using the discord.py library and hosted on Heroku:
```python
import os
import discord
from discord.ext import commands

# Replace with your own bot token
bot_token = "YOUR_BOT_TOKEN"

intents = discord.Intents.default()
intents.typing = False
intents.presences = True

client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.command()
async def coding(ctx):
    # Example of a simple coding response
    await ctx.send('Coding is the process of writing instructions for a computer to execute.' +
                       ' It can involve writing code in different programming languages like Python, Java, C++ etc.')

@client.command()
async def help(ctx):
    # Example of a simple help response
    await ctx.send('Here are some commands you can use on this bot: !coding and !help')

client.run(bot_token)
```
Make sure to replace `YOUR_BOT_TOKEN` with the token for your Discord bot. You will also need to install the discord.py library, which you can do by running `pip install discord.py`. 