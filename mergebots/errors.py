"""This module contains all MergeBots errors."""


class MergeBotsError(Exception):
    """Base class for all MergeBots errors."""


class ErrorWrapper(MergeBotsError):
    """This wrapper is used to contain errors that occurred outside main coroutine."""

    def __init__(self, error: BaseException) -> None:
        self.error = error
        super().__init__(f"{type(error).__module__}.{type(error).__name__}: {error}")
