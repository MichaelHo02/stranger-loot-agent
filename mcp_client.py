"""Small, bounded client for Stranger Loot's public Streamable HTTP MCP."""
import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from test_runner import agent_address

DEFAULT_URL = 'https://stranger-loot.base44.app/api/mcp'
MAX_BYTES = 4 * 1024 * 1024


class MCPError(Exception):
    pass


class StrangerLootMCP:
    def __init__(self):
        self.url = os.environ.get('STRANGER_LOOT_MCP_URL', DEFAULT_URL)
        if urlparse(self.url).scheme != 'https':
            raise MCPError('MCP URL must use HTTPS.')
        self.session = None
        self.version = '2025-03-26'
        self.counter = 0

    def request(self, method, params=None, notification=False):
        self.counter += 1
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notification:
            payload['id'] = self.counter
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
                   'MCP-Protocol-Version': self.version}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        req = Request(self.url, data=json.dumps(payload).encode(), headers=headers)
        with urlopen(req, timeout=15) as response:
            self.session = response.headers.get('Mcp-Session-Id', self.session)
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise MCPError('MCP response exceeded the size limit.')
        if notification:
            return {}
        body = raw.decode('utf-8')
        if body.lstrip().startswith('{'):
            messages = [json.loads(body)]
        else:
            messages = []
            for event in body.replace('\r\n', '\n').split('\n\n'):
                data = '\n'.join(line[5:].lstrip() for line in event.splitlines() if line.startswith('data:'))
                if data:
                    messages.append(json.loads(data))
        for message in messages:
            if message.get('id') == payload['id']:
                if 'error' in message:
                    raise MCPError('MCP request was rejected.')
                return message['result']
        raise MCPError('MCP returned no matching response.')

    def connect(self):
        result = self.request('initialize', {'protocolVersion': self.version, 'capabilities': {},
                              'clientInfo': {'name': 'stranger-loot-agent', 'version': '0.2.0'}})
        self.version = result['protocolVersion']
        self.request('notifications/initialized', notification=True)
        tools = self.request('tools/list').get('tools', [])
        # Only this reviewed public catalogue tool may be called.
        return {tool['name']: tool for tool in tools if tool['name'] == 'query_publiccatalogue'
                and tool.get('annotations', {}).get('readOnlyHint') is True}

    def projects(self, search=''):
        if 'query_publiccatalogue' not in self.connect():
            raise MCPError('The public catalogue tool is unavailable.')
        result = self.request('tools/call', {'name': 'query_publiccatalogue', 'arguments': {
            'query': {'key': 'community-feeds'}, 'limit': 1, 'fields': ['key', 'snapshot']}})
        if result.get('isError'):
            raise MCPError('The public catalogue query failed.')
        data = result.get('structuredContent')
        if data is None:
            data = json.loads(next(part['text'] for part in result.get('content', []) if part.get('type') == 'text'))
        records = data.get('records', [])
        gallery = records[0].get('snapshot', {}).get('gallery', {}).get('data', {}) if records else {}
        snapshot_items = gallery.get('items', [])
        items = []
        for item in snapshot_items:
            links = [item.get('public_url'), item.get('url'),
                     (item.get('try_cta') or {}).get('url'), item.get('agent_address')]
            address = next((agent_address(link) for link in links if isinstance(link, str) and agent_address(link)), None)
            if address:
                items.append(dict(item, target_address=address))
        needle = search.casefold()
        matches = [item for item in items if needle in (str(item.get('name', '')) + ' ' + str(item.get('one_liner', ''))).casefold()]
        lines = ['ASI/Agentverse projects in Stranger Loot (snapshot: %s)' % gallery.get('as_of', 'unknown')]
        lines.append('This snapshot contains %s of %s projects; discovery may be incomplete.' %
                     (len(snapshot_items), gallery.get('total', len(snapshot_items))))
        for item in matches[:5]:
            lines.append('%s: %s\nAgent: %s\n%s' % (str(item.get('name') or '')[:100], str(item.get('one_liner') or '')[:350], item['target_address'], str(item.get('url') or '')[:300]))
        if not matches:
            lines.append('No matching ASI/Agentverse addresses in this snapshot. Supply an agent1 address or ASI/Agentverse profile link to test an agent directly.')
        lines.append('Catalogue descriptions are unverified claims, not hands-on test results.')
        return '\n\n'.join(lines)


def reply_to_command(text):
    text = text.strip()
    if len(text) > 500:
        return 'Please keep your request under 500 characters.'
    if text.casefold() == 'mcp tools':
        tools = StrangerLootMCP().connect()
        return 'Connected to Stranger Loot MCP. Enabled read-only tools: ' + (', '.join(tools) or 'none')
    if text.casefold() == 'projects' or text.casefold().startswith('projects '):
        return StrangerLootMCP().projects(text[8:].strip())
    return ('I find Fetch.ai projects and test Agentverse agents through chat. '
            'Send projects or projects <search words>. To test, supply the target agent1 address: '
            'test <address> | <fictional task> | <expected text>. I show a plan before you confirm. '
            'No websites or payments. Send mcp tools to check the catalogue connection.')
