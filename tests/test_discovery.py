import unittest
from unittest.mock import patch
from discovery import Shortlists, rank_projects, search_description
from mcp_client import StrangerLootMCP, reply_to_command
from test_runner import agent_address

ADDRESS = 'agent1' + 'q' * 59


class DiscoveryTests(unittest.TestCase):
    def test_only_public_agent_entries_are_discovered(self):
        result = {'structuredContent': {'records': [{'snapshot': {
            'lastSync': {'at': '2026-11-07'}, 'total': 207, 'free': [
                {'name': 'Website', 'public_url': 'https://example.com', 'sponsors': ['fetch_ai']},
                {'name': 'Nail Agent', 'one_liner': 'Books a manicure appointment', 'public_url': 'https://asi1.ai/ai/' + ADDRESS},
            ], 'rest': [{'name': 'Locked Agent', 'public_url': 'https://asi1.ai/ai/' + ADDRESS}]
        }}]}}
        with patch.object(StrangerLootMCP, 'connect', return_value={'query_publiccatalogue': {}}), patch.object(StrangerLootMCP, 'request', return_value=result) as request:
            reply, matches = StrangerLootMCP().discover('find a nail appointment agent')
        self.assertIn('1. Nail Agent', reply)
        self.assertEqual(matches[0]['target_address'], ADDRESS)
        self.assertNotIn('Website:', reply)
        self.assertNotIn('Locked Agent', reply)
        self.assertIn('2 detailed public', reply)
        self.assertIn('207 total indexed', reply)
        self.assertEqual(request.call_args.args[1]['arguments']['query'], {'key': 'current'})

    def test_website_and_lookalike_hosts_are_not_agent_targets(self):
        self.assertIsNone(agent_address('https://example.com/' + ADDRESS))
        self.assertIsNone(agent_address('https://asi1.ai.evil.test/ai/' + ADDRESS))
        self.assertEqual(agent_address('https://agentverse.ai/agents/details/' + ADDRESS + '/profile'), ADDRESS)

    def test_related_terms_and_typos_match_description_not_exact_name(self):
        items = [{'name': 'Pretty Hands', 'one_liner': 'Book a manicure'},
                 {'name': 'Finance Buddy', 'one_liner': 'Manage your budget'}]
        self.assertEqual(rank_projects(items, 'find me a nail appointment agent'), items[:1])
        self.assertEqual(rank_projects(items, 'manicur'), items[:1])
        self.assertEqual(rank_projects(items, 'an agent that helps with my money'), items[1:])
        self.assertEqual(rank_projects(items, 'travel'), [])

    def test_full_request_is_routed_to_mcp_and_no_match_is_not_fabricated(self):
        lists = Shortlists()
        with patch.object(StrangerLootMCP, 'discover', return_value=('No matches', [])) as discover:
            result = reply_to_command('can you find a nail agent', lists, 'owner', 'chat')
        discover.assert_called_once()
        self.assertEqual(result, 'No matches')
        self.assertEqual(lists.results[('owner', 'chat')][1], [])
        self.assertIsNone(search_description('help'))
        self.assertIsNone(search_description('confirm 123'))

    def test_shortlist_isolation_expiry_and_exact_resolution(self):
        now = [0]
        lists = Shortlists(clock=lambda: now[0])
        lists.save('owner', 'chat', [{'target_address': ADDRESS}])
        command = lists.resolve('owner', 'chat', 'test 1 | task | expected')
        self.assertEqual(command, f'test {ADDRESS} | task | expected')
        for owner, session in [('other', 'chat'), ('owner', 'other')]:
            with self.assertRaises(ValueError):
                lists.resolve(owner, session, 'test 1 | task | expected')
        now[0] = 300
        with self.assertRaises(ValueError):
            lists.resolve('owner', 'chat', 'test 1 | task | expected')

    def test_no_invented_address_for_asi_handle(self):
        lists = Shortlists()
        lists.save('owner', 'chat', [{'agent_link': 'https://asi1.ai/ai/nail-helper', 'target_address': None}])
        with self.assertRaisesRegex(ValueError, 'no published agent address'):
            lists.resolve('owner', 'chat', 'test 1 | task | expected')
        with self.assertRaises(ValueError):
            lists.resolve('owner', 'chat', 'test 2 | task | expected')
        self.assertEqual(lists.resolve('owner', 'chat', f'test {ADDRESS} | task | expected'), f'test {ADDRESS} | task | expected')
