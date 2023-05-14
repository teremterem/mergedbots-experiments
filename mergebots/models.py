"""Pydantic models."""
# pylint: disable=no-name-in-module
from pydantic import BaseModel


class Bot(BaseModel):
    """Bot definition."""

    name: str
    description: str
