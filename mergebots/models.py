"""Pydantic models of MergeBots library."""
# pylint: disable=no-name-in-module
from typing import Callable, AsyncGenerator

from pydantic import BaseModel

FulfillmentFunc = Callable[["MergedBot", "MergedMessage"], AsyncGenerator["MergedMessage", None]]


class MergedParticipant(BaseModel):
    """A chat participant."""

    name: str
    is_human: bool


class MergedBot(MergedParticipant):
    """A bot that can interact with other bots."""

    is_human: bool = False

    handle: str
    description: str
    fulfillment_func: FulfillmentFunc


class MergedUser(MergedParticipant):
    """A user that can interact with bots."""

    is_human: bool = True


class MergedMessage(BaseModel):
    """A message that can be sent by a bot or a user."""

    sender: MergedParticipant
    content: str
    keep_typing: bool


class MergedUserMessage(MergedMessage):
    """A message that can be sent by a user."""

    sender: MergedUser
    keep_typing: bool = False


class MergedBotMessage(MergedMessage):
    """A message that can be sent by a bot."""

    sender: MergedBot


class InterimBotMessage(MergedBotMessage):
    """
    An interim message that can be sent by a bot. An interim message indicates that the bot is still typing
    (there will be more messages).
    """

    keep_typing: bool = True


class FinalBotMessage(MergedBotMessage):
    """A final message that can be sent by a bot. A final message indicates that the bot has finished typing."""

    keep_typing: bool = False
