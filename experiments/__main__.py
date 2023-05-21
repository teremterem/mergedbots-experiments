# pylint: disable=wrong-import-position
"""Main file for running the Discord bot."""
import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv
from mergedbots.ext.discord_integration import MergedBotDiscord

sys.path.append(str(Path(__file__).parents[1]))
from experiments.router_bot import router_bot

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)


if __name__ == "__main__":
    MergedBotDiscord(bot=router_bot).attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
