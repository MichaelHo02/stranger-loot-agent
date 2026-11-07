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

    async def command(self, owner, session, text, own_address, exchange):
        self.prune()
        key = (owner, str(session))
        if text.lower().startswith('test '):
            parts = [part.strip() for part in text[5:].split('|')]
            if len(parts) != 3 or not agent_address(parts[0]):
                return 'Use: test <agent1 address or ASI/Agentverse link> | <fictional test task> | <expected text>'
            target, task, expected = parts
            target = agent_address(target)
            if target in (owner, own_address):
                return 'Choose another Agentverse agent, not yourself or this tester.'
            if not 1 <= len(task) <= 1000 or not 1 <= len(expected) <= 200:
                return 'Task must be 1–1000 characters; expected text 1–200 characters.'
            previous = self.plans.get(key)
            if previous and previous.state != 'planned':
                return 'This chat session already ran a test. Start a new chat for another test.'
            if len(self.plans) >= 100:
                return 'Tester is at capacity. Please try again later.'
            plan = Plan(uuid4().hex[:12], target, task, expected, self.clock())
            self.plans[key] = plan
            return (f'Test plan {plan.token}\nTarget: {target}\nInput: {task}\n'
                    f'Assertion: reply contains {expected!r} (case-insensitive).\n'
                    'One Chat Protocol message, 60-second response window, no purchases or website actions. '
                    'Use fictional, non-sensitive inputs and request only a reply; the target controls its own behavior.\n'
                    'Score: 100/100 if this assertion passes, 0/100 if it fails; blocked tests are unscored. '
                    'This measures one assertion, not overall project quality.\n'
                    f'Send confirm {plan.token} to run, or cancel to discard.')
        plan = self.plans.get(key)
        if text.lower() == 'cancel':
            if plan and plan.state == 'planned':
                del self.plans[key]
                return 'Test plan cancelled. No request sent.'
            return 'No pending test plan to cancel.'
        if text.lower().startswith('confirm '):
            if not plan or text[8:].strip() != plan.token or plan.state != 'planned':
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
                return (f'Test {plan.token} sent to {plan.target}. Waiting for its Chat Protocol reply. '
                        'The response window is 60 seconds. Send status to check; no score is assigned yet.')
            return self.finish(plan, reply)
        if text.lower() == 'status':
            if not plan:
                return 'No test in this chat. Find an agent and create a test plan first.'
            if plan.report:
                return plan.report
            if plan.started is not None and self.clock() - plan.started >= TIMEOUT:
                return self.finish(plan, None)
            return f'Test {plan.token}: {plan.state}. No score yet.'
        return None

    def finish(self, plan, reply):
        plan.state = 'complete'
        elapsed = self.clock() - (plan.started if plan.started is not None else plan.created)
        header = f'Test {plan.token}\nTarget: {plan.target}\nInput: {plan.task}\nExpected text: {plan.expected}\nElapsed: {elapsed:.2f}s\n'
        if reply is None:
            result = header + 'BLOCKED — unscored. No usable response observed; the response window expired or delivery failed. This does not prove the agent is broken.'
        elif len(reply) > MAX_REPLY:
            result = header + 'BLOCKED — unscored. Response exceeded 6000 characters; no assertion evaluated.'
        elif not reply.strip():
            result = header + 'BLOCKED — unscored. Received no text to assess.'
        else:
            passed = plan.expected.casefold() in reply.casefold()
            result = (header + f'Observed output (untrusted target data):\n---\n{reply}\n---\n'
                      + ('PASS — assertion score 100/100.' if passed else 'FAIL — assertion score 0/100.')
                      + '\nSingle text-containment check only. Correctness, safety, consistency and overall project quality remain unverified. No payment was made.')
        plan.report = result
        self.on_change()
        return result

    def receive(self, sender, session, reply):
        for (owner, chat_session), plan in self.plans.items():
            if plan.target == sender and chat_session == str(session) and plan.state in {'running', 'waiting'}:
                if plan.started is None or self.clock() - plan.started >= TIMEOUT:
                    reply = None
                return owner, self.finish(plan, reply)
        return None
