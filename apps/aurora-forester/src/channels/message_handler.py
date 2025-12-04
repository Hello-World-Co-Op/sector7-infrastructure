"""
Aurora Forester - Multi-Channel Message Handler
Unified message handling across Discord, SMS, Tablet, Webhook, and Terminal.
"""

from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import asyncio

from ..core.aurora_graph import get_aurora, Message


class Channel(Enum):
    """Supported communication channels."""
    DISCORD = "discord"
    SMS = "sms"
    TABLET = "tablet"
    WEBHOOK = "webhook"
    TERMINAL = "terminal"


@dataclass
class IncomingMessage:
    """A message from any channel."""
    channel: Channel
    content: str
    user_id: str
    channel_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
        if self.session_id is None:
            self.session_id = f"{self.channel.value}_{self.user_id}_{datetime.now().strftime('%Y%m%d')}"


@dataclass
class OutgoingMessage:
    """A message to send back via a channel."""
    channel: Channel
    content: str
    recipient_id: str
    channel_id: Optional[str] = None
    metadata: Dict[str, Any] = None


# Type for channel adapters
ChannelAdapter = Callable[[OutgoingMessage], Awaitable[bool]]


class MessageRouter:
    """
    Routes messages between channels and Aurora.
    Central hub for all communication.
    """

    def __init__(self):
        self.aurora = get_aurora()
        self.adapters: Dict[Channel, ChannelAdapter] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def register_adapter(self, channel: Channel, adapter: ChannelAdapter):
        """Register an adapter for a channel."""
        self.adapters[channel] = adapter

    async def handle_incoming(self, message: IncomingMessage) -> OutgoingMessage:
        """
        Handle an incoming message from any channel.
        Returns the response to send back.
        """
        # Process through Aurora
        response = await self.aurora.process_message(
            message=message.content,
            channel=message.channel.value,
            session_id=message.session_id,
            user_id=message.user_id
        )

        return OutgoingMessage(
            channel=message.channel,
            content=response,
            recipient_id=message.user_id,
            channel_id=message.channel_id,
            metadata={"in_response_to": message.content[:50]}
        )

    async def send_response(self, message: OutgoingMessage) -> bool:
        """Send a response through the appropriate channel adapter."""
        adapter = self.adapters.get(message.channel)
        if adapter is None:
            print(f"No adapter registered for channel: {message.channel}")
            return False

        try:
            return await adapter(message)
        except Exception as e:
            print(f"Error sending message via {message.channel}: {e}")
            return False

    async def process_and_respond(self, message: IncomingMessage) -> bool:
        """Full pipeline: receive, process, respond."""
        response = await self.handle_incoming(message)
        return await self.send_response(response)

    async def start_queue_processor(self):
        """Start processing the message queue."""
        self._running = True
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self.process_and_respond(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Queue processor error: {e}")

    def stop(self):
        """Stop the queue processor."""
        self._running = False


# ============================================
# CHANNEL ADAPTERS
# ============================================

class DiscordAdapter:
    """Adapter for Discord messages."""

    def __init__(self, bot_client=None):
        self.client = bot_client

    async def send(self, message: OutgoingMessage) -> bool:
        """Send a message via Discord."""
        if self.client is None:
            print(f"Discord: {message.content}")
            return True

        # In production: use discord.py client to send
        # channel = self.client.get_channel(int(message.channel_id))
        # await channel.send(message.content)
        return True

    def create_adapter(self) -> ChannelAdapter:
        """Create the adapter function."""
        return self.send


class SMSAdapter:
    """Adapter for SMS messages via Twilio or similar."""

    def __init__(self, twilio_client=None):
        self.client = twilio_client

    async def send(self, message: OutgoingMessage) -> bool:
        """Send a message via SMS."""
        if self.client is None:
            print(f"SMS to {message.recipient_id}: {message.content}")
            return True

        # In production: use Twilio client
        # self.client.messages.create(
        #     body=message.content,
        #     from_=AURORA_PHONE_NUMBER,
        #     to=message.recipient_id
        # )
        return True

    def create_adapter(self) -> ChannelAdapter:
        return self.send


class TabletAdapter:
    """Adapter for Tablet PWA via WebSocket."""

    def __init__(self, websocket_server=None):
        self.server = websocket_server
        self.connections: Dict[str, Any] = {}

    async def send(self, message: OutgoingMessage) -> bool:
        """Send a message via WebSocket to tablet."""
        connection = self.connections.get(message.recipient_id)
        if connection is None:
            print(f"Tablet (no connection): {message.content}")
            return False

        # In production: send via WebSocket
        # await connection.send(json.dumps({
        #     "type": "message",
        #     "content": message.content,
        #     "timestamp": datetime.now().isoformat()
        # }))
        return True

    def create_adapter(self) -> ChannelAdapter:
        return self.send


class TerminalAdapter:
    """Adapter for terminal/CLI output."""

    async def send(self, message: OutgoingMessage) -> bool:
        """Output to terminal."""
        print(f"\n🌲 Aurora: {message.content}\n")
        return True

    def create_adapter(self) -> ChannelAdapter:
        return self.send


# ============================================
# WEBHOOK HANDLERS
# ============================================

class WebhookHandler:
    """
    Handle incoming webhooks from n8n and other sources.
    Provides REST API endpoints for message processing.
    """

    def __init__(self, router: MessageRouter):
        self.router = router
        self.webhook_secret: Optional[str] = None

    def set_secret(self, secret: str):
        """Set the webhook verification secret."""
        self.webhook_secret = secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC signature of webhook payload."""
        if self.webhook_secret is None:
            return True  # No verification configured

        import hmac
        import hashlib

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def handle_discord_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Discord webhook from n8n."""
        message = IncomingMessage(
            channel=Channel.DISCORD,
            content=data.get("content", ""),
            user_id=data.get("user_id", "unknown"),
            channel_id=data.get("channel_id"),
            metadata=data.get("metadata", {})
        )

        response = await self.router.handle_incoming(message)

        return {
            "success": True,
            "response": response.content,
            "channel_id": response.channel_id
        }

    async def handle_sms_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SMS webhook from Twilio via n8n."""
        message = IncomingMessage(
            channel=Channel.SMS,
            content=data.get("Body", ""),
            user_id=data.get("From", "unknown"),
            metadata={
                "message_sid": data.get("MessageSid"),
                "account_sid": data.get("AccountSid")
            }
        )

        response = await self.router.handle_incoming(message)

        return {
            "success": True,
            "response": response.content,
            "recipient": response.recipient_id
        }

    async def handle_tablet_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Tablet app webhook."""
        message = IncomingMessage(
            channel=Channel.TABLET,
            content=data.get("message", ""),
            user_id=data.get("user_id", "founder"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {})
        )

        response = await self.router.handle_incoming(message)

        return {
            "success": True,
            "response": response.content,
            "session_id": message.session_id
        }

    async def handle_generic_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic API webhook."""
        message = IncomingMessage(
            channel=Channel.WEBHOOK,
            content=data.get("message", ""),
            user_id=data.get("user_id", "api"),
            metadata=data
        )

        response = await self.router.handle_incoming(message)

        return {
            "success": True,
            "response": response.content
        }


# ============================================
# N8N WORKFLOW DEFINITIONS
# ============================================

N8N_WEBHOOK_CONFIGS = {
    "discord": {
        "path": "/webhook/aurora/discord",
        "method": "POST",
        "auth": "header",
        "description": "Receive Discord messages for Aurora processing"
    },
    "sms": {
        "path": "/webhook/aurora/sms",
        "method": "POST",
        "auth": "header",
        "description": "Receive SMS via Twilio webhook"
    },
    "tablet": {
        "path": "/webhook/aurora/tablet",
        "method": "POST",
        "auth": "bearer",
        "description": "Receive tablet PWA messages"
    },
    "scheduled": {
        "path": "/webhook/aurora/scheduled",
        "method": "POST",
        "auth": "header",
        "description": "Handle scheduled workflow triggers"
    }
}


def generate_n8n_workflow_template(webhook_type: str) -> Dict[str, Any]:
    """
    Generate an n8n workflow template for Aurora integration.
    """
    config = N8N_WEBHOOK_CONFIGS.get(webhook_type, N8N_WEBHOOK_CONFIGS["discord"])

    return {
        "name": f"Aurora - {webhook_type.title()} Handler",
        "nodes": [
            {
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "parameters": {
                    "path": config["path"],
                    "httpMethod": config["method"],
                    "authentication": config["auth"]
                }
            },
            {
                "name": "Aurora Processor",
                "type": "n8n-nodes-base.httpRequest",
                "parameters": {
                    "url": "http://aurora-api.aurora-system.svc.cluster.local:8000/process",
                    "method": "POST",
                    "bodyParametersJson": "={{ JSON.stringify($json) }}"
                }
            },
            {
                "name": "Response Router",
                "type": "n8n-nodes-base.switch",
                "parameters": {
                    "conditions": {
                        "string": [
                            {
                                "value1": "={{ $json.channel }}",
                                "operation": "equals",
                                "value2": webhook_type
                            }
                        ]
                    }
                }
            }
        ],
        "connections": {
            "Webhook": {
                "main": [[{"node": "Aurora Processor"}]]
            },
            "Aurora Processor": {
                "main": [[{"node": "Response Router"}]]
            }
        }
    }


# ============================================
# INITIALIZATION
# ============================================

_router: Optional[MessageRouter] = None


def get_router() -> MessageRouter:
    """Get the singleton message router."""
    global _router
    if _router is None:
        _router = MessageRouter()

        # Register default adapters
        _router.register_adapter(Channel.TERMINAL, TerminalAdapter().create_adapter())
        _router.register_adapter(Channel.DISCORD, DiscordAdapter().create_adapter())
        _router.register_adapter(Channel.SMS, SMSAdapter().create_adapter())
        _router.register_adapter(Channel.TABLET, TabletAdapter().create_adapter())

    return _router


def get_webhook_handler() -> WebhookHandler:
    """Get a webhook handler instance."""
    return WebhookHandler(get_router())
