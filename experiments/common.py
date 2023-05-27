"""Common stuff."""
from mergedbots import BotManager, InMemoryObjectManager

FAST_GPT_MODEL = "gpt-3.5-turbo"
SLOW_GPT_MODEL = "gpt-3.5-turbo"  # "gpt-4"

bot_manager = BotManager(object_manager=InMemoryObjectManager())
