# pylint: disable=import-error
"""A simple Discord bot that reverses messages."""
import json
import os
from typing import AsyncGenerator

import discord
from dotenv import load_dotenv
from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage
from mergedbots import BotMerger, MergedMessage, MergedBot
from mergedbots.ext.discord_integration import MergedBotDiscord
from mergedbots.ext.langchain_integration import LangChainParagraphStreamingCallback

import active_listener_prompt
import router_prompt

load_dotenv()

PLAIN_GPT = "PlainGPT"
ACTIVE_LISTENER = "ActiveListener"
ROUTER_BOT = "RouterBot"

PATIENT = "PATIENT"
AI_THERAPIST = "AI THERAPIST"

FAST_GPT_MODEL = "gpt-3.5-turbo"
SLOW_GPT_MODEL = "gpt-3.5-turbo"  # "gpt-4"

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

bot_merger = BotMerger()
discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
    print("Logged in as", discord_client.user)


@bot_merger.register_bot(
    PLAIN_GPT,
    description=(
        "A bot that uses either GPT-4 or ChatGPT to generate responses. Useful when the user seeks information and "
        "needs factual answers."
    ),
)
async def plain_gpt(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    """A bot that uses either GPT-4 or ChatGPT to generate responses without any hidden prompts."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    model_name = SLOW_GPT_MODEL
    yield message.service_followup_for_user(bot, f"`{model_name}`")

    print()
    paragraph_streaming = LangChainParagraphStreamingCallback(bot, message, verbose=True)
    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        temperature=0.0,
        streaming=True,
        callbacks=[paragraph_streaming],
        model_kwargs={"user": str(message.originator.uuid)},
        pl_tags=["mb_plain_gpt"],
    )
    async for msg in paragraph_streaming.stream_from_coroutine(
        chat_llm.agenerate(
            [
                [
                    ChatMessage(
                        role="user" if msg.is_sent_by_originator else "assistant",
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
    ACTIVE_LISTENER,
    description="A chatbot that acts as an active listener. Useful when the user needs to vent.",
)
async def active_listener(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    """A bot that acts as an active listener."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    model_name = SLOW_GPT_MODEL
    yield message.service_followup_for_user(bot, f"`{model_name} ({bot.handle})`")

    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        model_kwargs={
            "stop": [f"\n\n{PATIENT}:", f"\n\n{AI_THERAPIST}:"],
            "user": str(message.originator.uuid),
        },
        pl_tags=["mb_active_listener"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=active_listener_prompt.CHAT_PROMPT,
    )

    formatted_conv_parts = [
        f"{PATIENT if msg.is_sent_by_originator else AI_THERAPIST}: {msg.content}" for msg in conversation
    ]
    result = await llm_chain.arun(conversation="\n\n".join(formatted_conv_parts))
    yield message.final_bot_response(bot, result)


@bot_merger.register_bot(ROUTER_BOT)
async def router_bot(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    """A bot that routes messages to other bots based on the user's intent."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    chat_llm = PromptLayerChatOpenAI(
        model_name=FAST_GPT_MODEL,
        temperature=0.0,
        model_kwargs={
            "stop": ['"', "\n"],
            "user": str(message.originator.uuid),
        },
        pl_tags=["mb_router"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=router_prompt.CHAT_PROMPT,
    )

    bots_json = [
        {"name": other_handle, "description": other_bot.description}
        for other_handle, other_bot in bot_merger.merged_bots.items()
        if other_bot.handle != bot.handle
    ]
    formatted_conv_parts = [
        f"{'USER' if msg.is_sent_by_originator else 'ASSISTANT'}: {msg.content}" for msg in conversation
    ]

    # choose a bot and run it
    chosen_bot_handle = await llm_chain.arun(
        conversation="\n\n".join(formatted_conv_parts), bots=json.dumps(bots_json)
    )
    chosen_bot = bot_merger.get_bot(chosen_bot_handle, fallback_bot_handle="PlainGPT")
    async for msg in chosen_bot.fulfill(message):
        yield msg


if __name__ == "__main__":
    MergedBotDiscord(bot=bot_merger.get_bot(ROUTER_BOT)).attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
