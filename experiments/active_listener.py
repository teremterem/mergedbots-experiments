"""An active listener bot that listens to the user and asks open-ended questions."""
from typing import AsyncGenerator

from langchain import LLMChain
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from mergedbots import MergedMessage, MergedBot

from experiments.common import SLOW_GPT_MODEL

ACTIVE_LISTENER_PROMPT = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(
            "YOU ARE AN AI THERAPIST. HERE IS A CONVERSATION BETWEEN YOU AND A PATIENT."
        ),
        SystemMessagePromptTemplate.from_template("{conversation}"),
        HumanMessagePromptTemplate.from_template(
            """\
Employ active listening to encourage your patient to think out loud. Respond with no more than three sentences at a \
time and ask open-ended questions. Avoid giving direct advice. The purpose of your questions should be to facilitate \
critical thinking in your patient. Use questions to help the patient arrive at conclusions on their own. Ensure that \
your next message follows these instructions, even if previous messages did not.

NOW, PLEASE PROCEED YOUR CONVERSATION WITH THE PATIENT.

AI THERAPIST:"""
        ),
    ]
)

PATIENT = "PATIENT"
AI_THERAPIST = "AI THERAPIST"

active_listener = MergedBot(
    handle="ActiveListener",
    description="A chatbot that acts as an active listener. Useful when the user needs to vent.",
)


@active_listener
async def active_listener_func(bot: MergedBot, message: MergedMessage) -> AsyncGenerator[MergedMessage, None]:
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
        prompt=ACTIVE_LISTENER_PROMPT,
    )

    formatted_conv_parts = [
        f"{PATIENT if msg.is_sent_by_originator else AI_THERAPIST}: {msg.content}" for msg in conversation
    ]
    result = await llm_chain.arun(conversation="\n\n".join(formatted_conv_parts))
    yield message.final_bot_response(bot, result)
