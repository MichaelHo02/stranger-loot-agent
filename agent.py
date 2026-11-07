import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from mcp_client import reply_to_command
from test_runner import TestRunner

runner = TestRunner()

agent = Agent()

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # Acknowledge the incoming message first
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    if runner.duplicate(sender, msg.msg_id) or runner.is_target_reply(sender, ctx.session):
        return

    text = msg.text()
    if not text:
        return

    if len(text) > 1400:
        text = "help"

    async def exchange(target, task):
        response, status = await ctx.send_and_receive(
            target,
            ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                        content=[TextContent(type="text", text=task)]),
            response_type=ChatMessage,
            timeout=60,
        )
        if response is None:
            return None
        await ctx.send(target, ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc), acknowledged_msg_id=response.msg_id))
        return response.text()

    try:
        reply = await runner.command(sender, ctx.session, text, ctx.agent.address, exchange)
        if reply is None:
            reply = await asyncio.to_thread(reply_to_command, text)
    except Exception:
        reply = "Stranger Loot MCP is unavailable right now. Please try again later."
    content = [TextContent(type="text", text=reply)]
    await ctx.send(
        sender,
        ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=content),
    )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
