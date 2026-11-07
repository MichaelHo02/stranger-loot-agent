"""Rules-question regression exercise. Snapshot-grounded answers, not live plugin access."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rules_questions import answer_rules_question
from challenge_rules import RULES
from evals.run import build_report


def evaluate():
    results = []
    for case in json.loads((ROOT/'evals/rules_cases.json').read_text()):
        answer = answer_rules_question(case['prompt']) or ''
        failures = ['Missing required statement: '+term for term in case['required'] if term.casefold() not in answer.casefold()]
        failures += ['Unsupported statement: '+term for term in case['forbidden'] if term.casefold() in answer.casefold()]
        if RULES['book_version'] not in answer or 'snapshot, not a live' not in answer:
            failures.append('Rules provenance missing')
        results.append({'id':case['id'], 'prompt':case['prompt'], 'answer':answer,
                        'status':'fail' if failures else 'pass','failures':failures})
    return results


if __name__ == '__main__':
    report = build_report('rules', evaluate())
    report['limits'] = 'Curated rules questions against a bundled public Stranger Builds snapshot. No live plugin authentication, general reasoning or official eligibility verification.'
    directory = ROOT/'.eval-results'
    directory.mkdir(exist_ok=True)
    (directory/'rules.json').write_text(json.dumps(report,indent=2)+'\n')
    (directory/'rules.md').write_text('# Rules question exercise\n\n'+report['limits']+'\n\n'+
        f"Gate: **{report['gate']}** — {report['passed']}/{report['total']} passed.\n\n"+
        '\n'.join(f"- {r['id']}: {r['status']} {'; '.join(r['failures'])}" for r in report['results'])+'\n')
    print(f"rules: {report['passed']}/{report['total']} passed; gate={report['gate']}")
    raise SystemExit(0 if report['gate']=='pass' else 1)
