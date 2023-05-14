"""A simple Discord bot that reverses messages."""
import asyncio
import os
import re
import traceback
from typing import Any, AsyncGenerator

import discord
from discord import Message
from dotenv import load_dotenv
from langchain.schema import ChatMessage, BaseMessage

from mergebots import BotMerger

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

bot_merger = BotMerger()
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

    try:
        async for response in fulfill_message_with_typing(
            ChatMessage(role="user", content=message.content), message.channel.typing()
        ):
            await message.channel.send(response.content)
    except Exception:
        await message.channel.send(f"```\n{traceback.format_exc()}\n```")
        raise


def escape_markdown(text):
    """Helper function to escape Discord markdown characters."""
    # TODO this was generated by GPT-4... replace with a more nuanced / thought through approach ?
    escape_chars = r"\*_`~"
    return re.sub(rf"([{re.escape(escape_chars)}])", r"\\\1", text)


@bot_merger.register_bot("dummy_bot", "Dummy Bot", "A bot that reverses messages and repeats them three times.")
async def dummy_bot_fulfiller(message: BaseMessage) -> AsyncGenerator[BaseMessage, None]:
    """A dummy bot that reverses messages and repeats them three times."""
    for num in ("one", "two", "three"):
        await asyncio.sleep(2)
        yield ChatMessage(role="assistant", content=f"{message.content[::-1]} {num}")


async def fulfill_message_with_typing(
    message: ChatMessage, typing_context_manager: Any
) -> AsyncGenerator[BaseMessage, None]:
    """
    Fulfill a message. Returns a generator that would yield zero or more responses to the message.
    typing_context_manager is a context manager that would be used to indicate that the bot is typing.
    """
    # TODO make this function a part of the MergeBots lib ?
    response_generator = bot_merger.fulfill_message(message, "dummy_bot")
    while True:
        async with typing_context_manager:
            try:
                response = await anext(response_generator)
            except StopAsyncIteration:
                return

        yield response


if __name__ == "__main__":
    discord_client.run(DISCORD_BOT_SECRET)
