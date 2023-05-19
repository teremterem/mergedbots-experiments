"""Discord integration for MergeBots."""
import contextlib
import re
from collections import defaultdict
from typing import Any, AsyncGenerator

import discord

from ..core import BotMerger
from ..errors import ErrorWrapper
from ..models import MergedUserMessage, MergedUser, MergedMessage, MergedConversation
from ..utils import format_error_with_full_tb, get_text_chunks

DISCORD_MSG_LIMIT = 1900


class MergedBotDiscord:
    """Integration of a merged bot with Discord."""

    def __init__(self, bot_merger: BotMerger, merged_bot_handle: str):
        self._bot_merger = bot_merger
        self._merged_bot_handle = merged_bot_handle

        self._channel_convs: dict[Any, MergedConversation] = defaultdict(MergedConversation)

    def attach_discord_client(self, discord_client: discord.Client) -> None:
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
                    # TODO rethink conversation restarts
                    self._channel_convs[discord_message.channel.id] = MergedConversation()
                    message_visible_to_bots = False
                # TODO read about discord_message.channel.id... is it unique across all servers ?
                history = self._channel_convs[discord_message.channel.id]

                user_message = MergedUserMessage(
                    sender=merged_user,
                    content=discord_message.content,
                    is_visible_to_bots=message_visible_to_bots,
                )
                async for bot_message in self.fulfill_message_with_typing(
                    message=user_message,
                    history=history,
                    typing_context_manager=discord_message.channel.typing(),
                ):
                    for chunk in get_text_chunks(bot_message.content, DISCORD_MSG_LIMIT):
                        await discord_message.channel.send(chunk)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                if isinstance(exc, ErrorWrapper):
                    exc = exc.error
                for chunk in get_text_chunks(format_error_with_full_tb(exc), DISCORD_MSG_LIMIT):
                    await discord_message.channel.send(f"```\n{chunk}\n```")

        discord_client.event(on_message)

    async def fulfill_message_with_typing(
        self,
        message: MergedMessage,
        history: MergedConversation,
        typing_context_manager: Any,
    ) -> AsyncGenerator[MergedMessage, None]:
        """
        Fulfill a message. Returns a generator that would yield zero or more responses to the message.
        typing_context_manager is a context manager that would be used to indicate that the bot is typing.
        """
        response_generator = self._bot_merger.fulfill_message(
            bot_handle=self._merged_bot_handle,
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


def escape_discord_markdown(text):
    """Helper function to escape Discord markdown characters."""
    # TODO is this function needed at all ? who is responsible for escaping markdown and when ?
    escape_chars = r"\*_`~"
    return re.sub(rf"([{re.escape(escape_chars)}])", r"\\\1", text)


_null_context = contextlib.nullcontext()
