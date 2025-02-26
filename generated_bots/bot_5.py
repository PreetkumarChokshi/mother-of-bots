 To create a Discord bot with the specified model, you can use the `discord.py` library in Python. Here's an example of how to create a bot with this model:
```python
import discord
from transformers import pipeline

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

model = pipeline('question-answering', model='MTM0NDAyOTQ4NDAyNTc3NDE0MA.GXuS_R.rapKVBX-yOqIVAXFU-utFvl1PgHMWRp70PiucQ')

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not message.content.startswith('!'):
        return
    question = message.content[1:]
    response = model(question)
    await message.channel.send(response[0]['answer'])
    
client.run('your_discord_bot_token')
```
Make sure to replace `'your_discord_bot_token'` with your actual bot token. This code will create a Discord bot that listens for messages starting with '!' and sends a response from the specified model if it is a question. If you want to add more functionality to the bot, you can modify the code accordingly. 