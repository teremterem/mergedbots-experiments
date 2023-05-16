# pylint: disable=wrong-import-position
"""A simple Discord bot that reverses messages."""
import asyncio
import io
import itertools
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage

sys.path.append(str(Path(__file__).parents[1]))
from mergebots import BotMerger
from mergebots.discord_integration import attach_discord_client
from mergebots.models import MergedMessage, MergedConversation, MergedBot, FinalBotMessage, InterimBotMessage

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


class StreamingCallbackHandler(AsyncCallbackHandler):  # pylint: disable=abstract-method
    """
    A callback handler that splits the output into paragraphs and dispatches each paragraph as a separate message
    via a queue.
    """

    STREAM_END = "<|im_end|>"

    def __init__(self) -> None:
        self.msg_queue: asyncio.Queue = asyncio.Queue(maxsize=64)
        self._str_stream = io.StringIO()

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        self._str_stream.write(token)

        if not token or token.isspace():
            # token is empty, let's wait for a non-empty one (non-empty token would signify that
            # the previous message, if any, is not the last one just yet)
            return

        text_so_far = self._str_stream.getvalue()

        inside_code_block = (text_so_far.count("```") % 2) == 1
        if inside_code_block:
            # we don't want to split a code block
            return

        split_idx = text_so_far.rfind("\n\n")
        if split_idx != -1:
            await self.msg_queue.put(text_so_far[:split_idx])
            self._str_stream.close()
            self._str_stream = io.StringIO(text_so_far[split_idx + 2 :])

    async def on_llm_end(self, *args, **kwargs) -> None:  # pylint: disable=unused-argument
        await self.msg_queue.put(self._str_stream.getvalue() + self.STREAM_END)
        self._str_stream.close()


@bot_merger.register_bot("swipy", "Swipy", "")
async def therapist_fulfiller(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A dummy bot that reverses messages and repeats them three times."""

    conversation = [msg for msg in itertools.chain(history.messages, (message,)) if msg.is_visible_to_bots]
    if not conversation:
        yield FinalBotMessage(sender=bot, content="```\nCONVERSATION RESTARTED\n```", is_visible_to_bots=False)
        return

    streaming = StreamingCallbackHandler()
    chat_llm = PromptLayerChatOpenAI(
        model_name="gpt-4",  # "gpt-3.5-turbo",
        streaming=True,
        callbacks=[streaming],
        # TODO user=...,
        pl_tags=["discord_therapist"],
    )
    # TODO find a way to capture exceptions from inside create_task
    asyncio.create_task(
        chat_llm.agenerate(
            [
                [
                    ChatMessage(
                        role="user" if msg.sender.is_human else "assistant",
                        content=msg.content,
                    )
                    for msg in conversation
                ]
            ],
        )
    )
    while True:
        text = await streaming.msg_queue.get()

        if text.endswith(streaming.STREAM_END):
            text = text[: -len(streaming.STREAM_END)]
            yield FinalBotMessage(sender=bot, content=text)
            break

        yield InterimBotMessage(sender=bot, content=text)

    # TODO History object is modified after yield (a previous message is appended) - is it confusing ?
    #  Probably better to rethink this (freeze, make copies etc.)
    #  But don't come back to it unless you have more than one bot in your experiment !


if __name__ == "__main__":
    attach_discord_client(discord_client, bot_merger, "swipy")
    discord_client.run(DISCORD_BOT_SECRET)
