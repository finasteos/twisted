"""
Agent capable of using custom tools via Gemini function calling.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from backend.agents.base_agent import BaseAgent, AgentState
from tools.custom_toolkit import TWISTEDToolRegistry
from google.genai import types

logger = logging.getLogger("twisted.agents.tool_user")


class ToolUsingAgent(BaseAgent):
    """
    Extended agent that can execute real-world tools.
    Uses Gemini 3.1 Pro with customtools endpoint.
    """

    def __init__(
        self,
        agent_id: str,
        identity_path: str,
        skills_path: str,
        soul_path: str,
        llm_client,
        vector_store,
        comm_manager,
        tool_registry: TWISTEDToolRegistry,
    ):
        super().__init__(
            agent_id,
            identity_path,
            skills_path,
            soul_path,
            llm_client,
            vector_store,
            comm_manager,
        )
        self.tools = tool_registry
        self.pending_approvals = []

    async def execute_task_with_tools(
        self, task: str, case_id: str, auto_approve_safe: bool = True
    ) -> Dict:
        """
        Execute task, potentially using tools.
        """
        self.state = AgentState.REASONING
        logger.info(
            f"🤖 Agent {self.agent_id} starting task with tools: {task[:50]}..."
        )

        # Prepare tools for Gemini
        tool_declarations = self.tools.get_gemini_tool_declarations()

        # Build prompt with tools context
        prompt = f"""You are {self.identity_data.get("name", "TWISTED Agent")}.
{self.soul_data.get("philosophy", "")}

Task: {task}

You have access to tools. Use them when needed to complete this task.
Always explain your reasoning before calling a tool."""

        # Initial generation with tool availability
        response = await self.llm.generate(
            model="gemini-3.1-pro-preview-customtools",
            contents=prompt,
            tools=tool_declarations,
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            ),
        )

        result_parts = []

        # Iterate through response parts (Gemini might return text AND function calls)
        for part in response.candidates[0].content.parts:
            # Text response
            if part.text:
                result_parts.append({"type": "text", "content": part.text})
                await self._emit_thought(
                    query=task,
                    evidence=[part.text],
                    conclusion="Thinking...",
                    confidence=0.5,
                )

            # Tool call
            if part.function_call:
                tool_name = part.function_call.name
                # Handle args which might be a DotMap or similar from SDK
                args = dict(part.function_call.args) if part.function_call.args else {}

                logger.info(
                    f"🛠️ Agent {self.agent_id} calling tool: {tool_name} with args: {args}"
                )

                # Check if approval needed
                tool_def = self.tools.tools.get(tool_name)
                needs_approval = tool_def.requires_confirmation if tool_def else True

                if needs_approval and not auto_approve_safe:
                    # Queue for user approval (in a real system, this would pause and wait)
                    self.pending_approvals.append(
                        {
                            "tool": tool_name,
                            "args": args,
                            "reasoning": part.text if part.text else "Executing tool",
                        }
                    )
                    result_parts.append(
                        {"type": "awaiting_approval", "tool": tool_name, "args": args}
                    )
                else:
                    # Execute
                    tool_result = await self.tools.execute(
                        tool_name=tool_name,
                        arguments={**args},
                        user_approved=True,
                        case_id=case_id,
                    )

                    result_parts.append(
                        {
                            "type": "tool_result",
                            "tool": tool_name,
                            "result": tool_result,
                        }
                    )

                    # Log event
                    if self.comm:
                        await self.comm.broadcast_event_log(
                            case_id=case_id,
                            level="THINK",
                            agent=self.agent_id,
                            message=f"Executed tool: {tool_name}",
                            metadata={"result_keys": list(tool_result.keys())},
                        )

                    # Continue conversation with tool result
                    follow_up = await self.llm.generate(
                        model="gemini-3.1-pro-preview-customtools",
                        contents=[
                            types.Content(
                                role="user", parts=[types.Part.from_text(prompt)]
                            ),
                            response.candidates[0].content,
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=tool_name, response=tool_result
                                    )
                                ],
                            ),
                        ],
                        tools=tool_declarations,
                    )

                    # Process follow-up (simplified: one more step)
                    for follow_part in follow_up.candidates[0].content.parts:
                        if follow_part.text:
                            result_parts.append(
                                {"type": "text", "content": follow_part.text}
                            )

        return {
            "parts": result_parts,
            "tools_used": [p for p in result_parts if p["type"] == "tool_result"],
            "pending_approvals": self.pending_approvals,
        }
