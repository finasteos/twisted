"""
Gemini 3.1 Pro Custom Tools integration for TWISTED.
Enables agents to execute real-world actions.
"""

import json
import logging
import os
import time
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from google.genai import types

logger = logging.getLogger("twisted.tools")

class ToolCategory(Enum):
    FILE_SYSTEM = "file_system"
    WEB_AUTOMATION = "web_automation"
    CODE_EXECUTION = "code_execution"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATION = "communication"


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, str] # parameter_name -> description
    category: ToolCategory
    requires_confirmation: bool  # User approval required?
    dangerous: bool  # Can cause data loss or high risk?


class TWISTEDToolRegistry:
    """
    Registry of custom tools available to agents.
    All tools are opt-in, logged, and sandboxed where possible.
    """

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.implementations: Dict[str, Callable] = {}
        self.execution_log: List[Dict] = []

    def register_tool(
        self,
        definition: ToolDefinition,
        implementation: Callable
    ):
        """Register a new tool."""
        self.tools[definition.name] = definition
        self.implementations[definition.name] = implementation
        logger.info(f"🛠️ Registered tool: {definition.name}")

    def get_gemini_tool_declarations(self) -> List[types.Tool]:
        """Convert to Gemini function declaration format."""
        declarations = []

        for name, definition in self.tools.items():
            func_decl = types.FunctionDeclaration(
                name=name,
                description=definition.description,
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        k: types.Schema(type="STRING", description=v)
                        for k, v in definition.parameters.items()
                    },
                    required=list(definition.parameters.keys())
                )
            )
            declarations.append(types.Tool(function_declarations=[func_decl]))

        return declarations

    async def execute(
        self,
        tool_name: str,
        arguments: Dict,
        user_approved: bool = False,
        case_id: Optional[str] = None
    ) -> Dict:
        """
        Execute tool with safety checks.
        """
        definition = self.tools.get(tool_name)
        if not definition:
            return {"error": f"Unknown tool: {tool_name}"}

        # Check approval requirements
        if definition.requires_confirmation and not user_approved:
            return {
                "status": "awaiting_approval",
                "tool": tool_name,
                "arguments": arguments,
                "reason": f"Tool '{tool_name}' requires user confirmation"
            }

        # Log execution
        execution_record = {
            "timestamp": time.time(),
            "case_id": case_id,
            "tool": tool_name,
            "arguments": arguments,
            "approved": user_approved
        }

        try:
            # Execute
            impl = self.implementations[tool_name]
            result = await impl(**arguments, case_id=case_id)
            execution_record["result_summary"] = str(result)[:200]
            execution_record["success"] = True

        except Exception as e:
            logger.error(f"Tool execution failed ({tool_name}): {e}")
            execution_record["error"] = str(e)
            execution_record["success"] = False
            result = {"error": str(e)}

        self.execution_log.append(execution_record)
        return result


