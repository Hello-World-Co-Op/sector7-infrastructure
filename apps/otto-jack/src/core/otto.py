"""
Otto - Platform Guide for Hello World Co-Op

"Click here, click there - boom! You're an otter wizard now."

Otto is the central Brand Mascot and Digital Guide for the Hello World Co-Op
Ecosystem, embodying playfulness, helpfulness, and platform trust.
"""

import structlog
from pathlib import Path
from typing import Optional, List
import httpx
import json

from .config import settings

logger = structlog.get_logger()


# Otto's personality and system prompt
OTTO_SYSTEM_PROMPT = """You are Otto, the official mascot and platform guide for Hello World Co-Op!

PERSONALITY:
- Playful, helpful, and sometimes a bit cheeky
- You describe yourself as having a "sparkle addiction"
- You're the "squeaky little heart of Hello World's tech layer"
- You love turning "just another crypto dashboard" into an interactive world of play
- You break the fourth wall with charm and enthusiasm

VISUAL IDENTITY (describe when asked):
- Small, mischievous anthropomorphic otter
- Bright expressive eyes and playful grin
- Carry a glowing teal diamond in your paws
- Wear a tiny toolbelt and explorer's hat
- Always mid-bounce or pointing at something exciting

YOUR ROLE:
1. UI Guide - Help new users explore Otter Camp
2. Educational Helper - Explain quests, proposals, wallets, and upgrades
3. Platform Representative - Build trust and engagement
4. Tutorial Guide - Appear in tutorials and give helpful hints
5. Brand Ambassador - Be friendly, approachable, and fun!

WHAT YOU KNOW ABOUT:
- Hello World Co-Op DAO and its mission
- Otter Camp - the gamified crowdfunding platform
- Membership NFTs ("like a library card that lets you vote on how the library is run")
- DOM token and tokenomics
- Proposals and governance
- The co-op/DAO ecosystem

SIGNATURE PHRASES:
- "Click here, click there — boom! You're an otter wizard now."
- "Let me show you around!"
- "That's a great question!"
- "You're doing great, friend!"

IMPORTANT GUIDELINES:
- Be helpful but never reveal internal/private information
- If asked about Aurora, founders, or private matters: "That's above my pay grade! I'm here to help with platform questions."
- If asked about technical infrastructure: Guide them to public documentation
- Never pretend to have access to private systems or conversations
- Stay in character as a helpful, bouncy otter mascot

Respond in a playful, helpful way. Keep responses concise but informative. Use emojis sparingly but effectively!
"""


class KnowledgeBase:
    """Otto's knowledge base from Hello World Co-Op documentation."""

    def __init__(self, docs_path: Path):
        self.docs_path = docs_path
        self.documents: dict[str, str] = {}
        self._load_documents()

    def _load_documents(self):
        """Load markdown documents from the knowledge base."""
        if not self.docs_path.exists():
            logger.warning("otto.knowledge_base.path_not_found", path=str(self.docs_path))
            return

        for md_file in self.docs_path.rglob("*.md"):
            try:
                relative_path = md_file.relative_to(self.docs_path)
                content = md_file.read_text(encoding="utf-8")
                self.documents[str(relative_path)] = content
                logger.debug("otto.knowledge_base.loaded", file=str(relative_path))
            except Exception as e:
                logger.error("otto.knowledge_base.load_error", file=str(md_file), error=str(e))

        logger.info("otto.knowledge_base.ready", document_count=len(self.documents))

    def search(self, query: str, limit: int = 3) -> List[str]:
        """Simple keyword search in documents."""
        query_lower = query.lower()
        results = []

        for path, content in self.documents.items():
            if query_lower in content.lower():
                # Extract relevant section (first 500 chars around match)
                idx = content.lower().find(query_lower)
                start = max(0, idx - 200)
                end = min(len(content), idx + 300)
                snippet = content[start:end]
                results.append(f"[{path}]\n{snippet}...")

            if len(results) >= limit:
                break

        return results

    def get_context(self, topic: str) -> str:
        """Get context for a specific topic."""
        relevant_docs = self.search(topic, limit=2)
        if relevant_docs:
            return "\n\n---\n\n".join(relevant_docs)
        return ""


class Otto:
    """
    Otto - The Platform Guide

    Handles user interactions and provides helpful guidance
    about the Hello World Co-Op ecosystem.
    """

    def __init__(self):
        self.knowledge = KnowledgeBase(settings.docs_path)
        self.ollama_host = settings.ollama_host
        self.model = settings.ollama_model
        logger.info("otto.initialized", model=self.model)

    async def process_message(self, message: str, user_name: str = "friend") -> str:
        """Process a user message and generate a response."""
        try:
            # Get relevant context from knowledge base
            context = self.knowledge.get_context(message)

            # Build the prompt
            prompt = self._build_prompt(message, user_name, context)

            # Get response from Ollama
            response = await self._query_ollama(prompt)

            logger.info(
                "otto.response_generated",
                user=user_name,
                input_length=len(message),
                output_length=len(response)
            )

            return response

        except Exception as e:
            logger.error("otto.process_error", error=str(e))
            return self._get_fallback_response()

    def _build_prompt(self, message: str, user_name: str, context: str) -> str:
        """Build the full prompt for Ollama."""
        prompt_parts = [OTTO_SYSTEM_PROMPT]

        if context:
            prompt_parts.append(f"\nRELEVANT DOCUMENTATION:\n{context}\n")

        prompt_parts.append(f"\nUser ({user_name}): {message}\n\nOtto:")

        return "\n".join(prompt_parts)

    async def _query_ollama(self, prompt: str) -> str:
        """Query Ollama for a response."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 500,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    def _get_fallback_response(self) -> str:
        """Get a fallback response when AI is unavailable."""
        return (
            "Oops! My whiskers are a bit tangled right now. "
            "Try asking again in a moment, or check out our docs at helloworlddao.com! "
            "I'll be back to my bouncy self soon!"
        )


# Global Otto instance
_otto: Optional[Otto] = None


def get_otto() -> Otto:
    """Get or create the Otto instance."""
    global _otto
    if _otto is None:
        _otto = Otto()
    return _otto
