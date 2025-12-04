#!/usr/bin/env python3
"""
Aurora Forester - Main Entry Point

Personal assistant meta-agent for Graydon.
"""

import sys
import asyncio
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Aurora Forester - Personal Assistant")
        print("")
        print("Usage:")
        print("  python main.py bot      - Run Discord bot")
        print("  python main.py cli      - Run CLI interface")
        print("  python main.py test     - Run test conversation")
        return

    command = sys.argv[1].lower()

    if command == "bot":
        run_discord_bot()
    elif command == "cli":
        run_cli()
    elif command == "test":
        run_test()
    else:
        print(f"Unknown command: {command}")


def run_discord_bot():
    """Run the Discord bot."""
    logger.info("aurora.starting", mode="discord_bot")
    from src.bot.discord_bot import run_bot
    run_bot()


def run_cli():
    """Run CLI interface for testing."""
    logger.info("aurora.starting", mode="cli")
    asyncio.run(cli_loop())


async def cli_loop():
    """Interactive CLI loop."""
    from src.core.aurora import get_aurora
    from src.core.config import load_secrets

    load_secrets()
    aurora = get_aurora()

    print("\n" + "="*60)
    print("Aurora Forester - CLI Interface")
    print("="*60)
    print("\nHello Graydon! I'm Aurora, your personal assistant.")
    print("Type 'quit' to exit, '/help' for commands.\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("\nAurora: Take care, Graydon. Remember to rest well.")
                break

            response = await aurora.process_message(user_input, channel="cli")
            print(f"\nAurora: {response}\n")

        except KeyboardInterrupt:
            print("\n\nAurora: Goodbye, Graydon!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def run_test():
    """Run a test conversation."""
    logger.info("aurora.starting", mode="test")
    asyncio.run(test_conversation())


async def test_conversation():
    """Test Aurora with a few interactions."""
    from src.core.aurora import get_aurora
    from src.core.config import load_secrets
    from src.core.llm import OllamaClient

    load_secrets()

    print("\n" + "="*60)
    print("Aurora Forester - Test Mode")
    print("="*60)

    # Test Ollama connection
    print("\n1. Testing Ollama connection...")
    llm = OllamaClient()
    if await llm.check_health():
        print("   Ollama: Connected")
        models = await llm.list_models()
        print(f"   Available models: {', '.join(models)}")
    else:
        print("   Ollama: NOT CONNECTED - check if Ollama is running")
        return

    # Test Aurora
    print("\n2. Testing Aurora responses...")
    aurora = get_aurora()

    test_messages = [
        "Hello Aurora, are you there?",
        "/status",
        "What can you help me with?",
    ]

    for msg in test_messages:
        print(f"\n   You: {msg}")
        response = await aurora.process_message(msg, channel="test")
        # Truncate long responses for display
        if len(response) > 200:
            response = response[:200] + "..."
        print(f"   Aurora: {response}")

    print("\n" + "="*60)
    print("Test complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
