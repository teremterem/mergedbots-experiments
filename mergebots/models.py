"""Pydantic models of the MergeBots library."""
# pylint: disable=no-name-in-module
from pydantic import BaseModel

from mergebots.utils import FulfillmentFunc


class MergedBot(BaseModel):
    """A bot that can interact with other bots."""

    handle: str
    name: str
    description: str
    fulfillment_func: FulfillmentFunc
