import unittest
from unittest.mock import patch
from mcp_client import StrangerLootMCP
from test_runner import agent_address

ADDRESS = 'agent1' + 'q' * 59


class DiscoveryTests(unittest.TestCase):
    def test_only_agent_links_are_discovered_and_coverage_is_shown(self):
        result = {'structuredContent': {'records': [{'snapshot': {'gallery': {'data': {
            'as_of': '2026-11-07', 'total': 121, 'items': [
                {'name': 'Website', 'public_url': 'https://example.com', 'sponsors': ['fetch_ai']},
                {'name': 'Chat Agent', 'one_liner': 'Answers questions', 'public_url': 'https://asi1.ai/ai/' + ADDRESS},
            ]}}}}]}}
        with patch.object(StrangerLootMCP, 'connect', return_value={'query_publiccatalogue': {}}), patch.object(StrangerLootMCP, 'request', return_value=result):
            reply = StrangerLootMCP().projects()
        self.assertIn('Chat Agent', reply)
        self.assertIn(ADDRESS, reply)
        self.assertNotIn('Website:', reply)
        self.assertIn('2 of 121', reply)

    def test_website_and_lookalike_hosts_are_not_agent_targets(self):
        self.assertIsNone(agent_address('https://example.com/' + ADDRESS))
        self.assertIsNone(agent_address('https://asi1.ai.evil.test/ai/' + ADDRESS))
        self.assertEqual(agent_address('https://agentverse.ai/agents/details/' + ADDRESS + '/profile'), ADDRESS)
