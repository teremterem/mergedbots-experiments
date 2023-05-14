"""A simple Discord bot that reverses messages."""
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
    """Called when a message is created and sent by a user."""
    if message.author == discord_client.user:
        # TODO is this necessary ? check if it is
        return

    await message.channel.send("sup?")


if __name__ == "__main__":
    discord_client.run(DISCORD_BOT_SECRET)
