"""Core logic of the MergeBots library."""
import asyncio
from typing import Generator

from langchain.schema import BaseMessage, ChatMessage


async def fulfill_message(message: BaseMessage) -> Generator[BaseMessage, None, None]:
    """Fulfill a message. Returns a generator that would yield zero or more responses to the message."""
    for num in ("one", "two", "three"):
        await asyncio.sleep(2)
        yield ChatMessage(role="assistant", content=f"{message.content} {num}")
