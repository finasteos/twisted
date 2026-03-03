"""
Heartbeat Engine - Background Task Manager
Manages async processing without freezing the UI
"""

import asyncio
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid


@dataclass
class HeartbeatTask:
    task_id: str
    name: str
    status: str = "pending"
    progress: float = 0.0
    message: str = ""
    current_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    callbacks: list = field(default_factory=list)
    error: Optional[str] = None


class HeartbeatEngine:
    """
    Background task runner that prevents UI freezing.
    Runs in separate asyncio event loop.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._tasks: Dict[str, HeartbeatTask] = {}
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._initialized = True

    def start(self):
        """Start the heartbeat engine in a background thread."""
        if self._running:
            return

        self._running = True
        thread = threading.Thread(target=self._run_event_loop, daemon=True)
        thread.start()

    def _run_event_loop(self):
        """Run asyncio event loop in background thread."""
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_forever()

    def stop(self):
        """Stop the heartbeat engine."""
        self._running = False
        if self._event_loop:
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)

    def create_task(self, name: str) -> str:
        """Create a new heartbeat task."""
        task_id = str(uuid.uuid4())[:8]
        task = HeartbeatTask(task_id=task_id, name=name)
        self._tasks[task_id] = task
        return task_id

    def update_progress(
        self,
        task_id: str,
        progress: float,
        message: str,
        current_agent: Optional[str] = None,
        status: str = "running",
    ):
        """Update task progress (thread-safe)."""
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        task.progress = progress
        task.message = message
        task.current_agent = current_agent
        task.status = status
        task.updated_at = datetime.now()

        for callback in task.callbacks:
            try:
                callback(task)
            except Exception:
                pass

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status."""
        if task_id not in self._tasks:
            return None

        task = self._tasks[task_id]
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "current_agent": task.current_agent,
            "error": task.error,
        }

    def set_error(self, task_id: str, error: str):
        """Mark task as failed with error."""
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        task.status = "error"
        task.error = error
        task.updated_at = datetime.now()

    def set_complete(self, task_id: str):
        """Mark task as completed."""
        if task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        task.status = "completed"
        task.progress = 1.0
        task.message = "Complete"
        task.updated_at = datetime.now()

    def register_callback(self, task_id: str, callback: Callable):
        """Register a callback for status updates."""
        if task_id in self._tasks:
            self._tasks[task_id].callbacks.append(callback)


heartbeat_engine = HeartbeatEngine()
