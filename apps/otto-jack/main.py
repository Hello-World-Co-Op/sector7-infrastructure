#!/usr/bin/env python3
"""
Otto - Platform Guide for Hello World Co-Op

"Click here, click there - boom! You're an otter wizard now."

Usage:
    python main.py bot     # Run Discord bot
    python main.py --help  # Show help
"""

import sys
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable commands:")
        print("  bot    - Run the Discord bot")
        sys.exit(1)

    command = sys.argv[1]

    if command == "bot":
        from src.bot.discord_bot import run_bot
        run_bot()
    elif command == "--help":
        print(__doc__)
    else:
        print(f"Unknown command: {command}")
        print("Use 'python main.py --help' for available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
