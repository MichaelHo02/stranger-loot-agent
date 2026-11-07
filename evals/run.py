"""Evaluate business outcomes. Fixture, MCP and visible ASI results stay separate."""
import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from discovery import normalize_user_text, search_description
from mcp_client import StrangerLootMCP
from test_runner import agent_address


def grade_discovery(case, matches, elapsed):
    failures = []
    expected = case.get('expected_name')
    selected = [item for item in matches if item.get('name') == expected]
    if expected and not selected:
        failures.append('Expected candidate absent: ' + expected)
    if case.get('expect_empty') and matches:
        failures.append('Invented or irrelevant match for an unsupported request')
    if len(matches) < case.get('minimum_results', 0):
        failures.append('Too few candidates for an ambiguous request')
    if len(matches) > 5:
        failures.append('Shortlist exceeds five candidates')
    if case.get('require_address') and selected and not selected[0].get('target_address'):
        failures.append('Expected a published address for the ready candidate')
    for item in matches:
        link = item.get('agent_link')
        address = item.get('target_address')
        if address and (agent_address(address) != address or (link and agent_address(link) != address)):
            failures.append('Address is not grounded in the published link')
    if elapsed > 30:
        failures.append('Discovery exceeded 30 seconds')
    return failures


def grade_asi(case):
    failures = []
    if case.get('observer') != 'cua_visible_ui':
        failures.append('Missing visible UI observation; envelope logs alone do not count')
    window = case.get('observed_after_seconds', 0)
    latency = case.get('visible_reply_seconds')
    text = case.get('visible_reply_text')
    if latency is None or not text:
        failures.append('No visible agent reply')
        if window < 30:
            failures.append('Observation window shorter than the 30-second deadline')
    elif not isinstance(latency, (int, float)) or latency < 0 or latency > window:
        failures.append('Invalid visible-reply timing')
    elif latency > 30:
        failures.append('Visible reply exceeded 30 seconds')
    for term in case.get('required_terms', []):
        if not text or term.casefold() not in text.casefold():
            failures.append('Missing expected visible response: ' + term)
    if not case.get('evidence_file'):
        failures.append('Missing screenshot evidence reference')
    return failures


def run_discovery(mode):
    cases = json.loads((ROOT / 'evals/cases.json').read_text())
    fixture = json.loads((ROOT / 'evals/catalogue.json').read_text())
    results = []
    for case in cases:
        started = time.monotonic()
        try:
            manager = nullcontext()
            if mode == 'fixture':
                manager = patch.multiple(StrangerLootMCP,
                    connect=lambda self: {'query_publiccatalogue': {}},
                    request=lambda *args, **kwargs: {'structuredContent': {'records': [{'snapshot': fixture}]}})
            with manager:
                query = search_description(normalize_user_text(case['prompt']))
                if query is None:
                    raise ValueError('Prompt did not enter the discovery path')
                reply, matches = StrangerLootMCP().discover(query)
            elapsed = time.monotonic() - started
            failures = grade_discovery(case, matches, elapsed)
            results.append(dict(case, status='fail' if failures else 'pass', elapsed_seconds=round(elapsed, 3),
                                candidate_names=[item.get('name') for item in matches], failures=failures))
        except Exception as error:
            results.append(dict(case, status='error', failures=[type(error).__name__], elapsed_seconds=round(time.monotonic()-started, 3)))
    return results


def build_report(layer, results):
    passed = sum(result['status'] == 'pass' for result in results)
    return {'schema_version': 1, 'layer': layer, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'commit': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
            'working_tree_dirty': bool(subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).strip()),
            'total': len(results), 'passed': passed, 'failed': len(results)-passed,
            'gate': 'pass' if results and passed == len(results) else 'fail', 'results': results,
            'limits': 'Fixture and local MCP success do not establish hosted or ASI delivery. ASI requires visible UI evidence. Golden live cases may fail when public catalogue coverage changes; investigate rather than silently skip.'}


def readiness(directory):
    """Fail closed when any evidence layer is missing, failing, dirty or stale."""
    results = []
    current = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    for layer in ('fixture', 'mcp', 'asi'):
        path = directory / (layer + '.json')
        failures = []
        if not path.exists():
            failures.append('Missing evaluation report')
        else:
            report = json.loads(path.read_text())
            if (report.get('layer') != layer or not report.get('results') or report.get('gate') != 'pass'
                    or any(case.get('status') != 'pass' for case in report.get('results', []))):
                failures.append('Evaluation layer has not passed')
            subject = report.get('subject_commit', report.get('commit'))
            if subject != current:
                failures.append('Evidence is for a different code commit')
            if layer != 'asi' and report.get('working_tree_dirty'):
                failures.append('Evaluation used an uncommitted working tree')
            if layer == 'asi':
                for case in report.get('results', []):
                    failures.extend(grade_asi(case))
                    try:
                        checked = datetime.fromisoformat(case['checked_at'].replace('Z', '+00:00'))
                        age = (datetime.now(timezone.utc) - checked).total_seconds()
                        if not 0 <= age <= 3600:
                            failures.append('ASI UI observation is not fresh (one-hour maximum)')
                    except (KeyError, ValueError, TypeError):
                        failures.append('Missing or invalid ASI observation timestamp')
        results.append({'id':layer, 'status':'fail' if failures else 'pass', 'failures':failures})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture','mcp','asi','readiness'], required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / '.eval-results')
    args = parser.parse_args()
    if args.mode == 'readiness':
        results = readiness(args.output)
    elif args.mode == 'asi':
        if not args.evidence:
            parser.error('--evidence is required for ASI; no simulated ASI passes')
        evidence = json.loads(args.evidence.read_text())
        results = []
        for case in evidence['cases']:
            failures = grade_asi(case)
            results.append(dict(case, status='fail' if failures else 'pass', failures=failures))
    else:
        results = run_discovery(args.mode)
    report = build_report(args.mode, results)
    if args.mode == 'asi':
        report['subject_commit'] = evidence.get('deployed_commit', 'unknown')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f'{args.mode}.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = [f'# {args.mode} evaluation', '', f"Gate: **{report['gate'].upper()}** — {report['passed']}/{report['total']} cases passed.", '', '| Case | Result | Failures |', '| --- | --- | --- |']
    lines += [f"| {result['id']} | {result['status']} | {'; '.join(result['failures']) or '—'} |" for result in results]
    lines += ['', report['limits'], '']
    (args.output / f'{args.mode}.md').write_text('\n'.join(lines))
    print(f"{args.mode}: {report['passed']}/{report['total']} passed; gate={report['gate']}; report={args.output / (args.mode + '.md')}")
    return 0 if report['gate'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
