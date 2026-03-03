"""
NotebookLM MCP Client
Handles connection to NotebookLM MCP server for notebook management.
"""

import os
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class NotebookLMClient:
    """Client for interacting with NotebookLM via MCP."""

    def __init__(self, command: Optional[str] = None):
        self.command = command or "notebooklm-mcp"
        self.session: Optional[ClientSession] = None
        self._process = None

    async def connect(self) -> bool:
        """Connect to the NotebookLM MCP server."""
        try:
            server_params = StdioServerParameters(
                command=self.command, args=[], env=None
            )

            self._process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            return True
        except Exception as e:
            print(f"Failed to connect to NotebookLM MCP: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the NotebookLM MCP server."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None
        self.session = None

    async def list_notebooks(self) -> List[Dict[str, Any]]:
        """List all NotebookLM notebooks."""
        if not self._process:
            await self.connect()

        try:
            request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            self._process.stdin.write((request + "\n").encode())
            await self._process.stdin.drain()

            response = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=30
            )

            if response:
                data = json.loads(response.decode())
                return data.get("result", {}).get("tools", [])

            return []
        except Exception as e:
            print(f"Error listing notebooks: {e}")
            return []

    async def get_notebook_sources(self, notebook_id: str) -> List[Dict[str, Any]]:
        """Get sources for a specific notebook."""
        try:
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get_notebook_sources",
                        "arguments": {"notebook_id": notebook_id},
                    },
                }
            )

            self._process.stdin.write((request + "\n").encode())
            await self._process.stdin.drain()

            response = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=30
            )

            if response:
                data = json.loads(response.decode())
                return data.get("result", {}).get("content", [])

            return []
        except Exception as e:
            print(f"Error getting notebook sources: {e}")
            return []

    async def search_notebooks(self, query: str) -> List[Dict[str, Any]]:
        """Search across all notebooks."""
        try:
            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "search_notebooks",
                        "arguments": {"query": query},
                    },
                }
            )

            self._process.stdin.write((request + "\n").encode())
            await self._process.stdin.drain()

            response = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=30
            )

            if response:
                data = json.loads(response.decode())
                return data.get("result", {}).get("content", [])

            return []
        except Exception as e:
            print(f"Error searching notebooks: {e}")
            return []

    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        return self._process is not None and self._process.returncode is None


_notebooklm_client: Optional[NotebookLMClient] = None


async def get_notebooklm_client() -> NotebookLMClient:
    """Get or create the NotebookLM client singleton."""
    global _notebooklm_client

    if _notebooklm_client is None:
        _notebooklm_client = NotebookLMClient()

    return _notebooklm_client


async def close_notebooklm_client():
    """Close the NotebookLM client."""
    global _notebooklm_client

    if _notebooklm_client:
        await _notebooklm_client.disconnect()
        _notebooklm_client = None
