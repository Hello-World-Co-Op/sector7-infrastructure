"""
Aurora Forester - LLM Client
Handles communication with Ollama for inference
"""

import httpx
import structlog
from typing import List, Dict, Optional, AsyncIterator
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings


logger = structlog.get_logger()


class OllamaClient:
    """Client for Ollama LLM inference."""

    def __init__(self):
        self.base_url = settings.ollama_host
        self.default_model = settings.ollama_model
        self.fast_model = settings.ollama_model_fast
        self.client = httpx.AsyncClient(timeout=120.0)

        logger.info("ollama.client_initialized", base_url=self.base_url)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> str:
        """
        Send a chat completion request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to settings.ollama_model)
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            The assistant's response text
        """
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("message", {}).get("content", "")

            logger.debug(
                "ollama.chat_complete",
                model=model,
                input_messages=len(messages),
                response_length=len(content)
            )

            return content

        except httpx.HTTPError as e:
            logger.error("ollama.chat_error", error=str(e))
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream a chat completion response.

        Yields chunks of the response as they arrive.
        """
        model = model or self.default_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content

        except httpx.HTTPError as e:
            logger.error("ollama.stream_error", error=str(e))
            raise

    async def quick_response(self, prompt: str) -> str:
        """
        Get a quick response using the fast model.

        Good for simple queries that don't need deep reasoning.
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model=self.fast_model)

    async def check_health(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error("ollama.list_models_error", error=str(e))
            return []

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
