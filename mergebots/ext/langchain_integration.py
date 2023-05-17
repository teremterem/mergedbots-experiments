"""Integration with the LangChain library."""
import asyncio
import io
from typing import AsyncGenerator, Coroutine

from langchain.callbacks.base import AsyncCallbackHandler

from ..models import MergedBot, MergedMessage, InterimBotMessage, FinalBotMessage


class LangChainParagraphStreamingCallback(AsyncCallbackHandler):  # pylint: disable=abstract-method
    """
    A callback handler that splits the output into paragraphs and dispatches each paragraph as a separate message.
    """

    def __init__(self, bot: MergedBot) -> None:
        self._bot = bot
        self._str_stream = io.StringIO()
        self._msg_queue: asyncio.Queue[MergedMessage | Exception] = asyncio.Queue(maxsize=64)

    async def stream_from_coroutine(self, coro: Coroutine) -> AsyncGenerator[MergedMessage, None]:
        """
        Streams the output of the coroutine as a sequence of messages. Coroutine should be running a LangChain
        component that is already preconfigured to use this callback handler.
        """

        async def coro_wrapper() -> None:
            try:
                await coro
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # don't lose the exception
                await self._msg_queue.put(exc)

        asyncio.create_task(coro_wrapper())
        while True:
            msg = await self._msg_queue.get()
            if isinstance(msg, Exception):
                raise msg
            yield msg

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
            await self._msg_queue.put(InterimBotMessage(sender=self._bot, content=text_so_far[:split_idx]))
            self._str_stream.close()
            self._str_stream = io.StringIO(text_so_far[split_idx + 2 :])

    async def on_llm_end(self, *args, **kwargs) -> None:  # pylint: disable=unused-argument
        # streaming the last paragraph
        await self._msg_queue.put(FinalBotMessage(sender=self._bot, content=self._str_stream.getvalue()))
        self._str_stream.close()
