"""Discord integration for MergeBots."""
import contextlib
import re
import traceback
from typing import Any, AsyncGenerator

import discord

from mergebots import BotMerger
from mergebots.models import MergedMessage
from mergebots.models import MergedUserMessage, MergedUser


def attach_discord_client(discord_client: discord.Client, bot_merger: BotMerger, merged_bot_handle: str):
    """Attach a Discord client to a merged bot by its handle."""

    async def on_message(message: discord.Message) -> None:
        """Called when a message is sent to a channel (both a user message and a bot message)."""
        if message.author == discord_client.user:
            # make sure we are not embarking on an "infinite loop" journey
            return

        try:
            merged_user = MergedUser(name=message.author.name)  # TODO is it worth caching these objects ?
            user_message = MergedUserMessage(sender=merged_user, content=message.content)
            async for response in fulfill_message_with_typing(
                bot_merger,
                merged_bot_handle,
                user_message,
                message.channel.typing(),
            ):
                await message.channel.send(response.content)
        except Exception:
            await message.channel.send(f"```\n{traceback.format_exc()}\n```")
            raise

    discord_client.event(on_message)


async def fulfill_message_with_typing(
    bot_merger: BotMerger,
    merged_bot_handle: str,
    message: MergedMessage,
    typing_context_manager: Any,
) -> AsyncGenerator[MergedMessage, None]:
    """
    Fulfill a message. Returns a generator that would yield zero or more responses to the message.
    typing_context_manager is a context manager that would be used to indicate that the bot is typing.
    """
    response_generator = bot_merger.fulfill_message(message, merged_bot_handle)
    response = None
    while True:
        try:
            if not response or response.keep_typing:
                _typing_context_manager = typing_context_manager
            else:
                _typing_context_manager = _null_context

            async with _typing_context_manager:
                response = await anext(response_generator)

        except StopAsyncIteration:
            return

        yield response


_null_context = contextlib.nullcontext()


# TODO should attach_discord_client and fulfill_message_with_typing be combined into a class ? DiscordMergedBot ?


def escape_discord_markdown(text):
    """Helper function to escape Discord markdown characters."""
    # TODO is this function needed at all ? who is responsible for escaping markdown and when ?
    escape_chars = r"\*_`~"
    return re.sub(rf"([{re.escape(escape_chars)}])", r"\\\1", text)
