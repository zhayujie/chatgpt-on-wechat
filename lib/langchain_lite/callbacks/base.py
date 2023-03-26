"""Base callback handler that can be used to handle callbacks from lib."""
import asyncio
import functools
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from lib.langchain_lite.schema import BotAction, BotFinish, LLMResult


class BaseCallbackHandler(ABC):
    """Base callback handler that can be used to handle callbacks from lib."""

    @property
    def always_verbose(self) -> bool:
        """Whether to call verbose callbacks even if verbose is False."""
        return False

    @property
    def ignore_llm(self) -> bool:
        """Whether to ignore LLM callbacks."""
        return False

    @property
    def ignore_chain(self) -> bool:
        """Whether to ignore chain callbacks."""
        return False

    @property
    def ignore_bot(self) -> bool:
        """Whether to ignore bot callbacks."""
        return False

    @abstractmethod
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""

    @abstractmethod
    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """Run on new LLM token. Only available when streaming is enabled."""

    @abstractmethod
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""

    @abstractmethod
    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""

    @abstractmethod
    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""

    @abstractmethod
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""

    @abstractmethod
    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""

    @abstractmethod
    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""

    @abstractmethod
    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""

    @abstractmethod
    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""

    @abstractmethod
    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""

    @abstractmethod
    def on_bot_action(self, action: BotAction, **kwargs: Any) -> Any:
        """Run on bot action."""

    @abstractmethod
    def on_bot_finish(self, finish: BotFinish, **kwargs: Any) -> Any:
        """Run on bot end."""


class BaseCallbackManager(BaseCallbackHandler, ABC):
    """Base callback manager that can be used to handle callbacks from LangChain-Lite."""

    @property
    def is_async(self) -> bool:
        """Whether the callback manager is async."""
        return False

    @abstractmethod
    def add_handler(self, callback: BaseCallbackHandler) -> None:
        """Add a handler to the callback manager."""

    @abstractmethod
    def remove_handler(self, handler: BaseCallbackHandler) -> None:
        """Remove a handler from the callback manager."""

    def set_handler(self, handler: BaseCallbackHandler) -> None:
        """Set handler as the only handler on the callback manager."""
        self.set_handlers([handler])

    @abstractmethod
    def set_handlers(self, handlers: List[BaseCallbackHandler]) -> None:
        """Set handlers as the only handlers on the callback manager."""


