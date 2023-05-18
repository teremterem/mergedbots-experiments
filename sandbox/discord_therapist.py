# pylint: disable=wrong-import-position
"""A simple Discord bot that reverses messages."""
import itertools
import json
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv
from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage

sys.path.append(str(Path(__file__).parents[1]))
from mergebots import BotMerger, MergedMessage, MergedConversation, MergedBot, FinalBotMessage, InterimBotMessage
from mergebots.ext.discord_integration import MergedBotDiscord
from mergebots.ext.langchain_integration import LangChainParagraphStreamingCallback
from sandbox import active_listener_prompt, router_prompt

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


@bot_merger.register_bot(
    "PlainGPT",
    description=(
        "A bot that uses either GPT-4 or ChatGPT to generate responses. Useful when the user seeks information and "
        "needs factual answers."
    ),
)
async def fulfill_as_plain_gpt(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A bot that uses either GPT-4 or ChatGPT to generate responses without any hidden prompts."""
    conversation = [msg for msg in itertools.chain(history.messages, (message,)) if msg.is_visible_to_bots]
    if not conversation:
        yield FinalBotMessage(sender=bot, content="```\nCONVERSATION RESTARTED\n```", is_visible_to_bots=False)
        return

    model_name = "gpt-3.5-turbo"
    yield InterimBotMessage(sender=bot, content=f"`{model_name}`", is_visible_to_bots=False)

    print()
    paragraph_streaming = LangChainParagraphStreamingCallback(bot, verbose=True)
    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        temperature=0.0,
        streaming=True,
        callbacks=[paragraph_streaming],
        # TODO user=...,
        pl_tags=["mb_plain_gpt"],
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
    print()


@bot_merger.register_bot(
    "ActiveListener",
    description="A chatbot that acts as an active listener. Useful when the user needs to vent.",
)
async def fulfill_as_active_listener(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A chatbot that acts as an active listener."""
    conversation = [msg for msg in itertools.chain(history.messages, (message,)) if msg.is_visible_to_bots]
    if not conversation:
        yield FinalBotMessage(sender=bot, content="```\nCONVERSATION RESTARTED\n```", is_visible_to_bots=False)
        return

    model_name = "gpt-4"
    yield InterimBotMessage(sender=bot, content=f"`{model_name}`", is_visible_to_bots=False)

    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        # TODO user=...,
        pl_tags=["mb_active_listener"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=active_listener_prompt.CHAT_PROMPT,
    )

    formatted_conv_parts = [
        f"{'PATIENT' if msg.sender.is_human else 'AI THERAPIST'}: {msg.content}" for msg in conversation
    ]
    result = await llm_chain.arun(conversation="\n\n".join(formatted_conv_parts))
    yield FinalBotMessage(sender=bot, content=result)


@bot_merger.register_bot("RouterBot")
async def fulfill_as_router_bot(
    bot: MergedBot,
    message: MergedMessage,
    history: MergedConversation,
) -> AsyncGenerator[MergedMessage, None]:
    """A bot that routes messages to other bots based on the user's intent."""
    conversation = [msg for msg in itertools.chain(history.messages, (message,)) if msg.is_visible_to_bots]
    if not conversation:
        yield FinalBotMessage(sender=bot, content="```\nCONVERSATION RESTARTED\n```", is_visible_to_bots=False)
        return

    chat_llm = PromptLayerChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,
        model_kwargs={"stop": '"'},
        # TODO user=...,
        pl_tags=["mb_router"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=router_prompt.CHAT_PROMPT,
    )

    bots_json = [
        {"name": handle, "description": bot.description}
        for handle, bot in bot_merger.merged_bots.items()
        if handle != "RouterBot"
    ]
    formatted_conv_parts = [f"{'USER' if msg.sender.is_human else 'ASSISTANT'}: {msg.content}" for msg in conversation]

    chosen_bot_handle = await llm_chain.arun(
        conversation="\n\n".join(formatted_conv_parts), bots=json.dumps(bots_json)
    )
    yield InterimBotMessage(sender=bot, content=f"`{chosen_bot_handle}`", is_visible_to_bots=False)

    # run the chosen bot
    # TODO calling the second bot causes the message to appear twice in the history - fix it
    async for msg in bot_merger.fulfill_message(chosen_bot_handle, message, history):
        yield msg


if __name__ == "__main__":
    MergedBotDiscord(bot_merger, "RouterBot").attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
