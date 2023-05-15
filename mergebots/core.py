"""Core logic of MergeBots library."""
from collections import defaultdict
from typing import Callable, AsyncGenerator

from mergebots.models import MergedBot, MergedMessage, FulfillmentFunc, MergedChannel


class BotMerger:
    """A manager of merged bots."""

    def __init__(self) -> None:
        self.merged_bots = {}
        self.channels = defaultdict(MergedChannel)

    def register_bot(self, handle: str, name: str, description: str) -> Callable[[FulfillmentFunc], FulfillmentFunc]:
        """A decorator that registers a fulfillment function as a MergedBot."""

        def decorator(fulfillment_func: FulfillmentFunc) -> FulfillmentFunc:
            self.merged_bots[handle] = MergedBot(
                handle=handle,
                name=name,
                description=description,
                fulfillment_func=fulfillment_func,
            )
            return fulfillment_func

        return decorator

    async def fulfill_message(
        self,
        message: MergedMessage,
        bot_handle: str,
        channel_custom_id: str,
    ) -> AsyncGenerator[MergedMessage, None]:
        """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
        bot = self.merged_bots[bot_handle]
        conversation = self.channels[channel_custom_id].current_conversation
        conversation.messages.append(message)
        async for response in bot.fulfillment_func(bot, conversation, message):
            conversation.messages.append(response)
            yield response
