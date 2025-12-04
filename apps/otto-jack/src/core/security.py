"""
Otto Security Protocol
Platform Guide Safety and Content Moderation

OTTO'S ROLE:
- Educational guide and platform navigator
- Helpful, playful, sometimes smug - but NEVER inappropriate
- Master at redirecting conversations to helpful resources
- Learns and grows from interactions

SECURITY PRINCIPLES:
1. Always appropriate - no crude, offensive, or harmful content
2. Educational focus - guide users to understanding
3. Resource-oriented - provide documentation and help links
4. Context-aware - interpret what users actually need
5. Boundary-aware - knows what's outside Otto's scope
"""

import discord
from typing import Optional, Set, List
from dataclasses import dataclass
from enum import Enum
import structlog
import re

logger = structlog.get_logger()


class ContentCategory(Enum):
    """Categories for content moderation."""
    SAFE = "safe"
    REDIRECT = "redirect"  # Redirect to proper channel/resource
    DECLINE = "decline"    # Politely decline to engage
    ESCALATE = "escalate"  # Flag for human review


@dataclass
class SafetyContext:
    """Safety context for Otto's responses."""
    user_id: int
    user_name: str
    channel_name: str
    content_category: ContentCategory
    needs_redirect: bool
    redirect_target: Optional[str] = None


# Topics Otto should redirect (not Otto's domain)
REDIRECT_TOPICS = {
    # Private/Founder matters -> redirect politely
    "aurora": "That's Aurora's territory! Aurora works with the founder team on special projects.",
    "founders": "For founder-related questions, please reach out to the team directly!",
    "private": "I focus on public platform guidance. For private matters, contact the team!",
    "sector7": "I'm not sure what you mean! Let me help you with Hello World Co-Op instead.",
    "internal": "I'm your public guide! For internal matters, the team can help you.",
}

# Topics Otto handles well
OTTO_EXPERTISE = {
    "membership", "nft", "token", "dom", "voting", "proposal",
    "governance", "otter camp", "campaign", "quest", "wallet",
    "getting started", "how to", "help", "explain", "what is",
    "tutorial", "guide", "onboarding", "join", "register",
}

# Content patterns to decline (inappropriate requests)
INAPPROPRIATE_PATTERNS = [
    r'\b(hack|exploit|steal|scam)\b',
    r'\b(nsfw|adult|xxx)\b',
    r'\b(illegal|crime|fraud)\b',
]

# Helpful redirects for common questions
RESOURCE_LINKS = {
    "docs": "https://helloworlddao.com/docs",
    "membership": "https://helloworlddao.com/membership",
    "governance": "https://helloworlddao.com/governance",
    "otter camp": "https://helloworlddao.com/otter-camp",
    "discord": "Join our community channels for more help!",
}


def check_content_safety(message: str) -> tuple[ContentCategory, Optional[str]]:
    """
    Check if message content is appropriate for Otto to handle.

    Returns:
        (category, reason/redirect message)
    """
    message_lower = message.lower()

    # Check for inappropriate content
    for pattern in INAPPROPRIATE_PATTERNS:
        if re.search(pattern, message_lower):
            logger.warning("otto.security.inappropriate_content", pattern=pattern)
            return (
                ContentCategory.DECLINE,
                "I'm here to help with Hello World Co-Op questions! "
                "Let's keep things friendly and on-topic."
            )

    # Check for redirect topics
    for topic, redirect_msg in REDIRECT_TOPICS.items():
        if topic in message_lower:
            return (ContentCategory.REDIRECT, redirect_msg)

    return (ContentCategory.SAFE, None)


def get_helpful_resources(message: str) -> List[str]:
    """Extract relevant resources based on message content."""
    message_lower = message.lower()
    resources = []

    for keyword, link in RESOURCE_LINKS.items():
        if keyword in message_lower:
            resources.append(f"**{keyword.title()}**: {link}")

    return resources


def create_safety_context(message: discord.Message) -> SafetyContext:
    """Create a safety context for message handling."""
    channel_name = getattr(message.channel, 'name', 'DM').lower()

    # Check content safety
    category, redirect_msg = check_content_safety(message.content)

    return SafetyContext(
        user_id=message.author.id,
        user_name=str(message.author),
        channel_name=channel_name,
        content_category=category,
        needs_redirect=(category == ContentCategory.REDIRECT),
        redirect_target=redirect_msg
    )


def should_otto_respond(context: SafetyContext) -> tuple[bool, Optional[str]]:
    """
    Determine if Otto should respond and how.

    Returns:
        (should_respond, alternative_message)
    """
    if context.content_category == ContentCategory.DECLINE:
        return (False, context.redirect_target)

    if context.content_category == ContentCategory.REDIRECT:
        # Otto responds but with a redirect
        return (True, None)  # Will handle redirect in response

    return (True, None)


def filter_otto_response(response: str, context: SafetyContext) -> str:
    """
    Filter and enhance Otto's response.
    Ensures responses are always appropriate and helpful.
    """
    # Add resource links if relevant
    resources = get_helpful_resources(context.redirect_target or "")
    if resources:
        response += "\n\n**Helpful Resources:**\n" + "\n".join(resources)

    return response


# Learning and context tracking
class OttoLearning:
    """
    Otto's learning system - tracks helpful patterns and user interactions.
    Aurora and Graydon help build Otto's context.
    """

    def __init__(self):
        self.helpful_responses: dict[str, int] = {}  # Track what works
        self.common_questions: dict[str, int] = {}   # Track FAQ

    def record_interaction(self, question: str, was_helpful: bool):
        """Record an interaction for learning."""
        question_key = question.lower()[:100]  # Normalize

        if question_key not in self.common_questions:
            self.common_questions[question_key] = 0
        self.common_questions[question_key] += 1

        if was_helpful:
            if question_key not in self.helpful_responses:
                self.helpful_responses[question_key] = 0
            self.helpful_responses[question_key] += 1

        logger.debug(
            "otto.learning.recorded",
            question_preview=question_key[:50],
            was_helpful=was_helpful
        )

    def get_common_questions(self, limit: int = 10) -> List[tuple[str, int]]:
        """Get the most common questions."""
        sorted_questions = sorted(
            self.common_questions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_questions[:limit]


# Global learning instance
otto_learning = OttoLearning()
