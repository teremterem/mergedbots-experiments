# pylint: disable=wrong-import-position
"""Main file for running the Discord bot."""
import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv
from mergedbots.ext.discord_integration import MergedBotDiscord

load_dotenv()
sys.path.append(str(Path(__file__).parents[1]))
from experiments.active_listener import active_listener

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)
    print()


# async def console_chat() -> None:
#     """Chat with the bot in the console."""
#     merged_user = MergedUser(name="User")
#     previous_msg = None
#     while True:
#         user_message = MergedMessage(
#             previous_msg=previous_msg,
#             in_fulfillment_of=None,
#             sender=merged_user,
#             content=input("USER: "),
#             is_still_typing=False,
#             is_visible_to_bots=True,
#             originator=merged_user,
#         )
#         async for message in repo_inspector.fulfill(user_message):
#             previous_msg = message
#             print(f"{repo_inspector.name.upper()}:", message.content)


if __name__ == "__main__":
    MergedBotDiscord(bot=active_listener.merged_bot).attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)

    # asyncio.run(console_chat())
