"""A simple Discord bot that reverses messages."""
import asyncio
import os
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv

from mergebots import BotMerger
from mergebots.discord_integration import attach_discord_client
from mergebots.models import MergedMessage, MergedConversation, MergedBot, InterimBotMessage, FinalBotMessage

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

bot_merger = BotMerger()
discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)


@bot_merger.register_bot("dummy_bot", "Dummy Bot", "A bot that reverses messages and repeats them three times.")
async def dummy_bot_fulfiller(
    bot: MergedBot,
    conversation: MergedConversation,
    message: MergedMessage,
) -> AsyncGenerator[MergedMessage, None]:
    """A dummy bot that reverses messages and repeats them three times."""
    for num in ("one", "two", "three"):
        await asyncio.sleep(1)
        yield InterimBotMessage(
            sender=bot,
            content=f"{message.content[::-1]} {num}",
        )
    yield FinalBotMessage(
        sender=bot,
        content="```" + "\n".join([msg.content for msg in conversation.messages if msg.sender.is_human]) + "```",
    )


if __name__ == "__main__":
    attach_discord_client(discord_client, bot_merger, "dummy_bot")
    discord_client.run(DISCORD_BOT_SECRET)
