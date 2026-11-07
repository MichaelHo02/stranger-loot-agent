"""Description matching and user-owned shortlists. Catalogue text is data only."""
import re
import time
from difflib import SequenceMatcher

STOP = set('a an the i me my we our you your please can could would want like looking look find search for show list give help helps helping agent agents project projects asi fetch ai that which to of in on with and or is are does do it something about manage need near'.split())
GROUPS = [
    {'nail', 'nails', 'manicure', 'pedicure', 'salon'},
    {'appointment', 'appointments', 'booking', 'book', 'schedule', 'scheduling', 'reservation', 'reservations'},
    {'money', 'finance', 'financial', 'budget', 'budgeting', 'expense', 'expenses'},
    {'travel', 'trip', 'trips', 'holiday', 'vacation'},
    {'friend', 'friends', 'social', 'hangout', 'together', 'meetup'},
    {'study', 'studies', 'trial', 'trials', 'research'},
    {'medical', 'health', 'healthcare', 'clinical', 'patient', 'patients'},
]


def normalize_user_text(text, own_address=None):
    """ASI uses our address on profile first turns and our handle on later turns."""
    recipients = ['stranger-loot-tester']
    if own_address:
        recipients.append(own_address)
    pattern = r'^@(?:' + '|'.join(re.escape(recipient) for recipient in recipients) + r')(?:\s+|$)'
    return re.sub(pattern, '', text.strip(), count=1, flags=re.I).strip()


def words(text):
    return set(re.findall(r'[^\W_]+', text.casefold()))


def rank_projects(items, query):
    terms = words(query) - STOP
    concepts = []
    for term in sorted(terms):
        group = next((group for group in GROUPS if term in group), {term})
        if group not in concepts:
            concepts.append(group)
    ranked = []
    for item in items:
        name = words(str(item.get('name') or ''))
        description = words(str(item.get('one_liner') or ''))
        score = 0
        for group in concepts:
            if name & group:
                score += 3
            elif description & group:
                score += 1
            elif any(len(term) >= 4 and SequenceMatcher(None, term, word).ratio() >= .84
                     for term in group for word in name | description):
                score += .5
            else:
                break
        else:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get('name') or '').casefold()))
    return [item for _, item in ranked[:5]]


class Shortlists:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.results = {}

    def save(self, owner, session, matches):
        now = self.clock()
        self.results = {key: value for key, value in self.results.items() if now - value[0] < 300}
        key = (owner, str(session))
        if key not in self.results and len(self.results) >= 100:
            return False
        self.results[key] = (now, [
            {'target_address': item.get('target_address'), 'name': str(item.get('name') or '')[:100]}
            for item in matches[:5]
        ])
        return True

    def resolve(self, owner, session, command):
        """Resolve a number to the exact discovered address, never initiate a test."""
        if not command.lower().startswith('test '):
            return command
        target, separator, rest = command[5:].partition('|')
        if not target.strip().isdigit():
            return command
        result = self.results.get((owner, str(session)))
        if not result or self.clock() - result[0] >= 300:
            raise ValueError('Your shortlist expired or belongs to another chat. Search again before choosing a result.')
        index = int(target.strip()) - 1
        if not 0 <= index < len(result[1]):
            raise ValueError('Choose a number shown in your latest shortlist.')
        item = result[1][index]
        if not item.get('target_address'):
            raise ValueError('This candidate has an ASI link but no published agent address. It cannot be tested through Chat Protocol yet.')
        return 'test ' + item['target_address'] + (' | ' + rest.strip() if separator else '')


def search_description(text):
    stripped = text.strip()
    lower = stripped.casefold()
    for prefix in ('projects', 'find', 'search'):
        if lower == prefix:
            return ''
        if lower.startswith(prefix + ' '):
            return stripped[len(prefix):].strip()
    if lower not in {'help', 'hello', 'hi', 'what can you do?', 'mcp tools'} and not lower.startswith(('test ', 'confirm ', 'cancel')):
        return stripped
    return None
