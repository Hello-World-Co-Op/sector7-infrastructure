"""
Aurora Forester Security Model
Access control and privacy protection for Aurora

SECURITY LEVELS:
- FOUNDER: Full access (Graydon, Menley, Coby)
- AGENT_TEAM: Aurora system agents
- MEMBER: Regular co-op members (redirect to Otto)
- PUBLIC: Non-members (redirect to Otto)

PROTECTED TOPICS:
- Sector7: Ghost project, never discuss outside secure channels
- Private conversations: Never share outside aurora-forester channel
- Personal projects: Founder-only visibility
"""

import discord
from typing import Optional, Set
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class SecurityLevel(Enum):
    """Access levels for Aurora interactions."""
    FOUNDER = "founder"
    AGENT_TEAM = "agent_team"
    DEVELOPMENT = "development"
    MEMBER = "member"
    PUBLIC = "public"


@dataclass
class SecurityContext:
    """Security context for a message/interaction."""
    user_id: int
    user_name: str
    channel_id: int
    channel_name: str
    guild_id: Optional[int]
    roles: Set[str]
    is_dm: bool
    security_level: SecurityLevel
    is_secure_channel: bool


# Authorized user IDs (will be loaded from config)
AUTHORIZED_USERS = {
    # These should be Discord user IDs
    # Graydon, Menley, Coby - to be configured
}

# Role names that grant access
FOUNDER_ROLES = {"Founder", "Co-Founder", "founder", "co-founder"}
DEV_ROLES = {"Development", "Developer", "development", "developer", "Dev Team"}
AGENT_ROLES = {"Agent Team", "Aurora System", "agent-team"}

# Secure channel names
SECURE_CHANNELS = {"aurora-forester", "aurora", "founder-private", "sector7"}

# Protected topics - never discuss outside secure channels
PROTECTED_TOPICS = {
    "sector7": "This is a protected project. I can't discuss it here.",
    "ghost project": "I'm not familiar with that topic in this context.",
    "private infrastructure": "That's not something I can discuss publicly.",
}


def get_security_level(member: discord.Member, channel: discord.abc.GuildChannel) -> SecurityLevel:
    """Determine the security level for a guild member."""
    role_names = {role.name for role in member.roles}

    # Check for founder-level access
    if role_names & FOUNDER_ROLES:
        return SecurityLevel.FOUNDER

    # Check for agent team access
    if role_names & AGENT_ROLES:
        return SecurityLevel.AGENT_TEAM

    # Check for development team access
    if role_names & DEV_ROLES:
        return SecurityLevel.DEVELOPMENT

    # Default to member level
    return SecurityLevel.MEMBER


def is_secure_channel(channel_name: str) -> bool:
    """Check if a channel is designated as secure."""
    return channel_name.lower() in {c.lower() for c in SECURE_CHANNELS}


def check_protected_content(message: str) -> Optional[str]:
    """Check if message contains protected topics."""
    message_lower = message.lower()
    for topic, response in PROTECTED_TOPICS.items():
        if topic in message_lower:
            return response
    return None


def create_security_context(message: discord.Message) -> SecurityContext:
    """Create a security context from a Discord message."""
    is_dm = isinstance(message.channel, discord.DMChannel)

    if is_dm:
        # DMs are considered semi-secure (1:1 with Aurora)
        return SecurityContext(
            user_id=message.author.id,
            user_name=str(message.author),
            channel_id=message.channel.id,
            channel_name="DM",
            guild_id=None,
            roles=set(),
            is_dm=True,
            security_level=SecurityLevel.MEMBER,  # Will be upgraded if user is authorized
            is_secure_channel=False
        )

    # Guild channel
    member = message.author
    channel = message.channel

    role_names = {role.name for role in member.roles} if hasattr(member, 'roles') else set()
    security_level = get_security_level(member, channel) if isinstance(member, discord.Member) else SecurityLevel.PUBLIC

    return SecurityContext(
        user_id=message.author.id,
        user_name=str(message.author),
        channel_id=channel.id,
        channel_name=channel.name,
        guild_id=message.guild.id if message.guild else None,
        roles=role_names,
        is_dm=False,
        security_level=security_level,
        is_secure_channel=is_secure_channel(channel.name)
    )


def should_aurora_respond(context: SecurityContext) -> tuple[bool, Optional[str]]:
    """
    Determine if Aurora should respond directly or redirect to Otto.

    Returns:
        (should_respond, redirect_message)
        - (True, None) = Aurora should respond
        - (False, message) = Redirect to Otto with message
    """
    # Founders always get Aurora
    if context.security_level == SecurityLevel.FOUNDER:
        logger.info(
            "security.access_granted",
            user=context.user_name,
            level="founder",
            channel=context.channel_name
        )
        return (True, None)

    # Agent team gets Aurora in appropriate contexts
    if context.security_level == SecurityLevel.AGENT_TEAM:
        return (True, None)

    # Development team gets Aurora in dev channels
    if context.security_level == SecurityLevel.DEVELOPMENT:
        if context.is_secure_channel:
            return (True, None)
        # Dev team in public channels - limited access
        return (True, None)  # For now, allow but could restrict

    # In secure channels with lower access - shouldn't happen but handle it
    if context.is_secure_channel:
        logger.warning(
            "security.unauthorized_secure_channel",
            user=context.user_name,
            channel=context.channel_name
        )
        return (False, "This is a private channel. Please reach out to Otto in the general channels if you need assistance!")

    # Members and public in regular channels - redirect to Otto
    redirect_msg = (
        "Hi there! I'm Aurora, and I primarily work with the founder team. "
        "For general questions about Hello World Co-Op, Otto is your guide! "
        "You can find Otto in the main channels, or type `@Otto` for help. "
        "Otto knows all about the platform, Otter Camp, and how to get started!"
    )

    logger.info(
        "security.redirect_to_otto",
        user=context.user_name,
        channel=context.channel_name
    )

    return (False, redirect_msg)


def filter_response_for_context(response: str, context: SecurityContext) -> str:
    """
    Filter Aurora's response based on security context.
    Removes or redacts protected information for non-secure contexts.
    """
    if context.is_secure_channel and context.security_level in {SecurityLevel.FOUNDER, SecurityLevel.AGENT_TEAM}:
        # Full access in secure channels
        return response

    # Check for protected content and redact if necessary
    response_lower = response.lower()

    # Redact Sector7 references
    if "sector7" in response_lower or "sector 7" in response_lower:
        response = "[Content redacted - protected project reference]"
        logger.warning("security.content_redacted", reason="sector7_reference")

    return response
