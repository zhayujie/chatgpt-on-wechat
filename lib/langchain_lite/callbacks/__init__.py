"""Callback handlers that allow listening to events in LangChain-Lite."""

from lib.langchain_lite.callbacks.base import (
    BaseCallbackHandler,
    BaseCallbackManager,
    CallbackManager,
    SharedCallbackManager
)


def get_callback_manager() -> BaseCallbackManager:
    """Return the shared callback manager."""
    return SharedCallbackManager()


def set_handler(handler: BaseCallbackHandler) -> None:
    """Set handler."""
    callback = get_callback_manager()
    callback.set_handler(handler)


__all__ = [
    "CallbackManager",
    "SharedCallbackManager",
    "set_handler",
    "get_callback_manager",
    "BaseCallbackManager"
]
