"""A simple Discord bot that reverses messages."""
import os

import discord
from dotenv import load_dotenv

load_dotenv()

client = discord.Client(intents=discord.Intents.default())


@client.event
async def on_ready():
    """Called when the client is done preparing the data received from Discord."""
    print("I'm in")
    print(client.user)


@client.event
async def on_message(message):
    """Called when a message is created and sent by a user."""
    if message.author != client.user:
        await message.channel.send(message.content[::-1])


my_secret = os.environ["DISCORD_BOT_SECRET"]
client.run(my_secret)
