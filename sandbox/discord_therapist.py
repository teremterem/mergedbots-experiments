"""A simple Discord bot that reverses messages."""
import asyncio
import os
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv

from mergebots import BotMerger
from mergebots.discord_integration import attach_discord_client
from mergebots.models import MergedMessage, MergedConversation, MergedBot, FinalBotMessage

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

bot_merger = BotMerger()
discord_client = discord.Client(intents=discord.Intents.default())


# tree = app_commands.CommandTree(discord_client)


# @tree.command(name="start", description="Reset the dialog 🔄")
# async def start(ctx):
#     await ctx.send(content="Hello, World!")


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    # await tree.sync()
    print("Logged in as", discord_client.user)


@bot_merger.register_bot("dummy_bot", "Dummy Bot", "")
async def dummy_bot_fulfiller(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A dummy bot that reverses messages and repeats them three times."""
    # for num in ("one", "two", "three"):
    #     await asyncio.sleep(1)
    #     yield InterimBotMessage(
    #         sender=bot,
    #         content=f"{message.content[::-1]} {num}",
    #     )
    # yield FinalBotMessage(
    #     sender=bot,
    #     content="```" + "\n".join([msg.content for msg in conversation.messages if msg.sender.is_human]) + "```",
    # )
    await asyncio.sleep(0.1)
    conversation = [*history.messages, message]
    yield FinalBotMessage(
        sender=bot,
        content="```\n"
        + "\n".join([msg.content for msg in conversation if msg.sender.is_human and msg.is_visible_to_bots])
        + "\n```",
    )
    # TODO History object is modified after yield (a previous message is appended) - is it confusing ?
    #  Probably better to rethink this (freeze, make copies etc.)
    #  But don't come back to it unless you have more than one bot in your experiment !


if __name__ == "__main__":
    attach_discord_client(discord_client, bot_merger, "dummy_bot")
    discord_client.run(DISCORD_BOT_SECRET)
