"""MergeBots package."""
from .core import BotMerger
from .errors import MergeBotsError, ErrorWrapper
from .models import FulfillmentFunc

__all__ = [
    "BotMerger",
    "ErrorWrapper",
    "FulfillmentFunc",
    "MergeBotsError",
    # TODO add the rest of the stuff
]
