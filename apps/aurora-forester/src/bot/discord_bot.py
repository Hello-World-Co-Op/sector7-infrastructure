"""
Aurora Forester - Discord Bot
Primary interface for Graydon to interact with Aurora

Security Model:
- Founder role + aurora-forester channel = full access
- Development team = limited access
- Others = redirect to Otto
- Sector7 = never discussed outside secure channels
"""

import discord
from discord.ext import commands, tasks
import structlog
import asyncio
from datetime import datetime
from typing import Optional

from ..core.config import settings, load_secrets
from ..core.aurora import get_aurora, AuroraForester
from ..core.security import (
    create_security_context,
    should_aurora_respond,
    filter_response_for_context,
    check_protected_content,
    SecurityLevel,
)


logger = structlog.get_logger()


class AuroraBot(commands.Bot):
    """
    Aurora Forester Discord Bot

    A private bot for Graydon to interact with Aurora.
    Runs in a specific channel and responds to messages.
    """

    def __init__(self):
        # Load secrets first
        load_secrets()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="/aurora ",
            intents=intents,
            description="Aurora Forester - Personal Assistant for Graydon"
        )

        self.aurora: Optional[AuroraForester] = None
        self.allowed_channel_id: Optional[int] = settings.discord_channel_id

        logger.info("discord_bot.initialized")

    async def setup_hook(self):
        """Called when the bot is starting up."""
        # Initialize Aurora
        self.aurora = get_aurora()

        # Start background tasks
        self.self_care_check.start()

        logger.info("discord_bot.setup_complete")

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(
            "discord_bot.ready",
            user=str(self.user),
            guilds=len(self.guilds)
        )

        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="Graydon"
            )
        )

        # Send startup message to channel if configured
        if self.allowed_channel_id:
            channel = self.get_channel(self.allowed_channel_id)
            if channel:
                await channel.send(
                    "**Aurora Forester Online**\n\n"
                    "I'm here and ready to help, Graydon. "
                    "Type `/status` to see my current state, or just talk to me.\n\n"
                    f"*Started at {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
                )

    async def on_message(self, message: discord.Message):
        """Handle incoming messages with security model."""
        # Ignore own messages
        if message.author == self.user:
            return

        # Check if it's a DM or mentions the bot or is in allowed channel
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.user in message.mentions
        is_reply = message.reference and message.reference.resolved and message.reference.resolved.author == self.user
        is_allowed_channel = self.allowed_channel_id and message.channel.id == self.allowed_channel_id

        # Determine if we should even consider responding
        should_consider = is_dm or is_mention or is_reply or is_allowed_channel

        if not should_consider:
            return

        # Create security context
        security_context = create_security_context(message)

        logger.info(
            "discord_bot.message_received",
            user=security_context.user_name,
            channel=security_context.channel_name,
            security_level=security_context.security_level.value,
            is_secure=security_context.is_secure_channel
        )

        # Check if Aurora should respond or redirect to Otto
        can_respond, redirect_message = should_aurora_respond(security_context)

        if not can_respond:
            # Redirect to Otto
            await message.reply(redirect_message)
            return

        # Clean the message content (remove mentions)
        content = message.content
        for mention in message.mentions:
            content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
        content = content.strip()

        if not content:
            return

        # Check for protected content in non-secure channels
        if not security_context.is_secure_channel:
            protected_response = check_protected_content(content)
            if protected_response:
                await message.reply(protected_response)
                logger.warning(
                    "discord_bot.protected_topic_blocked",
                    user=security_context.user_name,
                    channel=security_context.channel_name
                )
                return

        # Show typing indicator
        async with message.channel.typing():
            try:
                # Process with Aurora
                response = await self.aurora.process_message(content, channel="discord")

                # Filter response based on security context
                response = filter_response_for_context(response, security_context)

                # Send response (split if too long)
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    # Split into chunks
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)

            except Exception as e:
                logger.error("discord_bot.message_error", error=str(e))
                await message.reply(
                    "I encountered an error processing that. "
                    "Let me know if you'd like me to try again."
                )

    @tasks.loop(minutes=30)
    async def self_care_check(self):
        """Periodic self-care check."""
        if not self.aurora or not self.allowed_channel_id:
            return

        try:
            reminder = await self.aurora.check_self_care()
            if reminder:
                channel = self.get_channel(self.allowed_channel_id)
                if channel:
                    await channel.send(reminder)
        except Exception as e:
            logger.error("discord_bot.self_care_error", error=str(e))

    @self_care_check.before_loop
    async def before_self_care_check(self):
        """Wait for bot to be ready before starting self-care checks."""
        await self.wait_until_ready()

    async def close(self):
        """Cleanup when shutting down."""
        self.self_care_check.cancel()
        if self.aurora:
            await self.aurora.shutdown()
        await super().close()
        logger.info("discord_bot.closed")


def run_bot():
    """Entry point for running the Discord bot."""
    load_secrets()

    if not settings.discord_token:
        logger.error("discord_bot.no_token", message="DISCORD_BOT_TOKEN not set")
        print("Error: DISCORD_BOT_TOKEN not set (check environment variables or secrets.env)")
        return

    bot = AuroraBot()

    try:
        bot.run(settings.discord_token)
    except discord.LoginFailure:
        logger.error("discord_bot.login_failed", message="Invalid token")
        print("Error: Invalid Discord bot token")
    except Exception as e:
        logger.error("discord_bot.error", error=str(e))
        print(f"Error: {e}")


if __name__ == "__main__":
    run_bot()
