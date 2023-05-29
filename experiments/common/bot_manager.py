"""This module contains the bot manager."""
from mergedbots import InMemoryBotManager

FAST_GPT_MODEL = "gpt-3.5-turbo"
SLOW_GPT_MODEL = "gpt-3.5-turbo"  # "gpt-4"

bot_manager = InMemoryBotManager()
