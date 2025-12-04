"""
Aurora Forester - Pattern Learning
Bounded recursive learning within specific domains
"""

import json
import structlog
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

from ..core.config import settings


logger = structlog.get_logger()


@dataclass
class Pattern:
    """A learned pattern."""
    id: str
    domain: str  # decision, time, project, communication, principle
    pattern_type: str  # e.g., "decision_factor", "work_pattern", "communication_style"
    description: str
    examples: List[Dict[str, Any]]
    confidence: float  # 0.0 to 1.0
    created_at: str
    last_used: Optional[str] = None
    use_count: int = 0


class PatternStore:
    """
    Bounded pattern storage and retrieval.

    Patterns are organized by domain to enforce learning boundaries.
    Each domain has strict limits on what can be learned.
    """

    # Allowed domains - learning is bounded to these only
    ALLOWED_DOMAINS = {
        "decision": "How Graydon evaluates options and makes choices",
        "time": "Work patterns, energy cycles, scheduling preferences",
        "project": "How projects are prioritized, started, and completed",
        "communication": "Writing style, tone preferences, phrasing patterns",
        "principle": "How core values apply to specific situations"
    }

    def __init__(self):
        self.patterns: Dict[str, List[Pattern]] = {domain: [] for domain in self.ALLOWED_DOMAINS}
        self.storage_path = settings.learning_path / "patterns"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load_patterns()

        logger.info("pattern_store.initialized", domains=list(self.ALLOWED_DOMAINS.keys()))

    def _load_patterns(self):
        """Load patterns from disk."""
        for domain in self.ALLOWED_DOMAINS:
            pattern_file = self.storage_path / f"{domain}_patterns.json"
            if pattern_file.exists():
                try:
                    with open(pattern_file, "r") as f:
                        data = json.load(f)
                        self.patterns[domain] = [Pattern(**p) for p in data]
                    logger.info("patterns.loaded", domain=domain, count=len(self.patterns[domain]))
                except Exception as e:
                    logger.error("patterns.load_error", domain=domain, error=str(e))

    def _save_patterns(self, domain: str):
        """Save patterns for a domain to disk."""
        pattern_file = self.storage_path / f"{domain}_patterns.json"
        try:
            with open(pattern_file, "w") as f:
                json.dump([asdict(p) for p in self.patterns[domain]], f, indent=2)
            logger.debug("patterns.saved", domain=domain, count=len(self.patterns[domain]))
        except Exception as e:
            logger.error("patterns.save_error", domain=domain, error=str(e))

    async def observe_interaction(self, interaction) -> None:
        """
        Observe an interaction and potentially learn from it.

        Learning only happens when:
        1. Learning is enabled
        2. The interaction has positive feedback (if feedback_required)
        3. The pattern fits within a defined domain
        """
        if not settings.learning_enabled:
            return

        # If feedback is required, only learn from positive feedback
        if settings.feedback_required and interaction.feedback != "positive":
            return

        # TODO: Implement pattern extraction
        # This is where we would analyze the interaction and extract patterns
        # For now, we just log that we observed it
        logger.debug(
            "patterns.observation",
            channel=interaction.channel,
            has_feedback=interaction.feedback is not None
        )

    async def add_pattern(
        self,
        domain: str,
        pattern_type: str,
        description: str,
        examples: List[Dict[str, Any]],
        confidence: float = 0.5
    ) -> Optional[Pattern]:
        """
        Add a new pattern (requires explicit action, not automatic).

        Returns None if domain is not allowed.
        """
        if domain not in self.ALLOWED_DOMAINS:
            logger.warning("patterns.invalid_domain", domain=domain)
            return None

        pattern = Pattern(
            id=f"{domain}_{len(self.patterns[domain])+1}_{datetime.now().strftime('%Y%m%d')}",
            domain=domain,
            pattern_type=pattern_type,
            description=description,
            examples=examples,
            confidence=confidence,
            created_at=datetime.now().isoformat()
        )

        self.patterns[domain].append(pattern)
        self._save_patterns(domain)

        logger.info("patterns.added", domain=domain, pattern_id=pattern.id)
        return pattern

    async def get_relevant_patterns(self, query: str) -> str:
        """
        Get patterns relevant to a query.

        Returns a formatted string of relevant patterns.
        """
        # TODO: Implement semantic search for relevant patterns
        # For now, return a simple summary of all patterns

        all_patterns = []
        for domain, patterns in self.patterns.items():
            if patterns:
                all_patterns.append(f"\n**{domain.title()} Patterns:**")
                for p in patterns[:3]:  # Limit to 3 per domain
                    all_patterns.append(f"- {p.description} (confidence: {p.confidence:.0%})")

        if not all_patterns:
            return ""

        return "\n".join(all_patterns)

    async def provide_feedback(self, interaction_id: str, feedback: str) -> bool:
        """
        Provide feedback on an interaction.

        feedback should be: "positive", "negative", or "neutral"
        """
        # TODO: Implement feedback mechanism
        logger.info("patterns.feedback", interaction_id=interaction_id, feedback=feedback)
        return True

    def get_domain_summary(self) -> Dict[str, int]:
        """Get count of patterns per domain."""
        return {domain: len(patterns) for domain, patterns in self.patterns.items()}
