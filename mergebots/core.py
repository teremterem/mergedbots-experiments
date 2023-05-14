"""Core logic of the MergeBots library."""
from typing import Callable, AsyncGenerator

from langchain.schema import BaseMessage

from mergebots.models import MergedBot
from mergebots.utils import FulfillmentFunc


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

    async def fulfill_message(self, message: BaseMessage, bot_handle: str) -> AsyncGenerator[BaseMessage, None]:
        """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
        # TODO make this function part of some bot class definition ? (BotClient, for example ?)
        async for response in self.get_merged_bot(bot_handle).fulfillment_func(message):
            yield response
