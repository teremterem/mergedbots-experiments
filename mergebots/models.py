"""Pydantic models of the MergeBots library."""
# pylint: disable=no-name-in-module
from pydantic import BaseModel


class MergedBot(BaseModel):
    """A bot that can interact with other bots."""

    name: str
    description: str
