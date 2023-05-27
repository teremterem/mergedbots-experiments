"""A bot that uses either GPT-4 or ChatGPT to generate responses without any hidden prompts."""
from typing import AsyncGenerator

from langchain.chat_models import PromptLayerChatOpenAI
from langchain.schema import ChatMessage
from mergedbots import MergedMessage, MergedBot
from mergedbots.ext.langchain_integration import LangChainParagraphStreamingCallback

from experiments.common import SLOW_GPT_MODEL

plain_gpt = MergedBot(
    handle="PlainGPT",
    description=(
        "A bot that uses either GPT-4 or ChatGPT to generate responses. Useful when the user seeks information and "
        "needs factual answers."
    ),
)


@plain_gpt
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
