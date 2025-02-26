 Here is a sample code for a Discord bot using the MTM0NDAyOTQ4NDAyNTc3NDE0MA.GXuS\_R.rapKVBX-yOqIVAXFU-utFvl1PgHMWRp70PiucQ model:
```python
import discord
from transformers import pipeline

intents = discord.Intents.default()
intents.typing = False
intents.presences = False

client = discord.Client(intents=intents)

model = pipeline("text-generation", model="MTM0NDAyOTQ4NDAyNTc3NDE0MA.GXuS_R.rapKVBX-yOqIVAXFU-utFvl1PgHMWRp70PiucQ")

@client.event
async def on\_ready():
    print(f"{client.user} has connected to Discord!")

@client.command()
async def generate(ctx):
    prompt = ctx.message.content
    generated_text = model(prompt=prompt, max_length=50, temperature=0.2)
    await ctx.send(generated_text[0]['generated_text'])

client.run("YOUR\_DISCORD\_BOT\_TOKEN")
```
Note: Replace `"YOUR\_DISCORD\_BOT\_TOKEN"` with your actual discord bot token. 