"""
Local LLM client for LM Studio / Ollama
"""

import asyncio
import aiohttp
from typing import Dict, Optional, List, Any


class LocalLLMClient:
    """Client for local LLM via LM Studio or Ollama API"""

    def __init__(
        self,
        base_url: str = "http://172.20.10.3:1234",
        model: str = "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b",
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_errors": 0,
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate completion using local LLM
        """
        session = await self._get_session()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"Local LLM error {resp.status}: {error_text}")

                data = await resp.json()

                self.usage_stats["total_requests"] += 1

                return data["choices"][0]["message"]["content"]

        except Exception as e:
            self.usage_stats["total_errors"] += 1
            raise

    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ):
        """Streaming generation"""
        session = await self._get_session()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        async with session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as resp:
            async for line in resp.content:
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except:
                            pass

    async def check_health(self) -> Dict[str, Any]:
        """Check if local LLM is available"""
        try:
            session = await self._get_session()

            # Try models list endpoint first
            async with session.get(
                f"{self.base_url}/v1/models",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [
                        m.get("id", m.get("name", "unknown"))
                        for m in data.get("model", [])
                    ]
                    return {
                        "status": "ok",
                        "available": True,
                        "models": models,
                        "current_model": self.model,
                        "url": self.base_url,
                    }

            # Fallback: try a simple completion
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return {"status": "ok", "available": True, "model": self.model}
                else:
                    return {
                        "status": "error",
                        "available": False,
                        "error": f"HTTP {resp.status}",
                    }

        except Exception as e:
            return {"status": "error", "available": False, "error": str(e)}

    def get_usage(self) -> Dict[str, int]:
        return self.usage_stats.copy()


import json
