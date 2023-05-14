"""A simple Discord bot that reverses messages."""
import os
from typing import Generator, Any

import discord
from discord import Message
from dotenv import load_dotenv
from langchain.schema import ChatMessage, BaseMessage

from mergebots import fulfill_message

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

    async for response in fulfill_message_with_typing(
        ChatMessage(role="user", content=message.content), message.channel.typing()
    ):
        await message.channel.send(response.content)


async def fulfill_message_with_typing(
    message: ChatMessage, typing_context_manager: Any
) -> Generator[BaseMessage, None, None]:
    """
    Fulfill a message. Returns a generator that would yield zero or more responses to the message.
    typing_context_manager is a context manager that would be used to indicate that the bot is typing.
    """
    response_generator = fulfill_message(message)
    while True:
        try:
            async with typing_context_manager:
                response = await anext(response_generator)
        except StopAsyncIteration:
            return

        yield response


if __name__ == "__main__":
    discord_client.run(DISCORD_BOT_SECRET)
