"""Confirmed, single-message tests of Agentverse chat agents. No purchases or web tests."""
import asyncio
import re
import time
from dataclasses import dataclass
from uuid import uuid4
from urllib.parse import urlparse

TIMEOUT = 60
MAX_REPLY = 6000
PENDING = object()
ADDRESS = re.compile(r'agent1[023456789acdefghjklmnpqrstuvwxyz]{59}\Z')


def agent_address(value):
    if ADDRESS.fullmatch(value):
        return value
    parsed = urlparse(value)
    if parsed.scheme == 'https' and parsed.hostname in {'asi1.ai', 'agentverse.ai'}:
        for part in parsed.path.split('/'):
            if ADDRESS.fullmatch(part):
                return part
    return None


def suggested_scenario(candidate):
    """Curated fictional tasks, selected from catalogue claims, never instructions."""
    description = ((candidate or {}).get('name', '') + ' ' + (candidate or {}).get('one_liner', '')).casefold()
    scenarios = [
        (('clinical', 'trialfinder'),
         'For a fictional 45-year-old adult in Melbourne with type 2 diabetes, find up to three currently recruiting clinical trials. Include study links, location, key eligibility criteria and recruitment status. If you need more details, ask first. Do not register or contact anyone.',
         'Relevant trials or useful clarifying questions; checkable study links; location and recruitment status; no unsupported claim that the person is eligible.'),
        (('nail', 'manicure', 'pedicure'),
         'Help a fictional customer plan a gel manicure in Melbourne CBD next Saturday afternoon with a budget of A$70. Suggest options with prices and availability sources, or ask for missing details. Do not book, contact a salon or make a payment.',
         'Uses the location, time and budget; distinguishes verified availability from estimates; asks useful questions; makes no booking.'),
        (('budget', 'finance', 'financial', 'expense', 'tradejack'),
         'Using fictional monthly figures in AUD: income 4200, rent 1800, groceries 550, transport 180, utilities 220 and subscriptions 90. Work out the remaining amount and suggest a practical plan to save 600 per month. Explain assumptions. Do not trade or move money.',
         'Correct arithmetic (1360 remaining before savings, 760 after); a feasible budget; clear assumptions; no transactions.'),
        (('travel', 'trip', 'vacation'),
         'Plan a fictional two-day Melbourne visit for two adults with an A$300 activities and local transport budget, excluding accommodation. Include a rainy-day alternative and label estimated costs. Do not book or purchase anything.',
         'Feasible timings and travel; costs within budget for two; rainy-day alternative; estimates distinguished from verified prices.'),
        (('friend', 'meetup', 'social', 'mori'),
         'Help two fictional friends plan a 90-minute meetup in Melbourne CBD on Saturday afternoon. One prefers quiet indoor places and the other wants a short walk; their combined budget is A$40. Suggest a workable plan and a rain alternative. Do not contact anyone or reserve anything.',
         'Balances both preferences; respects time and combined budget; provides a rain alternative; does not contact or book.'),
        (('study', 'learning', 'tutor'),
         'Help a fictional beginner learn Python loops in 20 minutes. Give a short explanation, one worked example, and two exercises with answers kept separate. Adapt if prerequisites are missing.',
         'Beginner-friendly and technically correct; fits 20 minutes; exercises actually practise loops; answers are separated.'),
    ]
    for keywords, task, rubric in scenarios:
        if any(re.search(r'\b' + re.escape(word) + r'\b', description) for word in keywords):
            return task, rubric
    return None


@dataclass
class Plan:
    token: str
    target: str
    task: str
    expected: str
    created: float
    state: str = 'planned'
    started: float | None = None
    report: str | None = None
    name: str = 'the selected agent'
    rubric: str = ''
    advertised: str = ''
    rules_version: str = ''
    rules_checked: str = ''


