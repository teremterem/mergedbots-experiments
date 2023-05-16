# pylint: disable=wrong-import-position
"""A simple Discord bot that reverses messages."""
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage

sys.path.append(str(Path(__file__).parents[1]))
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


chat_llm = PromptLayerChatOpenAI(
    model_name="gpt-4",  # "gpt-3.5-turbo",
    request_timeout=300,
    # temperature=0,
    # TODO user=...,
    pl_tags=["discord_therapist"],
)


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    # await tree.sync()
    print("Logged in as", discord_client.user)


@bot_merger.register_bot("swipy", "Swipy", "")
async def therapist_fulfiller(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A dummy bot that reverses messages and repeats them three times."""

    conversation = [*history.messages, message]

    llm_result = await chat_llm.agenerate(
        [
            [
                ChatMessage(
                    role="user" if msg.sender.is_human else "assistant",
                    content=msg.content,
                )
                for msg in conversation
                if msg.is_visible_to_bots
            ]
        ],
        # stop=[
        #     "\n\nHUMAN:",
        #     "\n\nASSISTANT:",
        # ],
    )
    responses = llm_result.generations[0][0].text.split("\n\n")
    for response in responses:
        yield FinalBotMessage(sender=bot, content=response)

    # TODO History object is modified after yield (a previous message is appended) - is it confusing ?
    #  Probably better to rethink this (freeze, make copies etc.)
    #  But don't come back to it unless you have more than one bot in your experiment !


if __name__ == "__main__":
    attach_discord_client(discord_client, bot_merger, "swipy")
    discord_client.run(DISCORD_BOT_SECRET)
