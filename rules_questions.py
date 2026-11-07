"""Answer bounded event questions from the public plugin snapshot, without account actions."""
from challenge_rules import RULES


def answer_rules_question(text):
    lower = text.strip().casefold()
    if lower.startswith(('investigate ', 'review ', 'find ', 'projects', 'test ', 'try ')):
        return None
    anchors = ('stranger builds', 'strangerbuilds', 'fetch.ai', 'fetch ai', 'rule', 'judg', 'hire',
               'feedback', 'eligible', 'eligibility', 'submission', 'deadline', 'repo', 'prize', 'sponsor', 'team size')
    if not any(term in lower for term in anchors):
        return None
    challenge = RULES['challenge']
    if any(term in lower for term in ('cash', 'paid', 'payment', 'pay ')):
        entry = next(entry for entry in RULES['general_rules'] if entry['title'] == 'Taking money from users')
        answer = entry['text']
    elif any(term in lower for term in ('repo', 'fork', 'opening', 'new work')):
        answer = challenge['rule'] + ' The public repo must not be a fork. Its creation date and history need verification; I have not checked them for your project.'
    elif any(term in lower for term in ('hire', 'automated', 'own test', 'owner test', 'self-test')):
        answer = challenge['definitions']['hire'] + ' My automated agent-to-agent trials and owner tests do not establish this requirement. I do not record official feedback, votes or counted hires.'
    elif 'feedback' in lower or 'improve' in lower:
        answer = challenge['brief'][2] + ' Internal testing is not proof of outside-team feedback. Until genuine feedback is recorded through the required process, keep it pending.'
    elif 'judg' in lower or 'score' in lower:
        answer = ('People judge entries. The general criteria are distinctiveness, whether it works, real sponsor integration and what the builders learned, equally weighted (1–5 each). '
                  'For Fetch.ai, usefulness, reliability and real use matter; agents hiring agents or getting paid can score higher. I am not an official judge, and a keyword match is not a quality score.')
    elif any(term in lower for term in ('deadline', 'when', 'close')):
        answer = (challenge['game']['clause'] + ' This snapshot does not establish an exact Melbourne closing time; check the current official schedule before relying on a cutoff.')
    elif 'team' in lower:
        answer = next(entry['text'] for entry in RULES['general_rules'] if entry['title'] == 'Teams of 1 or 2')
    elif 'prize' in lower:
        answer = 'This bundled snapshot does not establish the requested prize amount or your eligibility. Check the current Stranger Builds event book or official rules; I will not invent a prize or guarantee a win.'
    else:
        answer = (' '.join(challenge['brief']) + ' I can explain these requirements, but cannot certify eligibility or completion from a chat trial alone.')
    return (answer + '\n\nSource: Stranger Builds event_book, version ' + RULES['book_version'] +
            ', fetched ' + RULES['fetched_at'] + ' (snapshot, not a live rules lookup). '
            'Official source: ' + RULES['source_url'])
