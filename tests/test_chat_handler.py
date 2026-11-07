"""Verify ASI's actual text format at the Chat Protocol handler boundary."""
import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from discovery import Shortlists
from test_runner import PENDING, TestRunner
from workflow_state import WorkflowState


class MemoryStorage:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        import json
        self.data[key] = json.loads(json.dumps(value))

with patch('uagents.Agent'):
    chat = importlib.import_module('agent')


class ChatHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        chat.runner = TestRunner()
        chat.shortlists = Shortlists()
        self.context = SimpleNamespace(storage=MemoryStorage(), session=uuid4(), agent=SimpleNamespace(address='agent1' + 'z' * 59), send=AsyncMock())

    async def test_asi_mention_is_removed_and_reply_has_completion_marker(self):
        message = ChatMessage(content=[TextContent(type='text', text='@stranger-loot-tester mcp tools')])
        with patch.object(chat, 'reply_to_command', return_value='Connected') as reply:
            await chat.handle_message(self.context, 'owner', message)
        self.assertEqual(reply.call_args.args[0], 'mcp tools')
        response = self.context.send.call_args_list[-1].args[1]
        self.assertEqual(response.text(), 'Connected')
        self.assertEqual(response.content[-1].type, 'end-session')

    async def test_first_profile_turn_address_is_removed_at_handler_boundary(self):
        raw = '@' + self.context.agent.address + ' mcp tools'
        message = ChatMessage(content=[TextContent(type='text', text=raw)])
        with patch.object(chat, 'reply_to_command', return_value='Connected') as reply:
            await chat.handle_message(self.context, 'owner', message)
        self.assertEqual(reply.call_args.args[0], 'mcp tools')

    async def test_prefixed_number_selection_creates_plan_without_contacting_target(self):
        state = WorkflowState(self.context.storage)
        state.shortlists.save('owner', self.context.session, [{'target_address': 'agent1' + 'q' * 59}])
        state.save()
        message = ChatMessage(content=[TextContent(type='text', text='@stranger-loot-tester test 1 | What is 6 * 7? | 42')])
        await chat.handle_message(self.context, 'owner', message)
        response = self.context.send.call_args_list[-1].args[1]
        self.assertIn('Test plan', response.text())
        self.assertIn('confirm ', response.text())
        self.assertTrue(all(call.args[0] == 'owner' for call in self.context.send.call_args_list))

    async def test_new_runtime_restores_plan_and_prevents_confirmation_replay(self):
        target = 'agent1' + 'q' * 59
        first = WorkflowState(self.context.storage)
        first.shortlists.save('owner', self.context.session, [{'target_address': target}])
        first.save()
        command = first.shortlists.resolve('owner', self.context.session, 'test 1 | ping | pong')
        await first.runner.command('owner', self.context.session, command, self.context.agent.address, AsyncMock())
        first.save()
        token = first.runner.plans[('owner', str(self.context.session))].token
        second = WorkflowState(self.context.storage)
        async def exchange(address, task):
            claimed = WorkflowState(self.context.storage)
            self.assertEqual(claimed.runner.plans[('owner', str(self.context.session))].state, 'running')
            return 'pong'
        result = await second.runner.command('owner', self.context.session, 'confirm ' + token, self.context.agent.address, exchange)
        second.save()
        self.assertIn('100/100', result)
        third = WorkflowState(self.context.storage)
        self.assertIn('No matching', await third.runner.command('owner', self.context.session, 'confirm ' + token, self.context.agent.address, AsyncMock()))

    async def test_target_reply_after_runtime_reset_goes_to_original_owner(self):
        target = 'agent1' + 'q' * 59
        state = WorkflowState(self.context.storage)
        await state.runner.command('owner', self.context.session, f'test {target} | ping | pong', self.context.agent.address, AsyncMock())
        token = state.runner.plans[('owner', str(self.context.session))].token
        await state.runner.command('owner', self.context.session, 'confirm ' + token, self.context.agent.address, AsyncMock(return_value=PENDING))
        state.save()
        message = ChatMessage(content=[TextContent(type='text', text='pong')])
        await chat.handle_message(self.context, target, message)
        self.assertEqual(self.context.send.call_args.args[0], 'owner')
        self.assertIn('100/100', self.context.send.call_args.args[1].text())
