"""
Browser Use Cloud API Client
Integrates with https://docs.cloud.browser-use.com/introduction
for automated web browsing and research tasks.
"""

import os
import time
from typing import Any, Dict, List, Optional

import httpx

from backend.logging_config import get_logger

logger = get_logger("enrichment.browser_use")

BROWSER_USE_API_BASE = "https://api.browser-use.com/api/v1"


class BrowserUseClient:
    """
    Client for Browser Use Cloud API.
    Enables agents to perform automated web research via cloud-hosted browsers.

    Capabilities:
    - Run browser automation tasks (navigate, extract, fill forms)
    - Perform web research with natural language instructions
    - Extract structured data from web pages
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BROWSER_USE_API_KEY", "")
        self.base_url = BROWSER_USE_API_BASE
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def check_health(self) -> Dict[str, Any]:
        """Check if Browser Use Cloud API is reachable."""
        if not self.api_key:
            return {"status": "disabled", "message": "No API key configured"}

        try:
            client = await self._get_client()
            # List tasks as a health check
            resp = await client.get("/task", timeout=10.0)
            if resp.status_code == 200:
                return {"status": "ok", "message": "Browser Use Cloud connected"}
            return {
                "status": "error",
                "message": f"HTTP {resp.status_code}",
                "code": resp.status_code,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def create_task(
        self,
        instructions: str,
        url: Optional[str] = None,
        max_steps: int = 25,
        use_vision: bool = True,
        save_recording: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new browser automation task.

        Args:
            instructions: Natural language task description
            url: Starting URL (optional)
            max_steps: Maximum browser actions to take
            use_vision: Whether to use vision model for understanding pages
            save_recording: Whether to save a recording of the session
        """
        start = logger.agent_start(
            "BrowserUse", "", "create_task",
            {"instructions": instructions[:200], "url": url},
        )

        try:
            client = await self._get_client()
            payload: Dict[str, Any] = {
                "task": instructions,
                "max_steps": max_steps,
                "use_vision": use_vision,
                "save_browser_data": save_recording,
            }
            if url:
                payload["url"] = url

            logger.agent_step(
                "BrowserUse", "", "create_task",
                "Sending task to Browser Use Cloud",
                {"payload_keys": list(payload.keys())},
            )

            resp = await client.post("/task", json=payload)
            resp.raise_for_status()
            result = resp.json()

            task_id = result.get("id", "unknown")
            logger.agent_complete(
                "BrowserUse", "", "create_task", start,
                {"task_id": task_id},
            )
            return result

        except Exception as e:
            logger.agent_error("BrowserUse", "", "create_task", e)
            return {"error": str(e)}

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status and result of a browser task."""
        try:
            client = await self._get_client()
            resp = await client.get(f"/task/{task_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get task status: {e}", agent="BrowserUse")
            return {"error": str(e)}

    async def wait_for_task(
        self, task_id: str, poll_interval: float = 3.0, timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Poll for task completion.

        Returns the final task result when done.
        """
        start_time = time.time()
        logger.agent_step(
            "BrowserUse", "", "wait_for_task",
            f"Polling task {task_id}",
        )

        while (time.time() - start_time) < timeout:
            status = await self.get_task_status(task_id)

            task_status = status.get("status", "unknown")
            if task_status == "finished":
                logger.info(
                    f"Task {task_id} completed successfully",
                    agent="BrowserUse",
                    operation="wait_for_task",
                )
                return status
            elif task_status == "failed":
                error_msg = status.get("error", "Unknown error")
                logger.error(
                    f"Task {task_id} failed: {error_msg}",
                    agent="BrowserUse",
                    operation="wait_for_task",
                )
                return status
            elif task_status in ("created", "running"):
                import asyncio
                await asyncio.sleep(poll_interval)
            else:
                logger.warning(
                    f"Task {task_id} unknown status: {task_status}",
                    agent="BrowserUse",
                )
                import asyncio
                await asyncio.sleep(poll_interval)

        return {"error": "timeout", "task_id": task_id}

    async def run_research(
        self,
        query: str,
        urls: Optional[List[str]] = None,
        max_steps: int = 30,
    ) -> Dict[str, Any]:
        """
        High-level research method: run a browser task and wait for results.

        Args:
            query: Research question or instructions
            urls: Optional list of URLs to visit
            max_steps: Max browser actions
        """
        start = logger.agent_start(
            "BrowserUse", "", "run_research",
            {"query": query[:200], "url_count": len(urls) if urls else 0},
        )

        instructions = f"Research the following: {query}"
        if urls:
            instructions += f"\n\nStart by visiting these URLs: {', '.join(urls)}"
        instructions += "\n\nExtract and summarize the key findings."

        task = await self.create_task(
            instructions=instructions,
            url=urls[0] if urls else None,
            max_steps=max_steps,
        )

        if "error" in task:
            logger.agent_error(
                "BrowserUse", "", "run_research",
                Exception(task["error"]),
            )
            return task

        task_id = task.get("id")
        if not task_id:
            return {"error": "No task ID returned"}

        result = await self.wait_for_task(task_id)

        logger.agent_complete(
            "BrowserUse", "", "run_research", start,
            {"task_id": task_id, "status": result.get("status")},
        )
        return result

    async def stop_task(self, task_id: str) -> Dict[str, Any]:
        """Stop a running browser task."""
        try:
            client = await self._get_client()
            resp = await client.put(f"/task/{task_id}/stop")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to stop task: {e}", agent="BrowserUse")
            return {"error": str(e)}

    async def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent browser tasks."""
        try:
            client = await self._get_client()
            resp = await client.get("/task", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            return data.get("tasks", []) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}", agent="BrowserUse")
            return []
