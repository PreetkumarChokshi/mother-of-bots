 Here is a sample code for a discord bot using the codestral model:
```
import discord
from transformers import pipeline

intents = discord.Intents.default()
intents.messages = True

client = discord.Client(intents=intents)

model = pipeline('codestrel')

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if 'coding' in message.content.lower():
        response = model(message.content)
        await message.channel.send(response[0]['generated_text'])
```
This code sets up a discord bot using the discord.py library and the codestral model from Hugging Face. The bot listens for messages containing the word 'coding' in them, and when it receives one, it uses the codestral model to generate a response. The generated response is then sent back to the channel where the original message was sent.

Please note that you will need to install discord.py, transformers library and have discord bot token to run this code. 