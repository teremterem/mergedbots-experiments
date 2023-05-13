"""A simple Discord bot that reverses messages."""
import os

import discord
import httpx
from dotenv import load_dotenv

load_dotenv()

httpx_client = httpx.AsyncClient()
discord_client = discord.Client(intents=discord.Intents.default())

CHAT_MERGER_BOT_TOKEN = os.environ["CHAT_MERGER_BOT_TOKEN"]
BOT_TOKEN_HEADER = "X-Chat-Merger-Bot-Token"


@discord_client.event
async def on_ready():
    """Called when the client is done preparing the data received from Discord."""
    print("I'm in")
    print(discord_client.user)


@discord_client.event
async def on_message(message):
    """Called when a message is created and sent by a user."""
    if message.author != discord_client.user:
        await httpx_client.post(
            "http://localhost:8000/bot_update",
            json={"message": message.content},
            headers={BOT_TOKEN_HEADER: CHAT_MERGER_BOT_TOKEN},
        )

        # TODO this should be initiated by ChatMerger
        await message.channel.send(message.content[::-1])


discord_bot_secret = os.environ["DISCORD_BOT_SECRET"]
discord_client.run(discord_bot_secret)
