# pylint: disable=wrong-import-position
"""Main file for running the Discord bot."""
import os
import sys
from pathlib import Path

import discord
from botmerger.ext.discord_integration import attach_bot_to_discord
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parents[1]))

from experiments.rewoo.rewoo import rewoo

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)
    print()


if __name__ == "__main__":
    attach_bot_to_discord(rewoo.bot, discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
