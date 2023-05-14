"""Utility functions for MergeBots library."""
from typing import Callable, AsyncGenerator

from langchain.schema import BaseMessage

FulfillmentFunc = Callable[[BaseMessage], AsyncGenerator[BaseMessage, None]]
