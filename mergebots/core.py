"""Core logic of the MergeBots library."""
import asyncio
from typing import Generator

from langchain.schema import BaseMessage, ChatMessage


async def fulfill_message(message: BaseMessage) -> Generator[BaseMessage, None, None]:
    """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
    for i, num in enumerate(("one", "two", "three", "four", "five", "six", "seven")):
        if i % 2:
            await asyncio.sleep(5)
        yield ChatMessage(role="assistant", content=f"{message.content} {num}")
