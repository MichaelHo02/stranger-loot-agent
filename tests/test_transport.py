"""Exercise real uAgents correlation without external agents or network."""
import unittest
from datetime import datetime, timezone
from uuid import uuid4
from uagents.dispatch import Dispatcher
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, TextContent


class ChatCorrelationTests(unittest.IsolatedAsyncioTestCase):
    async def test_ack_wrong_sender_and_wrong_session_do_not_satisfy_test(self):
        dispatcher = Dispatcher()
        session = uuid4()
        digest = ChatMessage.build_schema_digest(ChatMessage)
        await dispatcher.register_pending_response('tester', 'target', session, {digest})
        ack = ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=uuid4())
        self.assertFalse(dispatcher.dispatch_pending_response('target', 'tester', session,
                         ChatAcknowledgement.build_schema_digest(ChatAcknowledgement), ack.model_dump_json()))
        reply = ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type='text', text='42')])
        self.assertFalse(dispatcher.dispatch_pending_response('intruder', 'tester', session, digest, reply.model_dump_json()))
        self.assertFalse(dispatcher.dispatch_pending_response('target', 'tester', uuid4(), digest, reply.model_dump_json()))
        self.assertTrue(dispatcher.dispatch_pending_response('target', 'tester', session, digest, reply.model_dump_json()))
        received = await dispatcher.wait_for_response('tester', 'target', session, 1)
        self.assertEqual(ChatMessage.model_validate_json(received.message).text(), '42')
        self.assertEqual(dispatcher.pending_responses, {})

    async def test_transport_timeout_cleans_pending_response(self):
        dispatcher = Dispatcher()
        session = uuid4()
        await dispatcher.register_pending_response('tester', 'target', session, {ChatMessage.build_schema_digest(ChatMessage)})
        self.assertIsNone(await dispatcher.wait_for_response('tester', 'target', session, 0.001))
        self.assertEqual(dispatcher.pending_responses, {})
