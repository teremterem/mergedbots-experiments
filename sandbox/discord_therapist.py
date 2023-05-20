# pylint: disable=wrong-import-position
"""A simple Discord bot that reverses messages."""
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
from mergebots import BotMerger, MergedMessage, MergedBot
from mergebots.ext.discord_integration import MergedBotDiscord
from mergebots.ext.langchain_integration import LangChainParagraphStreamingCallback
from sandbox import active_listener_prompt, router_prompt

load_dotenv()

DISCORD_BOT_SECRET = os.environ["DISCORD_BOT_SECRET"]

bot_merger = BotMerger()
discord_client = discord.Client(intents=discord.Intents.default())


@discord_client.event
async def on_ready() -> None:
    """Called when the client is done preparing the data received from Discord."""
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
) -> AsyncGenerator[MergedMessage, None]:
    """A bot that uses either GPT-4 or ChatGPT to generate responses without any hidden prompts."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    model_name = "gpt-3.5-turbo"
    yield message.service_followup_for_user(bot, f"`{model_name}`")

    print()
    paragraph_streaming = LangChainParagraphStreamingCallback(bot, message, verbose=True)
    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        temperature=0.0,
        streaming=True,
        callbacks=[paragraph_streaming],
        model_kwargs={"user": str(message.original_initiator.uuid)},
        pl_tags=["mb_plain_gpt"],
    )
    async for msg in paragraph_streaming.stream_from_coroutine(
        chat_llm.agenerate(
            [
                [
                    ChatMessage(
                        role="assistant" if msg.sender == bot else "user",
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
) -> AsyncGenerator[MergedMessage, None]:
    """A chatbot that acts as an active listener."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    model_name = "gpt-3.5-turbo"  # "gpt-4"
    yield message.service_followup_for_user(bot, f"`{model_name}`")

    chat_llm = PromptLayerChatOpenAI(
        model_name=model_name,
        model_kwargs={
            "stop": ["AI THERAPIST:", "USER:"],
            "user": str(message.original_initiator.uuid),
        },
        pl_tags=["mb_active_listener"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=active_listener_prompt.CHAT_PROMPT,
    )

    formatted_conv_parts = [
        f"{'AI THERAPIST' if msg.sender == bot else 'PATIENT'}: {msg.content}" for msg in conversation
    ]
    result = await llm_chain.arun(conversation="\n\n".join(formatted_conv_parts))
    yield message.final_bot_response(bot, result)


@bot_merger.register_bot("RouterBot")
async def fulfill_as_router_bot(
    bot: MergedBot,
    message: MergedMessage,
) -> AsyncGenerator[MergedMessage, None]:
    """A bot that routes messages to other bots based on the user's intent."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    chat_llm = PromptLayerChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.0,
        model_kwargs={
            "stop": ['"'],
            "user": str(message.original_initiator.uuid),
        },
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
    formatted_conv_parts = [f"{'ASSISTANT' if msg.sender == bot else 'USER'}: {msg.content}" for msg in conversation]

    chosen_bot_handle = await llm_chain.arun(
        conversation="\n\n".join(formatted_conv_parts), bots=json.dumps(bots_json)
    )
    yield message.service_followup_for_user(bot, f"`{chosen_bot_handle}`")

    # run the chosen bot
    async for msg in bot_merger.fulfill_message(chosen_bot_handle, message):
        yield msg


if __name__ == "__main__":
    MergedBotDiscord(bot_merger, "RouterBot").attach_discord_client(discord_client)
    discord_client.run(DISCORD_BOT_SECRET)
