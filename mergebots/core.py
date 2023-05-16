"""Core logic of MergeBots library."""
from typing import Callable, AsyncGenerator

from mergebots.models import MergedBot, MergedMessage, FulfillmentFunc, MergedConversation


class BotMerger:
    """A manager of merged bots."""

    def __init__(self) -> None:
        self._merged_bots = {}

    def register_bot(self, handle: str, name: str, description: str) -> Callable[[FulfillmentFunc], FulfillmentFunc]:
        """A decorator that registers a fulfillment function as a MergedBot."""

        def decorator(fulfillment_func: FulfillmentFunc) -> FulfillmentFunc:
            self._merged_bots[handle] = MergedBot(
                handle=handle,
                name=name,
                description=description,
                fulfillment_func=fulfillment_func,
            )
            return fulfillment_func

        return decorator

    async def fulfill_message(
        self,
        bot_handle: str,
        message: MergedMessage,
        history: MergedConversation,
    ) -> AsyncGenerator[MergedMessage, None]:
        """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
        bot = self._merged_bots[bot_handle]
        # TODO append first message with "latency" (after it is processed by MergedBot and not before)
        history.messages.append(message)
        async for response in bot.fulfillment_func(bot, message, history):
            yield response
            history.messages.append(response)
