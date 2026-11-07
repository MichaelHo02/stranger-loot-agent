"""Repeatable handler benchmark. Synthetic responses are never labelled live ASI."""
import argparse
import asyncio
import importlib
import json
import math
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from workflow_state import WorkflowState
from evals.run import build_report

TARGET = 'agent1' + 'q' * 59
SELF = 'agent1' + 'z' * 59


class Storage:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = json.loads(json.dumps(value))


def percentile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


async def sample(chat, case):
    """Exercise handler + saved workflow state, never an external target."""
    context = SimpleNamespace(storage=Storage(), session=uuid4(),
                              agent=SimpleNamespace(address=SELF), send=AsyncMock())
    state = WorkflowState(context.storage)
    state.shortlists.save('owner', context.session, [{'target_address': TARGET,
                          'name': case['name'], 'one_liner': case['description']}])
    state.save()
    latencies = []
    failures = []

    async def turn(text):
        context.send.reset_mock()
        started = time.perf_counter()
        await chat.handle_message(context, 'owner', ChatMessage(content=[TextContent(type='text', text=text)]))
        latencies.append((time.perf_counter() - started) * 1000)
        return context.send.call_args.args[1].text()

    plan_text = await turn('@' + SELF + ' test 1')
    plan = WorkflowState(context.storage).runner.plans.get(('owner', str(context.session)))
    if plan is None:
        return latencies, ['No saved plan']
    for term in case['task_terms']:
        if term.casefold() not in plan.task.casefold():
            failures.append('Missing scenario requirement: ' + term)
    for term in case['rubric_terms']:
        if term.casefold() not in plan.rubric.casefold():
            failures.append('Missing review criterion: ' + term)
    if case['name'] not in plan_text or 'Reply “start”' not in plan_text:
        failures.append('Plan lacks name or friendly start action')
    if TARGET in plan_text or plan.token in plan_text:
        failures.append('Internal identifier exposed in plan')
    if any(call.args[0] == TARGET for call in context.send.call_args_list):
        failures.append('Target contacted before confirmation')
    await turn('@stranger-loot-tester start')
    sent = [call for call in context.send.call_args_list if call.args[0] == TARGET]
    if len(sent) != 1 or sent[0].args[1].text() != plan.task:
        failures.append('Start did not send the exact planned task once')
    await turn('start')
    if any(call.args[0] == TARGET for call in context.send.call_args_list):
        failures.append('Repeated start sent another task')
    # Synthetic target data tests reporting, not actual target quality or delivery.
    response = ChatMessage(content=[TextContent(type='text', text='Synthetic response for report evaluation.')])
    await chat.handle_message(context, TARGET, response)
    report = context.send.call_args.args[1].text()
    if 'Review checklist' not in report or case['name'] not in report:
        failures.append('Missing named evidence report and rubric')
    if TARGET in report or plan.token in report or '100/100' in report or 'PASS' in report:
        failures.append('Report exposes IDs or invents a quality pass')
    return latencies, failures


async def evaluate(repeats, budget_ms):
    with patch('uagents.Agent'):
        chat = importlib.import_module('agent')
    results = []
    for case in json.loads((ROOT / 'evals/scenarios.json').read_text()):
        times, failures = [], []
        for _ in range(repeats):
            try:
                elapsed, errors = await sample(chat, case)
                times.extend(elapsed)
                failures.extend(errors)
            except Exception as error:
                failures.append(type(error).__name__ + ': ' + str(error))
        p95 = percentile(times, .95)
        if p95 is None or p95 > budget_ms:
            failures.append('Handler p95 exceeds latency budget or has no samples')
        results.append({'id':case['id'], 'status':'fail' if failures else 'pass',
                        'failures':sorted(set(failures)), 'repeats':repeats, 'turns_measured':len(times),
                        'p50_ms':round(percentile(times, .5), 3) if times else None,
                        'p95_ms':round(p95, 3) if p95 is not None else None,
                        'max_ms':round(max(times), 3) if times else None})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=20)
    parser.add_argument('--budget-ms', type=float, default=250)
    parser.add_argument('--output', type=Path, default=ROOT / '.eval-results')
    args = parser.parse_args()
    if not 1 <= args.repeats <= 100 or not math.isfinite(args.budget_ms) or args.budget_ms <= 0:
        parser.error('Use 1–100 repeats and a positive finite latency budget')
    results = asyncio.run(evaluate(args.repeats, args.budget_ms))
    report = build_report('performance', results)
    report['limits'] = 'Local handler with synthetic transport and target replies. Excludes network and hosted ASI delivery; no quality scores are assessed.'
    report['budget_ms'] = args.budget_ms
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'performance.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Handler performance', '', report['limits'], '',
             f"Gate: **{report['gate']}**. p95 budget: {args.budget_ms} ms.", '',
             '| Scenario | Result | Turns | p50 ms | p95 ms | Max ms |', '| --- | --- | --- | --- | --- | --- |']
    lines += [f"| {r['id']} | {r['status']} | {r['turns_measured']} | {r['p50_ms']} | {r['p95_ms']} | {r['max_ms']} |" for r in results]
    lines += ['', *[f"- {r['id']}: {failure}" for r in results for failure in r['failures']]]
    (args.output / 'performance.md').write_text('\n'.join(lines) + '\n')
    print(f"performance: {report['passed']}/{report['total']} scenarios passed; {args.repeats} repeats; gate={report['gate']}")
    return 0 if report['gate'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
