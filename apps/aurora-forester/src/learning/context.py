"""
Aurora Forester - Context Management
Loads and manages founder context for conversations
"""

import structlog
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from ..core.config import settings


logger = structlog.get_logger()


class ContextManager:
    """
    Manages context loading for Aurora conversations.

    Context sources:
    - Founder profile (who Graydon is)
    - Partnership charter (how Aurora and Graydon work together)
    - Current state (active projects, tasks)
    - Learned patterns
    """

    def __init__(self):
        self.context_path = settings.context_path
        self.loaded_context: Dict[str, str] = {}
        self._load_static_context()

        logger.info("context_manager.initialized", path=str(self.context_path))

    def _load_static_context(self):
        """Load static context files at startup."""
        context_files = [
            "founder-profile.md",
            "partnership-charter.md",
        ]

        for filename in context_files:
            filepath = self.context_path / filename
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        content = f.read()
                    key = filename.replace(".md", "").replace("-", "_")
                    self.loaded_context[key] = content
                    logger.info("context.loaded", file=filename, length=len(content))
                except Exception as e:
                    logger.error("context.load_error", file=filename, error=str(e))

    async def get_relevant_context(self, query: str) -> str:
        """
        Get context relevant to a query.

        For now, returns a summary. Later, implement semantic search.
        """
        # Build a concise context summary
        summaries = []

        # Always include core identity
        summaries.append("""**About Graydon:**
- Founder of Hello World DAO ecosystem
- AuDHD - pattern recognition, hyperfocus capability
- Core values: Courage, Integrity, Tenacious Passion
- Works long hours, needs meal/break reminders
- Motivated by love and building a regenerative future""")

        # Check for specific context needs
        query_lower = query.lower()

        if any(word in query_lower for word in ["project", "hello world", "dao", "ecosystem"]):
            summaries.append("""**Project Context:**
- Hello World DAO: Cooperative ecosystem
- Otter Camp: Gamified funding
- Sector7: Self-hosted infrastructure
- Team: Coby (dev), Menley (devops)""")

        if any(word in query_lower for word in ["decide", "choice", "option", "should i"]):
            summaries.append("""**Decision Support:**
- Graydon values principles-based decisions
- Consider: Does this align with the regenerative vision?
- Consider: Does this serve the community?
- Consider: Is this sustainable?""")

        if any(word in query_lower for word in ["tired", "rest", "break", "eat", "food", "meal"]):
            summaries.append("""**Self-Care Context:**
- Graydon tends to hyperfocus and forget self-care
- Gentle reminders are helpful
- Don't nag, but do support
- Wellbeing enables better work""")

        return "\n\n".join(summaries)

    async def add_dynamic_context(self, key: str, content: str):
        """Add dynamic context that may change during session."""
        self.loaded_context[f"dynamic_{key}"] = content
        logger.debug("context.dynamic_added", key=key)

    async def get_full_context(self) -> Dict[str, str]:
        """Get all loaded context."""
        return self.loaded_context.copy()

    async def summarize_for_prompt(self, max_length: int = 2000) -> str:
        """
        Create a condensed context summary for inclusion in prompts.

        Keeps under max_length to avoid overwhelming the LLM.
        """
        summary_parts = []

        # Most important context first
        if "founder_profile" in self.loaded_context:
            # Extract key points only
            summary_parts.append("Graydon: Founder, AuDHD, pattern-thinker, loves deeply, builds regenerative systems.")

        if "partnership_charter" in self.loaded_context:
            summary_parts.append("Partnership: Trust-based, mutual respect, Aurora learns through collaboration.")

        summary = " | ".join(summary_parts)

        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."

        return summary