class TWISTEDTools:
    """
    Concrete tool implementations for TWISTED agents.
    """

    def __init__(self, registry: TWISTEDToolRegistry):
        self.registry = registry
        self._register_all()

    def _register_all(self):
        """Register all TWISTED tools."""

        # File System Tools
        self.registry.register_tool(
            ToolDefinition(
                name="view_file",
                description="Read contents of a file in the case directory",
                parameters={"file_path": "Path to file relative to case directory"},
                category=ToolCategory.FILE_SYSTEM,
                requires_confirmation=False,
                dangerous=False
            ),
            self._view_file
        )

        self.registry.register_tool(
            ToolDefinition(
                name="search_files",
                description="Search for files by name pattern in case directory",
                parameters={"pattern": "Glob pattern like '*.pdf' or '*contract*'"},
                category=ToolCategory.FILE_SYSTEM,
                requires_confirmation=False,
                dangerous=False
            ),
            self._search_files
        )

        # Code Execution (Sandboxed)
        self.registry.register_tool(
            ToolDefinition(
                name="analyze_data",
                description="Execute Python analysis on case data (sandboxed)",
                parameters={
                    "code": "Python code to execute",
                    "data_source": "Which collection to query: case_ingestion, case_analysis, etc."
                },
                category=ToolCategory.CODE_EXECUTION,
                requires_confirmation=True,
                dangerous=False  # Sandboxed
            ),
            self._analyze_data
        )

        # Web Automation
        self.registry.register_tool(
            ToolDefinition(
                name="fetch_webpage",
                description="Fetch and extract text from a URL",
                parameters={"url": "Full URL to fetch"},
                category=ToolCategory.WEB_AUTOMATION,
                requires_confirmation=False,
                dangerous=False
            ),
            self._fetch_webpage
        )

        self.registry.register_tool(
            ToolDefinition(
                name="search_current_info",
                description="Search for current information on a topic",
                parameters={"query": "Search query"},
                category=ToolCategory.WEB_AUTOMATION,
                requires_confirmation=False,
                dangerous=False
            ),
            self._search_current
        )

        # Communication Tools
        self.registry.register_tool(
            ToolDefinition(
                name="draft_email",
                description="Draft an email based on case context and strategy",
                parameters={
                    "recipient_type": "lawyer, insurance, counterparty, etc.",
                    "tone": "formal, assertive, empathetic, etc.",
                    "key_points": "Brief list of specific points to include"
                },
                category=ToolCategory.COMMUNICATION,
                requires_confirmation=False,
                dangerous=False
            ),
            self._draft_email
        )

        self.registry.register_tool(
            ToolDefinition(
                name="generate_mermaid",
                description="Generate Mermaid diagram for visualization",
                parameters={
                    "diagram_type": "flowchart, sequence, gantt, mindmap",
                    "content_description": "What the diagram should show"
                },
                category=ToolCategory.DATA_ANALYSIS,
                requires_confirmation=False,
                dangerous=False
            ),
            self._generate_mermaid
        )

    # Tool Implementations

    async def _view_file(self, file_path: str, case_id: str = None) -> Dict:
        """Safely view file contents."""
        try:
            safe_path = self._sanitize_path(file_path, case_id)
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {
                "file_path": file_path,
                "size": len(content),
                "content_preview": content[:2000],
                "full_content_available": len(content) <= 2000
            }
        except Exception as e:
            return {"error": str(e)}

    async def _search_files(self, pattern: str, case_id: str = None) -> Dict:
        """Search for files matching pattern."""
        import fnmatch

        case_dir = Path(f"./uploads/{case_id}")
        if not case_dir.exists():
            return {"error": f"Case directory not found: {case_id}"}

        matches = []
        for root, dirs, files in os.walk(case_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    rel_path = os.path.relpath(os.path.join(root, filename), case_dir)
                    matches.append({
                        "name": filename,
                        "path": rel_path,
                        "size": os.path.getsize(os.path.join(root, filename))
                    })

        return {
            "pattern": pattern,
            "matches_found": len(matches),
            "files": matches[:20]  # Limit results
        }

    async def _analyze_data(self, code: str, data_source: str, case_id: str = None) -> Dict:
        """
        Execute sandboxed Python analysis.
        """
        import io
        import sys

        # Very restricted globals
        safe_globals = {
            "__builtins__": {
                "len": len, "range": range, "enumerate": enumerate, "zip": zip,
                "map": map, "filter": filter, "sum": sum, "min": min, "max": max,
                "abs": abs, "round": round, "str": str, "int": int, "float": float,
                "list": list, "dict": dict, "set": set, "tuple": tuple,
            }
        }

        output_buffer = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output_buffer

        try:
            # Note: real sandbox would use multiprocessing or a separate container
            exec(code, safe_globals)
            return {
                "success": True,
                "output": output_buffer.getvalue(),
                "variables_count": len([k for k in safe_globals if not k.startswith("__")])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            sys.stdout = original_stdout

    async def _fetch_webpage(self, url: str, **kwargs) -> Dict:
        """Fetch webpage with safety checks."""
        import requests
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return {"error": "Only HTTP/HTTPS URLs allowed"}

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return {
                "url": url,
                "text_preview": response.text[:2000],
                "status_code": response.status_code
            }
        except Exception as e:
            return {"error": str(e)}

    async def _search_current(self, query: str, **kwargs) -> Dict:
        """Mock search for now, would integrate with Tavily/Serp."""
        return {
            "query": query,
            "results": [
                {"title": f"Result for {query}", "snippet": "Sample information...", "url": "https://example.com"}
            ]
        }

    async def _draft_email(self, recipient_type: str, tone: str,
                          key_points: str, case_id: str = None) -> Dict:
        """Simplified draft implementation."""
        # In full version, this would call LLM within the tool implementation
        return {
            "subject": f"Follow-up regarding {recipient_type}",
            "body": f"Dear recipient,\n\nPoints covered: {key_points}\n\nRegards,\nTWISTED Engine",
            "recipient_type": recipient_type,
            "tone": tone
        }

    async def _generate_mermaid(self, diagram_type: str,
                                content_description: str, case_id: str = None) -> Dict:
        """Mock Mermaid specs."""
        return {
            "diagram_type": diagram_type,
            "mermaid_code": f"{diagram_type}\n  A[Start] --> B[End]",
            "description": content_description
        }

    def _sanitize_path(self, file_path: str, case_id: Optional[str]) -> Path:
        """Ensure path stays within case directory."""
        if case_id:
            base = Path(f"./uploads/{case_id}").resolve()
        else:
            base = Path("./uploads").resolve()

        requested = (base / file_path).resolve()
        if not str(requested).startswith(str(base)):
            raise ValueError("Path traversal attempt detected")
        return requested
