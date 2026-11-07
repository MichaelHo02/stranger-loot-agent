import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from mcp_client import reply_to_command
from discovery import normalize_user_text
from workflow_state import WorkflowState
from test_runner import PENDING


agent = Agent()

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    # Acknowledge the incoming message first
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id),
    )

    state = WorkflowState(ctx.storage)
    runner = state.runner
    shortlists = state.shortlists
    if runner.duplicate(sender, msg.msg_id):
        return
    if runner.is_target_reply(sender, ctx.session):
        result = runner.receive(sender, ctx.session, msg.text() or "")
        state.save()
        if result:
            owner, report = result
            await ctx.send(owner, ChatMessage(
                timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                content=[TextContent(type="text", text=report), EndSessionContent(type="end-session")]))
        return

    text = normalize_user_text(msg.text() or "", own_address=ctx.agent.address)
    if not text:
        return

    if len(text) > 1400:
        text = "help"

    async def exchange(target, task):
        status = await ctx.send(
            target,
            ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                        content=[TextContent(type="text", text=task)]),
        )
        if getattr(status, "status", None) == "failed":
            return None
        return PENDING

    try:
        try:
            resolved = shortlists.resolve(sender, ctx.session, text)
        except ValueError as error:
            resolved = None
            reply = str(error)
        if resolved is not None:
            reply = await runner.command(sender, ctx.session, resolved, ctx.agent.address, exchange,
                                         candidate=shortlists.candidate(sender, ctx.session, resolved[5:].split('|')[0].strip())
                                         if resolved.lower().startswith('test ') else None)
        if reply is None:
            reply = await asyncio.to_thread(reply_to_command, text, shortlists, sender, ctx.session)
    except Exception:
        reply = "Stranger Loot MCP is unavailable right now. Please try again later."
    state.save()
    content = [TextContent(type="text", text=reply), EndSessionContent(type="end-session")]
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
