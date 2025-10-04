from __future__ import annotations

import dataclasses
import logging
import queue
from logging.handlers import QueueHandler, QueueListener
from typing import Literal, Any

from litestar import Litestar
from litestar.types.callable_types import ExceptionLoggingHandler, GetLogger, LifespanHook


@dataclasses.dataclass(frozen=True)
class NewLoggingConfig:
    log_exceptions: Literal["always", "debug", "never"] = "always"
    """Should exceptions be logged"""
    disable_stack_trace: set[int | type[Exception]] = dataclasses.field(default_factory=set)  # noqa: UP007
    """Set of http status codes and exceptions to disable stack trace logging for."""
    exception_logging_handler: ExceptionLoggingHandler | None = None
    """Handler function for logging exceptions."""
    get_logger: GetLogger = logging.getLogger

    def configure_logger(self) -> LifespanHook | None:
        logger: logging.Logger = self.get_logger("litestar")
        handler_queue: queue.Queue[Any] = queue.Queue(-1)
        queue_handler = QueueHandler(handler_queue)
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.addHandler(queue_handler)
        listener = QueueListener(handler_queue, queue_handler, respect_handler_level=True)
        listener.start()

        def shutdown(app: Litestar) -> None:
            listener.stop()

        return shutdown