class CallbackManager(BaseCallbackManager):
    """Callback manager that can be used to handle callbacks from lib."""

    def __init__(self, handlers: List[BaseCallbackHandler]) -> None:
        """Initialize callback manager."""
        self.handlers: List[BaseCallbackHandler] = handlers

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    handler.on_llm_start(serialized, prompts, **kwargs)

    def on_llm_new_token(
        self, token: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when LLM generates a new token."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    handler.on_llm_new_token(token, **kwargs)

    def on_llm_end(
        self, response: LLMResult, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when LLM ends running."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    handler.on_llm_end(response)

    def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    handler.on_llm_error(error)

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    handler.on_chain_start(serialized, inputs, **kwargs)

    def on_chain_end(
        self, outputs: Dict[str, Any], verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when chain ends running."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    handler.on_chain_end(outputs)

    def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when chain errors."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    handler.on_chain_error(error)

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    handler.on_tool_start(serialized, input_str, **kwargs)

    def on_bot_action(
        self, action: BotAction, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    handler.on_bot_action(action, **kwargs)

    def on_tool_end(self, output: str, verbose: bool = False, **kwargs: Any) -> None:
        """Run when tool ends running."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    handler.on_tool_end(output, **kwargs)

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when tool errors."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    handler.on_tool_error(error)

    def on_text(self, text: str, verbose: bool = False, **kwargs: Any) -> None:
        """Run on additional input from chains and bots."""
        for handler in self.handlers:
            if verbose or handler.always_verbose:
                handler.on_text(text, **kwargs)

    def on_bot_finish(
        self, finish: BotFinish, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run on bot end."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    handler.on_bot_finish(finish, **kwargs)

    def add_handler(self, handler: BaseCallbackHandler) -> None:
        """Add a handler to the callback manager."""
        self.handlers.append(handler)

    def remove_handler(self, handler: BaseCallbackHandler) -> None:
        """Remove a handler from the callback manager."""
        self.handlers.remove(handler)

    def set_handlers(self, handlers: List[BaseCallbackHandler]) -> None:
        """Set handlers as the only handlers on the callback manager."""
        self.handlers = handlers


class AsyncCallbackHandler(BaseCallbackHandler):
    """Async callback handler that can be used to handle callbacks from lib."""

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""

    async def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""

    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""

    async def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""

    async def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""

    async def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""

    async def on_bot_action(self, action: BotAction, **kwargs: Any) -> None:
        """Run on bot action."""

    async def on_bot_finish(self, finish: BotFinish, **kwargs: Any) -> None:
        """Run on bot end."""


class AsyncCallbackManager(BaseCallbackManager):
    """Async callback manager that can be used to handle callbacks from LangChain-Lite."""

    @property
    def is_async(self) -> bool:
        """Return whether the handler is async."""
        return True

    def __init__(self, handlers: List[BaseCallbackHandler]) -> None:
        """Initialize callback manager."""
        self.handlers: List[BaseCallbackHandler] = handlers

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_llm_start):
                        await handler.on_llm_start(serialized, prompts, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_llm_start, serialized, prompts, **kwargs
                            ),
                        )

    async def on_llm_new_token(
        self, token: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_llm_new_token):
                        await handler.on_llm_new_token(token, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_llm_new_token, token, **kwargs
                            ),
                        )

    async def on_llm_end(
        self, response: LLMResult, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when LLM ends running."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_llm_end):
                        await handler.on_llm_end(response, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_llm_end, response, **kwargs),
                        )

    async def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        for handler in self.handlers:
            if not handler.ignore_llm:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_llm_error):
                        await handler.on_llm_error(error, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_llm_error, error, **kwargs),
                        )

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_chain_start):
                        await handler.on_chain_start(serialized, inputs, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_chain_start, serialized, inputs, **kwargs
                            ),
                        )

    async def on_chain_end(
        self, outputs: Dict[str, Any], verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when chain ends running."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_chain_end):
                        await handler.on_chain_end(outputs, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_chain_end, outputs, **kwargs),
                        )

    async def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when chain errors."""
        for handler in self.handlers:
            if not handler.ignore_chain:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_chain_error):
                        await handler.on_chain_error(error, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_chain_error, error, **kwargs),
                        )

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_tool_start):
                        await handler.on_tool_start(serialized, input_str, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_tool_start, serialized, input_str, **kwargs
                            ),
                        )

    async def on_tool_end(
        self, output: str, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when tool ends running."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_tool_end):
                        await handler.on_tool_end(output, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_tool_end, output, **kwargs),
                        )

    async def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        verbose: bool = False,
        **kwargs: Any
    ) -> None:
        """Run when tool errors."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_tool_error):
                        await handler.on_tool_error(error, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(handler.on_tool_error, error, **kwargs),
                        )

    async def on_text(self, text: str, verbose: bool = False, **kwargs: Any) -> None:
        """Run when text is printed."""
        for handler in self.handlers:
            if verbose or handler.always_verbose:
                if asyncio.iscoroutinefunction(handler.on_text):
                    await handler.on_text(text, **kwargs)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, functools.partial(handler.on_text, text, **kwargs)
                    )

    async def on_bot_action(
        self, action: BotAction, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run on bot action."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_bot_action):
                        await handler.on_bot_action(action, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_bot_action, action, **kwargs
                            ),
                        )

    async def on_bot_finish(
        self, finish: BotFinish, verbose: bool = False, **kwargs: Any
    ) -> None:
        """Run when bot finishes."""
        for handler in self.handlers:
            if not handler.ignore_bot:
                if verbose or handler.always_verbose:
                    if asyncio.iscoroutinefunction(handler.on_bot_finish):
                        await handler.on_bot_finish(finish, **kwargs)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            None,
                            functools.partial(
                                handler.on_bot_finish, finish, **kwargs
                            ),
                        )

    def add_handler(self, handler: BaseCallbackHandler) -> None:
        """Add a handler to the callback manager."""
        self.handlers.append(handler)

    def remove_handler(self, handler: BaseCallbackHandler) -> None:
        """Remove a handler from the callback manager."""
        self.handlers.remove(handler)

    def set_handlers(self, handlers: List[BaseCallbackHandler]) -> None:
        """Set handlers as the only handlers on the callback manager."""
        self.handlers = handlers


def get_callback_manager() -> BaseCallbackManager:
    """Return the shared callback manager."""
    return SharedCallbackManager()


class Singleton:
    """A thread-safe singleton class that can be inherited from."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> Any:
        """Create a new shared instance of the class."""
        if cls._instance is None:
            with cls._lock:
                # Another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance


class SharedCallbackManager(Singleton, BaseCallbackManager):
    """A thread-safe singleton CallbackManager."""

    _callback_manager: CallbackManager = CallbackManager(handlers=[])

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        with self._lock:
            self._callback_manager.on_llm_start(serialized, prompts, **kwargs)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        with self._lock:
            self._callback_manager.on_llm_end(response, **kwargs)

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run when LLM generates a new token."""
        with self._lock:
            self._callback_manager.on_llm_new_token(token, **kwargs)

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        with self._lock:
            self._callback_manager.on_llm_error(error, **kwargs)

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""
        with self._lock:
            self._callback_manager.on_chain_start(serialized, inputs, **kwargs)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        with self._lock:
            self._callback_manager.on_chain_end(outputs, **kwargs)

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""
        with self._lock:
            self._callback_manager.on_chain_error(error, **kwargs)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        with self._lock:
            self._callback_manager.on_tool_start(serialized, input_str, **kwargs)

    def on_bot_action(self, action: BotAction, **kwargs: Any) -> Any:
        """Run on bot action."""
        with self._lock:
            self._callback_manager.on_bot_action(action, **kwargs)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""
        with self._lock:
            self._callback_manager.on_tool_end(output, **kwargs)

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""
        with self._lock:
            self._callback_manager.on_tool_error(error, **kwargs)

    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""
        with self._lock:
            self._callback_manager.on_text(text, **kwargs)

    def on_bot_finish(self, finish: BotFinish, **kwargs: Any) -> None:
        """Run on bot end."""
        with self._lock:
            self._callback_manager.on_bot_finish(finish, **kwargs)

    def add_handler(self, callback: BaseCallbackHandler) -> None:
        """Add a callback to the callback manager."""
        with self._lock:
            self._callback_manager.add_handler(callback)

    def remove_handler(self, callback: BaseCallbackHandler) -> None:
        """Remove a callback from the callback manager."""
        with self._lock:
            self._callback_manager.remove_handler(callback)

    def set_handlers(self, handlers: List[BaseCallbackHandler]) -> None:
        """Set handlers as the only handlers on the callback manager."""
        with self._lock:
            self._callback_manager.handlers = handlers
