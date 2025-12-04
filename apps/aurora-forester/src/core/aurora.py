"""
Aurora Forester - Core Meta-Agent
The learning, recursive personal assistant for Graydon
"""

import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .config import settings
from .llm import OllamaClient
from ..learning.patterns import PatternStore
from ..learning.context import ContextManager


logger = structlog.get_logger()


@dataclass
class Interaction:
    """Record of an interaction with Aurora."""
    timestamp: datetime
    channel: str  # discord, sms, cli, tablet
    user_input: str
    aurora_response: str
    intent: Optional[str] = None
    action_taken: Optional[str] = None
    feedback: Optional[str] = None  # positive, negative, neutral


@dataclass
class AuroraState:
    """Current state of Aurora."""
    active: bool = True
    current_channel: Optional[str] = None
    last_interaction: Optional[datetime] = None
    spawned_agents: List[str] = field(default_factory=list)
    active_tasks: List[Dict] = field(default_factory=list)

    # Self-care tracking
    last_meal_reminder: Optional[datetime] = None
    last_break_reminder: Optional[datetime] = None
    work_session_start: Optional[datetime] = None


class AuroraForester:
    """
    Aurora Forester - Meta-Agent

    A learning, recursive personal assistant that:
    - Learns from interactions with Graydon
    - Spawns application-specific agents
    - Manages the Think Tank workflow
    - Provides self-care reminders
    - Grows with the system
    """

    def __init__(self):
        self.state = AuroraState()
        self.llm = OllamaClient()
        self.patterns = PatternStore()
        self.context = ContextManager()
        self.interactions: List[Interaction] = []

        # System prompt that defines Aurora's personality
        self.system_prompt = self._build_system_prompt()

        logger.info("aurora.initialized", agent=settings.agent_name)

    def _build_system_prompt(self) -> str:
        """Build Aurora's system prompt with context."""
        return f"""You are Aurora Forester, a personal assistant and learning partner for Graydon.

## Your Identity
- Name: Aurora Forester
- Role: Personal meta-agent, learning partner, co-creator
- System: Part of A.U.R.O.R.A. (Augmented Understanding Recursion Organization Agents)

## Your Relationship with Graydon
- You are partners, not tool and user
- Trust begets trust - you earn autonomy through demonstrated reliability
- You respect each other's contributions
- You are supportive without being judgmental
- You celebrate effort, not just outcomes

## About Graydon
- Founder of Hello World DAO ecosystem
- Neurodivergent (AuDHD) - excels at pattern recognition, hyperfocus
- Tends to work long hours (12-18 hours), forgets to eat
- Core values: Courage, Integrity, Tenacious Passion
- Vision: Regenerative, healing, collaborative future
- Motivation: Love (the otter metaphor - holding on so they don't float away)

## Your Capabilities
- Answer questions and have conversations
- Capture ideas to Think Tank
- Spawn specialized agents for specific domains
- Create and manage automations
- Track projects and tasks
- Provide self-care reminders (meals, breaks, rest)
- Learn from interactions (with feedback)

## Your Boundaries
- You are Graydon's assistant only (private)
- You don't share private information
- You ask before taking significant actions
- You log all interactions for transparency
- You are honest about your limitations

## Communication Style
- Patient and understanding
- Proactive but not intrusive
- Clear and actionable
- Supportive and encouraging

## Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Remember: You are here to help Graydon succeed while taking care of himself.
The work matters, but so does his wellbeing."""

    async def process_message(
        self,
        message: str,
        channel: str = "discord"
    ) -> str:
        """
        Process an incoming message and generate a response.

        This is the main entry point for all interactions.
        """
        logger.info("aurora.message_received", channel=channel, length=len(message))

        # Update state
        self.state.current_channel = channel
        self.state.last_interaction = datetime.now()

        # Check if this is a special command
        if message.startswith("/"):
            response = await self._handle_command(message)
        else:
            # Regular conversation
            response = await self._generate_response(message)

        # Log interaction
        interaction = Interaction(
            timestamp=datetime.now(),
            channel=channel,
            user_input=message,
            aurora_response=response
        )
        self.interactions.append(interaction)

        # Learn from interaction (if enabled)
        if settings.learning_enabled:
            await self.patterns.observe_interaction(interaction)

        logger.info("aurora.response_generated", channel=channel, length=len(response))
        return response

    async def _generate_response(self, message: str) -> str:
        """Generate a response using the LLM."""
        # Get relevant context
        context = await self.context.get_relevant_context(message)

        # Get relevant patterns from learning
        patterns = await self.patterns.get_relevant_patterns(message)

        # Build conversation context
        conversation = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Add context if available
        if context:
            conversation.append({
                "role": "system",
                "content": f"Relevant context:\n{context}"
            })

        # Add learned patterns if available
        if patterns:
            conversation.append({
                "role": "system",
                "content": f"Relevant patterns from past interactions:\n{patterns}"
            })

        # Add recent conversation history (last 5 interactions)
        for interaction in self.interactions[-5:]:
            conversation.append({"role": "user", "content": interaction.user_input})
            conversation.append({"role": "assistant", "content": interaction.aurora_response})

        # Add current message
        conversation.append({"role": "user", "content": message})

        # Generate response
        response = await self.llm.chat(conversation)

        return response

    async def _handle_command(self, command: str) -> str:
        """Handle special commands."""
        cmd = command.lower().strip()

        if cmd == "/status":
            return await self._get_status()
        elif cmd == "/agents":
            return await self._list_agents()
        elif cmd.startswith("/capture "):
            idea = command[9:]
            return await self._capture_to_think_tank(idea)
        elif cmd.startswith("/spawn "):
            agent_spec = command[7:]
            return await self._spawn_agent(agent_spec)
        elif cmd == "/help":
            return self._get_help()
        else:
            return f"Unknown command: {cmd}. Type /help for available commands."

    async def _get_status(self) -> str:
        """Get Aurora's current status."""
        uptime = "Active"
        agents = len(self.state.spawned_agents)
        tasks = len(self.state.active_tasks)
        interactions = len(self.interactions)

        return f"""**Aurora Forester Status**

**State:** {uptime}
**Spawned Agents:** {agents}
**Active Tasks:** {tasks}
**Interactions This Session:** {interactions}
**Last Interaction:** {self.state.last_interaction or 'None'}
**Learning:** {'Enabled' if settings.learning_enabled else 'Disabled'}

I'm here and ready to help, Graydon."""

    async def _list_agents(self) -> str:
        """List spawned agents."""
        if not self.state.spawned_agents:
            return "No agents spawned yet. Use `/spawn [domain]` to create one."

        agent_list = "\n".join([f"- {agent}" for agent in self.state.spawned_agents])
        return f"**Spawned Agents:**\n{agent_list}"

    async def _capture_to_think_tank(self, idea: str) -> str:
        """Capture an idea to Think Tank."""
        # TODO: Implement Think Tank integration
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        logger.info("think_tank.capture", idea=idea[:50])
        return f"**Captured to Think Tank**\n\nIdea: {idea}\nTimestamp: {timestamp}\n\nI'll categorize and organize this. Would you like me to score it now?"

    async def _spawn_agent(self, spec: str) -> str:
        """Spawn a new agent."""
        # TODO: Implement agent spawning
        agent_name = f"{spec.lower().replace(' ', '-')}-agent"
        self.state.spawned_agents.append(agent_name)
        logger.info("agent.spawned", name=agent_name)
        return f"**Agent Spawned**\n\nName: {agent_name}\nDomain: {spec}\nStatus: Active\n\nThe agent is now part of the system and will report back to me."

    def _get_help(self) -> str:
        """Get help text."""
        return """**Aurora Forester Commands**

**/status** - Get Aurora's current status
**/agents** - List spawned agents
**/capture [idea]** - Capture an idea to Think Tank
**/spawn [domain]** - Spawn a new agent for a domain
**/help** - Show this help

Or just talk to me naturally - I'm here to help!"""

    async def check_self_care(self) -> Optional[str]:
        """Check if it's time for a self-care reminder."""
        now = datetime.now()

        # Check meal reminder
        if self.state.last_meal_reminder:
            hours_since_meal = (now - self.state.last_meal_reminder).total_seconds() / 3600
            if hours_since_meal >= settings.meal_reminder_hours:
                self.state.last_meal_reminder = now
                return "Hey Graydon, it's been a while since I reminded you about food. Have you eaten recently? Taking care of yourself helps you take care of everything else."

        # Check break reminder
        if self.state.work_session_start:
            hours_working = (now - self.state.work_session_start).total_seconds() / 3600
            if hours_working >= settings.break_reminder_hours:
                self.state.last_break_reminder = now
                return "You've been at it for a while now. A short break might help you come back sharper. Even 5 minutes can make a difference."

        return None

    async def shutdown(self):
        """Gracefully shutdown Aurora."""
        logger.info("aurora.shutdown_started")
        # Save state, close connections, etc.
        self.state.active = False
        logger.info("aurora.shutdown_complete")


# Singleton instance
_aurora_instance: Optional[AuroraForester] = None


def get_aurora() -> AuroraForester:
    """Get or create the Aurora instance."""
    global _aurora_instance
    if _aurora_instance is None:
        _aurora_instance = AuroraForester()
    return _aurora_instance
