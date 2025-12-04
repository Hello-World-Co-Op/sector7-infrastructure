"""
Otto Discord Bot
Public platform guide for Hello World Co-Op

Otto responds to:
- Direct mentions (@Otto)
- Messages in designated help channels
- DMs from community members
"""

import discord
from discord.ext import commands
import structlog
from datetime import datetime
from typing import Optional

from ..core.config import settings, load_secrets
from ..core.otto import get_otto, Otto


logger = structlog.get_logger()


# Channels where Otto actively responds
HELP_CHANNELS = {
    "help", "support", "questions", "general", "welcome",
    "getting-started", "newcomers", "otter-camp", "onboarding"
}

# Channels Otto should NOT respond in (Aurora's territory)
PRIVATE_CHANNELS = {
    "aurora-forester", "aurora", "founder-private", "founders",
    "development", "dev-team", "sector7"
}


class OttoBot(commands.Bot):
    """
    Otto - Platform Guide Discord Bot

    A public-facing bot that helps community members
    navigate the Hello World Co-Op ecosystem.
    """

    def __init__(self):
        load_secrets()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="!otto ",
            intents=intents,
            description="Otto - Your friendly platform guide!"
        )

        self.otto: Optional[Otto] = None
        logger.info("otto_bot.initialized")

    async def setup_hook(self):
        """Called when the bot is starting up."""
        self.otto = get_otto()
        logger.info("otto_bot.setup_complete")

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(
            "otto_bot.ready",
            user=str(self.user),
            guilds=len(self.guilds)
        )

        # Set playful status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="in Otter Camp | @Otto for help!"
            )
        )

    async def on_message(self, message: discord.Message):
        """Handle incoming messages."""
        # Ignore own messages
        if message.author == self.user:
            return

        # Ignore bots
        if message.author.bot:
            return

        # Get channel name
        channel_name = getattr(message.channel, 'name', 'DM').lower()

        # Never respond in private channels (Aurora's territory)
        if channel_name in PRIVATE_CHANNELS:
            return

        # Determine if Otto should respond
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.user in message.mentions
        is_help_channel = channel_name in HELP_CHANNELS
        is_reply = (
            message.reference and
            message.reference.resolved and
            message.reference.resolved.author == self.user
        )

        should_respond = is_dm or is_mention or is_reply

        # In help channels, respond to questions even without mention
        if is_help_channel and not should_respond:
            # Check if it looks like a question
            content_lower = message.content.lower()
            question_indicators = ["?", "how do", "what is", "where", "help", "explain"]
            if any(q in content_lower for q in question_indicators):
                should_respond = True

        if not should_respond:
            return

        # Clean the message content
        content = message.content
        for mention in message.mentions:
            content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
        content = content.strip()

        if not content:
            # Just mentioned with no content
            await message.reply(
                "Hey there! I'm Otto, your friendly platform guide! "
                "Ask me anything about Hello World Co-Op, Otter Camp, "
                "or how to get started! Click here, click there - boom!"
            )
            return

        logger.info(
            "otto_bot.message_received",
            user=str(message.author),
            channel=channel_name,
            content_length=len(content)
        )

        # Show typing indicator
        async with message.channel.typing():
            try:
                # Process with Otto
                user_name = message.author.display_name
                response = await self.otto.process_message(content, user_name)

                # Send response (split if too long)
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)

            except Exception as e:
                logger.error("otto_bot.message_error", error=str(e))
                await message.reply(
                    "Oops! Got a bit tangled in my whiskers there. "
                    "Try again in a moment!"
                )

    async def close(self):
        """Cleanup when shutting down."""
        await super().close()
        logger.info("otto_bot.closed")


def run_bot():
    """Entry point for running the Otto Discord bot."""
    load_secrets()

    if not settings.discord_token:
        logger.error("otto_bot.no_token", message="DISCORD_BOT_TOKEN not set")
        print("Error: DISCORD_BOT_TOKEN not set")
        return

    bot = OttoBot()

    try:
        bot.run(settings.discord_token)
    except discord.LoginFailure:
        logger.error("otto_bot.login_failed", message="Invalid token")
        print("Error: Invalid Discord bot token")
    except Exception as e:
        logger.error("otto_bot.error", error=str(e))
        print(f"Error: {e}")


if __name__ == "__main__":
    run_bot()