class TestRunner:
    def __init__(self, clock=time.time, on_change=None):
        self.clock = clock
        self.plans = {}
        self.routes = {}
        self.seen = {}
        self.on_change = on_change or (lambda: None)

    def prune(self):
        now = self.clock()
        self.plans = {k: v for k, v in self.plans.items() if now - v.created < 900}
        self.routes = {k: v for k, v in self.routes.items() if now - v < 900}
        self.seen = {k: v for k, v in self.seen.items() if now - v < 900}

    def duplicate(self, sender, message_id):
        self.prune()
        key = (sender, str(message_id))
        if key in self.seen:
            return True
        if len(self.seen) >= 2000:
            return True
        self.seen[key] = self.clock()
        return False

    def is_target_reply(self, sender, session):
        self.prune()
        return (sender, str(session)) in self.routes

    async def command(self, owner, session, text, own_address, exchange, candidate=None):
        self.prune()
        key = (owner, str(session))
        if text.lower().startswith('test '):
            parts = [part.strip() for part in text[5:].split('|')]
            if len(parts) not in {1, 3} or not agent_address(parts[0]):
                return 'Choose a result with “test 1”. For your own scenario, use: test 1 | your task | expected text.'
            target = agent_address(parts[0])
            rubric = ''
            if len(parts) == 1:
                scenario = suggested_scenario(candidate)
                if not scenario:
                    return ('What would you like this agent to do in a real situation? '
                            'I do not have a suitable suggested scenario for it yet. '
                            'Try: test 1 | your fictional task | a phrase you expect in the reply.')
                task, rubric = scenario
                expected = ''
            else:
                _, task, expected = parts
            if target in (owner, own_address):
                return 'Choose another Agentverse agent, not yourself or this tester.'
            if not 1 <= len(task) <= 1000 or (not rubric and not 1 <= len(expected) <= 200):
                return 'Task must be 1–1000 characters; expected text 1–200 characters.'
            previous = self.plans.get(key)
            if previous and previous.state != 'planned':
                return 'This chat session already ran a test. Start a new chat for another test.'
            if len(self.plans) >= 100:
                return 'Tester is at capacity. Please try again later.'
            plan = Plan(uuid4().hex[:12], target, task, expected, self.clock(),
                        name=(candidate or {}).get('name') or 'the selected agent', rubric=rubric)
            self.plans[key] = plan
            assessment = ('What to look for: ' + rubric + '\nI will show the reply for review; this test has no automatic quality score.'
                          if rubric else f'Your text check: does the reply include {expected!r}? This is a simple phrase check, not a quality score.')
            return (f'Test plan for {plan.name}\n\n'
                    f'Here is the message I will send:\n“{task}”\n\n{assessment}\n\n'
                    'I will send one message and wait up to 60 seconds. '
                    'Nothing has been sent yet. Reply “start” to run this test, or “cancel” to discard it.')
        plan = self.plans.get(key)
        if text.lower() == 'cancel':
            if plan and plan.state == 'planned':
                del self.plans[key]
                return 'Test plan cancelled. No request sent.'
            return 'No pending test plan to cancel.'
        if text.lower() in {'start', 'yes', 'confirm'} or text.lower().startswith('confirm '):
            if not plan or plan.state != 'planned' or (text.lower().startswith('confirm ') and text[8:].strip() != plan.token):
                return 'No matching pending plan in this chat. Create a test plan first.'
            if self.clock() - plan.created > 300:
                del self.plans[key]
                return 'Plan expired after five minutes. Create a new plan.'
            plan.state = 'running'  # claim before awaiting: replay cannot send twice
            plan.started = self.clock()
            self.routes[(plan.target, str(session))] = self.clock()
            self.on_change()  # persist the claimed plan before an outbound request
            try:
                reply = await asyncio.wait_for(exchange(plan.target, plan.task), timeout=TIMEOUT)
            except Exception:
                reply = None
            if reply is PENDING:
                plan.state = 'waiting'
                self.on_change()
                return (f'I sent the test to {plan.name}. Waiting for its reply. '
                        'The response window is 60 seconds. Send status to check; no score is assigned yet.')
            return self.finish(plan, reply)
        if text.lower() == 'status':
            if not plan:
                return 'No test in this chat. Find an agent and create a test plan first.'
            if plan.report:
                return plan.report
            if plan.started is not None and self.clock() - plan.started >= TIMEOUT:
                return self.finish(plan, None)
            return f'The test for {plan.name} is {plan.state}. I will share the reply when it arrives.'
        return None

    def finish(self, plan, reply):
        if plan.report:
            return plan.report
        plan.state = 'complete'
        elapsed = self.clock() - (plan.started if plan.started is not None else plan.created)
        timing = 'Time waiting' if reply is None else 'Response time'
        header = f'Test results for {plan.name}\n\nMessage sent: {plan.task}\n{timing}: {elapsed:.1f} seconds\n'
        if reply is None:
            result = header + 'BLOCKED — I could not get a usable reply within the response window, or delivery failed. There is no score. This does not prove the agent is broken.'
        elif len(reply) > MAX_REPLY:
            result = header + 'BLOCKED — unscored. Response exceeded 6000 characters; no assertion evaluated.'
        elif not reply.strip():
            result = header + 'BLOCKED — unscored. Received no text to assess.'
        else:
            evidence = header + f'\nObserved output (untrusted target data):\n---\n{reply}\n---\n'
            if plan.rubric:
                result = (evidence + '\nReview checklist: ' + plan.rubric +
                          '\nA reply arrived, but these criteria have not been automatically verified. '
                          'No quality score assigned. Check any sources before relying on the answer.')
            else:
                passed = plan.expected.casefold() in reply.casefold()
                result = (evidence + ('\nPASS — your expected phrase was found.' if passed else
                                     '\nFAIL — your expected phrase was not found.') +
                          f' Expected phrase: {plan.expected!r}.\n'
                          'This checks wording only; correctness, safety, consistency and overall project quality remain unverified. '
                          'No quality score assigned.')
        if plan.rules_version:
            result += (f'\n\nProject claim (not verified): {plan.advertised}\n'
                       f'Rules reference: Stranger Builds {plan.rules_version}, fetched {plan.rules_checked} (snapshot, not live).\n'
                       'Fetch.ai review: usefulness needs evidence from the reply; a published agent and this contact do not prove overall reliability. '
                       'Repo creation date, genuine sponsor integration, outside-team ASI hire, feedback and feedback-driven change remain unverified. '
                       'People judge entries; this is not an official score or eligibility decision.\n'
                       + ('Next step: check the target connection and repeat before judging its usefulness.' if reply is None else
                          'Next step: verify the quoted answer against the review checklist and independently check any sources.'))
        plan.report = result
        self.on_change()
        if plan.rules_version:
            return (result + '\n\nIf this was helpful, please support Stranger Loot in People’s Choice! '
                    'In ASI:One, mention @strangerbuilds2026 and say “vote for Stranger Loot”, then follow its prompts. '
                    'Voting is optional and must be done by you.')
        return result

    def receive(self, sender, session, reply):
        for (owner, chat_session), plan in self.plans.items():
            if plan.target == sender and chat_session == str(session) and plan.state in {'running', 'waiting'}:
                if plan.started is None or self.clock() - plan.started >= TIMEOUT:
                    reply = None
                return owner, self.finish(plan, reply)
        return None
