import logging
from typing import Optional, Dict, Any


class ContextAwareLogger:
    def __init__(self, logger: logging.Logger, component: str = ""):
        self._logger = logger
        self._component = component
        self._context: Dict[str, Any] = {}

    def set_context(self, **context: Any) -> None:
        self._context.update(context)

    def clear_context(self) -> None:
        self._context.clear()

    def _format_message(self, message: str, extra_context: Optional[Dict[str, Any]] = None) -> str:
        context = {**self._context}
        if extra_context:
            context.update(extra_context)

        context_parts = []

        if board := context.get("board"):
            context_parts.append(f"board={board}")

        if column := context.get("column"):
            context_parts.append(f"column={column}")

        if item := context.get("item"):
            context_parts.append(f"item={item}")

        if jira_ticket := context.get("jira_ticket"):
            context_parts.append(f"JIRA:{jira_ticket}")

        if correlation_id := context.get("correlation_id"):
            context_parts.append(f"id={correlation_id}")

        if context_parts:
            context_str = f"[{', '.join(context_parts)}]"
            return f"{context_str} {message}"

        return message

    def debug(self, message: str, **context: Any) -> None:
        self._logger.debug(self._format_message(message, context))

    def info(self, message: str, **context: Any) -> None:
        self._logger.info(self._format_message(message, context))

    def warning(self, message: str, **context: Any) -> None:
        self._logger.warning(self._format_message(message, context))

    def error(self, message: str, **context: Any) -> None:
        self._logger.error(self._format_message(message, context))

    def critical(self, message: str, **context: Any) -> None:
        self._logger.critical(self._format_message(message, context))

    def exception(self, message: str, **context: Any) -> None:
        self._logger.exception(self._format_message(message, context))