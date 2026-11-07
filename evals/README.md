# Outcome evaluations

These evals measure whether users can discover an appropriate agent and actually see its response. They are separate from the code regression suite and from the assertion scores this agent gives a target.

## Baseline and first improvement

On 7 November 2026:

| Layer | Initial baseline | After discovery improvement |
| --- | --- | --- |
| Original 10 discovery cases, fixtures | 7/10 | 10/10 |
| Original 10 discovery cases, live public MCP | 7/10 | 10/10 |
| Expanded discovery set, fixtures | Not run before change | 14/14 |
| Expanded discovery set, live public MCP | Not run before change | 14/14 |
| Visible ASI discovery reply in 30 seconds | 0/1 | No later passing UI observation |

The failing paraphrases involved medical studies, finances, and a meetup between friends. The matcher required every non-filler query concept to match and lacked ordinary related terms. Removing conversational fillers and adding study/trial and meetup vocabulary fixed the original failures. Four additional variants cover clinical studies, budgeting, social meetups, and exclusion of a nail website. These are small hand-written regression examples, not a blinded evaluation or proof of general semantic understanding.

The first fixture and live MCP reports are preserved under `baselines/`. The ASI evidence record is under `evidence/asi-baseline.json`. Screenshot evidence remains local to avoid uploading account UI to the public repository.

## Run

From the repository root, with the existing Python environment:

```sh
# Fast deterministic outcomes using a curated public catalogue fixture.
.venv/bin/python evals/run.py --mode fixture

# Actual public MCP discovery; no target messages, writes, purchases or AI credits.
.venv/bin/python evals/run.py --mode mcp

# Grade an observed ASI browser run. This command does not drive the browser.
.venv/bin/python evals/run.py --mode asi --evidence evals/evidence/asi-baseline.json

# Require all three layers; missing or failing evidence is a failure.
.venv/bin/python evals/run.py --mode readiness
```

Each command writes a JSON record and Markdown scorecard under ignored `.eval-results/`. Failing evals exit 1. Reported provenance includes the code commit and whether the working tree was dirty. The ASI report separately identifies the deployed commit that was actually observed. A live catalogue case can fail because source coverage changed; investigate that result rather than silently dropping the case.

GitHub Actions runs regression tests, fixture evals, scenario performance and live MCP discovery on every push. A green Actions run does **not** pass the visible ASI gate; that requires separate UI evidence.

## ASI UI observation protocol

1. Use CUA to open the public agent profile in an isolated, signed-in chat. Do not read cookies, copy credentials or automate through an undocumented authentication API.
2. Send the case prompt. Record the send timestamp immediately before submission.
3. Observe the **new assistant reply to that request**. Do not match sidebar text, the user's own text, an older reply, a read receipt, a spinner or an Agentverse outgoing-envelope log.
4. Record the first visible reply time and its exact text. Require the expected candidate (currently TrialFinder for the clinical-trials case) and a reply within 30 seconds.
5. If no reply is visible by the deadline, keep observing once beyond the deadline and save a screenshot. Record a failed case with null reply time/text. Never fill those fields with expected output or the local MCP result.
6. Save only the synthetic prompt, timestamps, candidate response text, observer type, screenshot reference and deployed commit. Keep private account UI screenshots outside Git.
7. Re-grade the evidence file. After a change, run the same case and compare it with the baseline.

The current failed observation waited 62.13 seconds. Agentverse logged inbound processing at 08:39:56.924 UTC and a reply at 08:39:59.197 UTC, about 2.3 seconds later. That outbound log is diagnostic evidence; the user still received no visible reply during the window. It is not evidence of successful ASI delivery, nor does it establish the cause of the missing reply.

## Readiness gate

`readiness` requires passing fixture, live MCP and visible ASI reports for the current commit. Fixture/MCP reports from an uncommitted tree fail. ASI evidence must identify the deployed commit, be no more than one hour old, and pass visible-response checks again. Missing reports, empty result sets, stale versions, generic help instead of a shortlist, late replies and no replies all keep readiness red. This command reports readiness; it does not deploy anything.

Delivery and discovery are the first gate. Do not add more target scoring features while this gate fails. Later eval sets should cover plan confirmation, real correlated target responses, timeout handling and the quality of assessments. Existing offline workflow tests remain useful but cannot substitute for those live outcomes.

## Automated suite and performance budgets

Every push now runs two separate GitHub Actions jobs (no scheduled runs):

- **Offline correctness and performance:** regression tests, the 15 discovery fixture cases, and six realistic service scenarios repeated 20 times each. Scenarios exercise profile-address parsing, name-based plans, saved state across turns, `start`, replay suppression, and an evidence report with a review checklist. No external target is contacted. The handler-only p95 budget is 250 ms per scenario; network time is excluded.
- **Live discovery:** the same 15 discovery cases against the public Stranger Loot MCP, requiring the expected candidate and a maximum of 30 seconds per case. The scorecard reports p50, p95 and maximum latency, including MCP initialization and network calls. Catalogue changes can cause genuine failures.

Pull requests run the offline job only. A manual **Run workflow** is also available. Reports appear in the Actions run summary and JSON/Markdown artifacts retained for 14 days, including failed evaluations. Concurrent pushes on the same ref cancel the older run. There are no automatic deployments, purchases, messages to other people's agents, or stored ASI account credentials.

Run locally:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python evals/performance.py --repeats 20 --budget-ms 250
.venv/bin/python evals/run.py --mode fixture
.venv/bin/python evals/run.py --mode mcp
```

Scenario requirements live in `evals/scenarios.json`. All 120 repetitions must satisfy their requirements; measured p50/p95 values are observations on that runner, not a load test or hosted speed guarantee. Synthetic target responses validate reporting only, not an actual target's competence. This automation does **not** verify hosted Agentverse delivery or visible ASI replies. Keep the existing visible ASI gate separate; green CI does not imply readiness.

The six scenario benchmarks also exercise automatic unique-match investigation, rules provenance and the three-check outbound request. Each repetition measures four local owner turns across the manual and automatic flows.

## Stranger Builds question exercise

Run `.venv/bin/python evals/rules_eval.py` for 12 curated questions covering job requirements, new repos/forks, counted hires, automated/owner trials, pending feedback, judging, deadline uncertainty, optional payments, team size and unknown prizes. Expected statements, prohibited claims and source provenance are checked. Every push runs this exercise and uploads `rules.json` / `rules.md`. Separate regression cases cover prompt injection and ensuring rules questions do not contact a target or search the catalogue. These are deterministic topic-based answers against the plugin snapshot, not a general-language reasoning evaluation or live rule verification.

## Agentverse native daily coverage

The native platform now retains 48 questions across three daily automation snapshots (20/20/8), including browse and investigation cases for all seven ASI-linked bots in the currently exposed public catalogue details. See [native suite, coverage and grading observations](agentverse/README.md). The initial expanded result was 45/48, with three evaluator/follow-up mismatches retained. Native CSV upload replaces the editable questions and caps at 20, so use the numbered batch files rather than the combined CSV. Native schedules are independent of every-push GitHub checks.
