"""Discord integration for MergeBots."""
import contextlib
import re
import traceback
from collections import defaultdict
from typing import Any, AsyncGenerator

import discord

from mergebots import BotMerger
from mergebots.models import MergedMessage, MergedConversation
from mergebots.models import MergedUserMessage, MergedUser

# TODO turn the content of this module into a class


CHANNEL_CONVS = defaultdict(MergedConversation)


def attach_discord_client(discord_client: discord.Client, bot_merger: BotMerger, merged_bot_handle: str):
    """Attach a Discord client to a merged bot by its handle."""

    async def on_message(discord_message: discord.Message) -> None:
        """Called when a message is sent to a channel (both a user message and a bot message)."""
        if discord_message.author == discord_client.user:
            # make sure we are not embarking on an "infinite loop" journey
            return

        try:
            merged_user = MergedUser(name=discord_message.author.name)  # TODO is it worth caching these objects ?
            message_visible_to_bots = True
            if discord_message.content.startswith("!"):
                # any prefix command just starts a new conversation for now
                # TODO rethink this ?
                CHANNEL_CONVS[discord_message.channel.id] = MergedConversation()
                message_visible_to_bots = False
            # TODO read about discord_message.channel.id... is it unique across all servers ?
            history = CHANNEL_CONVS[discord_message.channel.id]

            user_message = MergedUserMessage(
                sender=merged_user,
                content=discord_message.content,
                is_visible_to_bots=message_visible_to_bots,
            )
            async for bot_message in fulfill_message_with_typing(
                bot_merger=bot_merger,
                bot_handle=merged_bot_handle,
                message=user_message,
                history=history,
                typing_context_manager=discord_message.channel.typing(),
            ):
                await discord_message.channel.send(bot_message.content)
        except Exception:
            await discord_message.channel.send(f"```\n{traceback.format_exc()}\n```")
            raise

    discord_client.event(on_message)


async def fulfill_message_with_typing(
    bot_merger: BotMerger,
    bot_handle: str,
    message: MergedMessage,
    history: MergedConversation,
    typing_context_manager: Any,
) -> AsyncGenerator[MergedMessage, None]:
    """
    Fulfill a message. Returns a generator that would yield zero or more responses to the message.
    typing_context_manager is a context manager that would be used to indicate that the bot is typing.
    """
    response_generator = bot_merger.fulfill_message(
        bot_handle=bot_handle,
        message=message,
        history=history,
    )
    response = None
    while True:
        try:
            if not response or response.is_still_typing:
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
