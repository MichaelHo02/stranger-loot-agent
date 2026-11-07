"""Small, bounded client for Stranger Loot's public Streamable HTTP MCP."""
import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from test_runner import agent_address
from discovery import rank_projects, search_description

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

    def discover(self, search=''):
        if 'query_publiccatalogue' not in self.connect():
            raise MCPError('The public catalogue tool is unavailable.')
        result = self.request('tools/call', {'name': 'query_publiccatalogue', 'arguments': {
            'query': {'key': 'current'}, 'limit': 1, 'fields': ['key', 'snapshot']}})
        if result.get('isError'):
            raise MCPError('The public catalogue query failed.')
        data = result.get('structuredContent')
        if data is None:
            data = json.loads(next(part['text'] for part in result.get('content', []) if part.get('type') == 'text'))
        records = data.get('records', [])
        snapshot = records[0].get('snapshot', {}) if records else {}
        # Only explicitly public detailed entries; never use locked/rest data.
        detailed = snapshot.get('free', [])
        items = []
        for item in detailed:
            links = [item.get('public_url'), item.get('try_url'), item.get('agent_address')]
            address = next((agent_address(link) for link in links if isinstance(link, str) and agent_address(link)), None)
            asi_link = next((link for link in links if isinstance(link, str)
                            and urlparse(link).scheme == 'https'
                            and urlparse(link).hostname in {'asi1.ai', 'agentverse.ai'}), None)
            if address or asi_link:
                items.append(dict(item, target_address=address, agent_link=asi_link))
        matches = rank_projects(items, search)
        lines = ['ASI/Agentverse shortlist from Stranger Loot MCP (updated: %s)' %
                 (snapshot.get('lastSync') or {}).get('at', 'unknown')]
        lines.append('%s detailed public projects searched; %s total indexed. Some descriptions or agent links may be unavailable.' %
                     (len(detailed), snapshot.get('total', len(detailed))))
        for index, item in enumerate(matches, 1):
            lines.append('%s. %s: %s\n%s\n%s' % (
                index, str(item.get('name') or '')[:100], str(item.get('one_liner') or '')[:350],
                '[View profile](%s)' % str(item.get('agent_link') or item.get('source_url') or '')[:600],
                'Ready for a confirmed chat test.' if item.get('target_address') else
                'ASI link found; agent address not published here, so testing is unavailable.'))
        if not matches:
            lines.append('No matching ASI/Agentverse candidates in the available public details. Try different words. This is not proof that no such agent exists.')
        elif any(item.get('target_address') for item in matches):
            ready_index = next(index for index, item in enumerate(matches, 1) if item.get('target_address'))
            lines.append('Want to try one? Reply **test %s** and I will suggest a realistic scenario for you to review before sending it.' % ready_index)
        else:
            lines.append('Candidate profiles are available above. Automatic testing needs a published Chat Protocol agent address; no address will be guessed.')
        lines.append('Matches use keywords, related terms and typo tolerance. Descriptions are unverified claims; no agent has been tested by this search.')
        return '\n\n'.join(lines), matches

    def projects(self, search=''):
        return self.discover(search)[0]


def reply_to_command(text, shortlists=None, owner=None, session=None):
    text = text.strip()
    if len(text) > 500:
        return 'Please keep your request under 500 characters.'
    if text.casefold() == 'mcp tools':
        tools = StrangerLootMCP().connect()
        return 'Connected to Stranger Loot MCP. Enabled read-only tools: ' + (', '.join(tools) or 'none')
    query = search_description(text)
    if query is not None:
        reply, matches = StrangerLootMCP().discover(query)
        if shortlists is not None and not shortlists.save(owner, session, matches):
            return 'Discovery is at capacity. Please try again later.'
        return reply
    return ('I investigate ASI projects for hackathon builders. Tell me what to explore, such as '
            '“investigate a clinical trials agent”. I research the public details, use the available challenge rules, '
            'and run three chat-only checks. I ask only if several projects match. '
            'You receive the quoted reply and review criteria, or a clear blocked result. '
            'Send status while waiting. No purchases, votes or official feedback. '
            'Rules currently use a dated Stranger Builds snapshot. Send projects to browse without testing.')
