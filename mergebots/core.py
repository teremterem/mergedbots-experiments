"""Core logic of MergeBots library."""
from typing import Callable, AsyncGenerator

from mergebots.models import MergedBot, MergedMessage, FulfillmentFunc


class BotMerger:
    """A manager of merged bots."""

    def __init__(self) -> None:
        self._merged_bots = {}

    def register_bot(self, handle: str, name: str, description: str) -> Callable[[FulfillmentFunc], FulfillmentFunc]:
        """A decorator that registers a fulfillment function as a MergedBot."""

        def decorator(fulfillment_func: FulfillmentFunc) -> FulfillmentFunc:
            self.register_bot_obj(
                MergedBot(
                    handle=handle,
                    name=name,
                    description=description,
                    fulfillment_func=fulfillment_func,
                )
            )
            return fulfillment_func

        return decorator

    def register_bot_obj(self, bot: MergedBot) -> None:
        """Register a MergedBot object."""
        self._merged_bots[bot.handle] = bot

    def get_merged_bot(self, bot_handle: str) -> "MergedBot":
        """Get a merged bot by its handle."""
        return self._merged_bots[bot_handle]

    async def fulfill_message(self, message: MergedMessage, bot_handle: str) -> AsyncGenerator[MergedMessage, None]:
        """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
        bot = self.get_merged_bot(bot_handle)
        async for response in bot.fulfillment_func(bot, message):
            yield response
