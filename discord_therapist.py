"""A simple Discord bot that reverses messages."""
import asyncio
import os

import discord
from discord import Message
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)


@discord_client.event
async def on_message(message: Message) -> None:
    """Called when a message is sent to a channel (both a user message and a bot message)."""
    if message.author == discord_client.user:
        # make sure we are not embarking on an "infinite loop" journey
        return

    async with message.channel.typing():
        await asyncio.sleep(3)
        await message.channel.send("sup?")


if __name__ == "__main__":
    discord_client.run(DISCORD_BOT_SECRET)
