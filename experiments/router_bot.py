"""A bot that routes messages to other bots based on the user's intent."""
import json
from typing import AsyncGenerator

from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from mergedbots import MergedMessage, MergedBot

from experiments.active_listener import active_listener
from experiments.common import FAST_GPT_MODEL
from experiments.plain_gpt import plain_gpt

ROUTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("HERE IS A CONVERSATION BETWEEN A USER AND AN AI ASSISTANT."),
        SystemMessagePromptTemplate.from_template("{conversation}"),
        SystemMessagePromptTemplate.from_template(
            "AND HERE IS A LIST OF BOTS WHO COULD BE USED TO RESPOND TO THE CONVERSATION ABOVE."
        ),
        SystemMessagePromptTemplate.from_template("{bots}"),
        HumanMessagePromptTemplate.from_template(
            """\
Which of the bots above would you like to use to respond to the LAST message of the conversation above?

BOT NAME: \""""
        ),
    ]
)

router_bot = MergedBot(handle="RouterBot")
other_bots = {bot.handle: bot for bot in (plain_gpt, active_listener)}


@router_bot
async def router_bot(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
    """A bot that routes messages to other bots based on the user's intent."""
    conversation = message.get_full_conversion()
    if not conversation:
        yield message.service_followup_as_final_response(bot, "```\nCONVERSATION RESTARTED\n```")
        return

    chat_llm = PromptLayerChatOpenAI(
        model_name=FAST_GPT_MODEL,
        temperature=0.0,
        max_tokens=10,
        model_kwargs={
            "stop": ['"', "\n"],
            "user": str(message.originator.uuid),
        },
        pl_tags=["mb_router"],
    )
    llm_chain = LLMChain(
        llm=chat_llm,
        prompt=ROUTER_PROMPT,
    )

    bots_json = [
        {"name": other_handle, "description": other_bot.description} for other_handle, other_bot in other_bots.items()
    ]
    formatted_conv_parts = [
        f"{'USER' if msg.is_sent_by_originator else 'ASSISTANT'}: {msg.content}" for msg in conversation
    ]

    # choose a bot and run it
    chosen_bot_handle = await llm_chain.arun(
        conversation="\n\n".join(formatted_conv_parts), bots=json.dumps(bots_json)
    )
    print(f"ROUTING TO: {chosen_bot_handle}")
    chosen_bot = other_bots.get(chosen_bot_handle, plain_gpt)
    async for msg in chosen_bot.fulfill(message):
        yield msg
