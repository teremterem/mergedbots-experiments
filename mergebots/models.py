"""Pydantic models of the MergeBots library."""
# pylint: disable=no-name-in-module
from typing import Callable, AsyncGenerator

from langchain.schema import BaseMessage
from pydantic import BaseModel


class MergedBot(BaseModel):
    """A bot that can interact with other bots."""

    handle: str
    name: str
    description: str
    fulfillment_func: Callable[[BaseMessage], AsyncGenerator[BaseMessage, None]]
