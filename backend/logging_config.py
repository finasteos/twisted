"""
TWISTED — Structured Debug Logging System
Writes JSON-lines log file for easy debugging and testing.
All agent operations, LLM calls, memory ops, and pipeline steps are logged.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


LOG_DIR = Path(os.getenv("TWISTED_LOG_DIR", "./logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "twisted_debug.log"


class JsonLineFormatter(logging.Formatter):
    """Formats log records as JSON lines for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        for key in ("agent", "case_id", "operation", "duration_ms",
                     "step", "details", "error", "memory_stats"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class TwistedLogger:
    """
    Central logging facade for TWISTED.
    Provides structured logging with both console and file output.

    Usage:
        from backend.logging_config import get_logger
        logger = get_logger("agent.context_weaver")
        logger.agent_step("context_weaver", case_id, "analyze", "Extracting entities", {"doc_count": 5})
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"twisted.{name}")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up file (JSON lines) and console handlers."""
        if self.logger.handlers:
            return  # Already configured

        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # JSON lines file handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonLineFormatter())
        self.logger.addHandler(file_handler)

        # Console handler (human-readable)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_fmt = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_fmt)
        self.logger.addHandler(console_handler)

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(message, extra=kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(message, extra=kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(message, extra=kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self.logger.exception(message, extra=kwargs)

    # ── High-level structured logging helpers ──

    def agent_start(self, agent: str, case_id: str, operation: str,
                    details: Optional[Dict] = None) -> float:
        """Log the start of an agent operation. Returns start_time for duration calc."""
        start = time.time()
        self.logger.info(
            f"[{agent}] START {operation}",
            extra={
                "agent": agent,
                "case_id": case_id,
                "operation": operation,
                "step": "start",
                "details": details or {},
            },
        )
        return start

    def agent_step(self, agent: str, case_id: str, operation: str,
                   step_name: str, details: Optional[Dict] = None) -> None:
        """Log a sub-step within an agent operation."""
        self.logger.info(
            f"[{agent}] STEP {operation} -> {step_name}",
            extra={
                "agent": agent,
                "case_id": case_id,
                "operation": operation,
                "step": step_name,
                "details": details or {},
            },
        )

    def agent_complete(self, agent: str, case_id: str, operation: str,
                       start_time: float, details: Optional[Dict] = None) -> None:
        """Log the completion of an agent operation."""
        duration_ms = round((time.time() - start_time) * 1000, 2)
        self.logger.info(
            f"[{agent}] DONE {operation} ({duration_ms}ms)",
            extra={
                "agent": agent,
                "case_id": case_id,
                "operation": operation,
                "step": "complete",
                "duration_ms": duration_ms,
                "details": details or {},
            },
        )

    def agent_error(self, agent: str, case_id: str, operation: str,
                    error: Exception, details: Optional[Dict] = None) -> None:
        """Log an agent operation failure."""
        self.logger.error(
            f"[{agent}] ERROR {operation}: {error}",
            extra={
                "agent": agent,
                "case_id": case_id,
                "operation": operation,
                "step": "error",
                "error": str(error),
                "details": details or {},
            },
        )

    def llm_call(self, agent: str, model: str, prompt_len: int,
                 response_len: int, duration_ms: float) -> None:
        """Log an LLM API call."""
        self.logger.debug(
            f"[{agent}] LLM call: model={model} prompt={prompt_len}ch response={response_len}ch ({duration_ms}ms)",
            extra={
                "agent": agent,
                "operation": "llm_call",
                "details": {
                    "model": model,
                    "prompt_length": prompt_len,
                    "response_length": response_len,
                },
                "duration_ms": duration_ms,
            },
        )

    def memory_op(self, operation: str, collection: str,
                  details: Optional[Dict] = None) -> None:
        """Log a memory/vector store operation."""
        self.logger.debug(
            f"[Memory] {operation} on {collection}",
            extra={
                "agent": "memory",
                "operation": operation,
                "details": {"collection": collection, **(details or {})},
            },
        )

    def pipeline_stage(self, case_id: str, stage: str, percent: float,
                       message: str) -> None:
        """Log a pipeline stage transition."""
        self.logger.info(
            f"[Pipeline] {stage} {percent:.0f}%: {message}",
            extra={
                "agent": "pipeline",
                "case_id": case_id,
                "operation": stage,
                "step": f"{percent:.0f}%",
                "details": {"message": message},
            },
        )


# Module-level factory
_loggers: Dict[str, TwistedLogger] = {}


def get_logger(name: str) -> TwistedLogger:
    """Get or create a TwistedLogger instance."""
    if name not in _loggers:
        _loggers[name] = TwistedLogger(name)
    return _loggers[name]
