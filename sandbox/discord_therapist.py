# pylint: disable=wrong-import-position
"""A simple Discord bot that reverses messages."""
import itertools
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage

sys.path.append(str(Path(__file__).parents[1]))
from mergebots import BotMerger, MergedMessage, MergedConversation, MergedBot, FinalBotMessage, InterimBotMessage
from mergebots.ext.discord_integration import MergedBotDiscord
from mergebots.ext.langchain_integration import LangChainParagraphStreamingCallback

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


@bot_merger.register_bot("PlainGPT")
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

    model_name = "gpt-3.5-turbo"
    yield InterimBotMessage(sender=bot, content=f"`{model_name}`", is_visible_to_bots=False)

    paragraph_streaming = LangChainParagraphStreamingCallback(bot)
    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        streaming=True,
        callbacks=[paragraph_streaming],
        # TODO user=...,
        pl_tags=["discord_therapist"],
    )
    async for msg in paragraph_streaming.stream_from_coroutine(
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
    ):
        yield msg


if __name__ == "__main__":
    MergedBotDiscord(bot_merger, "PlainGPT").attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
