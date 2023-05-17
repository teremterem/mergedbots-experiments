"""Core logic of MergeBots library."""
from typing import Callable, AsyncGenerator

from .models import MergedBot, MergedMessage, FulfillmentFunc, MergedConversation


class BotMerger:
    """A manager of merged bots."""

    def __init__(self) -> None:
        self._merged_bots = {}

    def register_bot(
        self,
        handle: str,
        name: str = None,
        description: str = None,
    ) -> Callable[[FulfillmentFunc], FulfillmentFunc]:
        """A decorator that registers a fulfillment function as a MergedBot."""

        def decorator(fulfillment_func: FulfillmentFunc) -> FulfillmentFunc:
            self._merged_bots[handle] = MergedBot(
                handle=handle,
                name=name or handle,
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
        first_message_appended = False
        async for response in bot.fulfillment_func(bot, message, history):
            if not first_message_appended:
                # appending the first message to the history after processing has started to separate it from the
                # history for the bot that is being called
                history.messages.append(message)
                first_message_appended = True
            yield response
            # appending bot response to the history after it has been yielded to separate it from the history for the
            # external bots that are possibly calling this bot
            history.messages.append(response)

        # TODO History object is modified after yield (a previous message is appended) - is it confusing ?
        #  Probably better to rethink this (freeze, make copies etc.)
        #  But don't come back to it unless you have more than one bot in your experiment !
