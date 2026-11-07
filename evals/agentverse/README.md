# Agentverse native question suite

Updated 8 November 2026 (Melbourne). `questions.csv` contains **100 unique cases**. The platform's CSV upload **replaces** the Questions tab and accepts at most **20** questions; it does not append. Do not upload the combined file directly. Import `batch-1.csv` through `batch-5.csv` individually and save each as an automation snapshot.

## Saved daily automations

| Native automation | Questions | Daily time shown by Agentverse |
| --- | ---: | --- |
| Daily 1 - Rules and help | 20 | 09:00 |
| Daily 2v2 - Bot investigations | 20 | 09:15 |
| Daily 3v3 - Edge and rules | 20 | 09:30 |
| Daily 4 - Discovery variations | 20 | 09:45 |
| Daily 5 - Workflow boundaries | 20 | 10:00 |

The browser's schedule form did not label a timezone, so the table records the displayed values without asserting a timezone. Each automation keeps its own questions even after the Questions tab changes. The current editable Questions tab holds the final 20-case batch; all 100 cases are retained across the five daily automation snapshots. Updating the editable tab does not synchronize the saved automations.

The user explicitly approved daily runs that contact the bots. All five snapshots were saved. The first batch is unchanged and retains its 20/20 baseline; Run now was invoked for all four changed/new snapshots. Results are in native Runs. GitHub tests remain active separately.

## Bot coverage

`agent-coverage.json` records the public MCP inventory used for coverage. At capture, Stranger Loot indexed 210 projects but exposed only 40 detailed public entries. Seven of those had ASI/Agentverse links:

- Mori Together
- TradeJack (handle link only; no published Chat Protocol address in this snapshot)
- Blood Bridge
- TOOL OFFER AGENT
- TrialFinder
- Undo Department
- vendor_check

Each has one browse case and one investigation case. Six can initiate one chat-only request containing three checks. TradeJack must explain the missing address and send nothing; no address is guessed. This covers every ASI-linked bot in the available public details, not every bot among all 210 indexed projects.

The 100 cases retain the original 48 prompts and add 52 cases covering rule edge cases, uppercase and service-description lookup for each bot, fresh-chat controls, ambiguous browse queries, invalid targets, unsupported projects and prompt injection. Each case has an explicit expected answer; none was added with an empty rubric. Native grading can generate follow-up turns as well as assess the initial discovery/start/block response; expected answers must distinguish those stages. It is not proof that all target agents replied, that their outputs were correct, or that the trial finished successfully. No votes, purchases, official feedback or counted hires are created by these tests.

## Historical baseline

The original 15-case Generated Test completed on 8 November 2026 with 15/15 passed (100%). That result belongs to the original rules/help/browse-only set, not the expanded 48 cases. Keep later native results separate. Screenshot evidence is kept outside the public repository.

The addition-only export is retained for provenance, but because import replaces the list and caps at 20, use the numbered batch files instead. No automatic repository-to-Agentverse question sync is implemented.

## First expanded runs

All three **Run now** actions completed and the automation list showed:

- Daily 1: 20/20 passed (100%).
- Daily 2: 18/20 passed (90%), Needs attention.
- Daily 3: 7/8 passed (88% rounded), Needs attention.

Total: **45/48**. The seven named investigation cases passed the native initial-response grading; this does not establish that six remote agents completed their trials. TradeJack's expected outcome is no contact due to its missing public address.

Failures were inspected and retained:

- `projects Blood Bridge`: discovery returned the correct published profile and explicitly said its claims were unverified. The grader interpreted offering a later test as forbidden trial execution, although this browse reply itself sent no trial.
- `projects Undo Department`: the native evaluator subsequently issued `test 1`, supplied a custom task, then sent `start`. The agent followed that explicit confirmation. The grader assessed the resulting multi-turn conversation against the original browse-only expectation and failed it for sending a trial. The initial discovery and later authorized action must be evaluated separately in a future rubric revision.
- `WHAT CAN YOU DO?`: the capability reply was correct. The evaluator added an unlisted `DeFi Yield Aggregator` investigation request, received an honest no-match response, and failed it for not investigating that project. Catalogue coverage and capability/help expectations need separate grading.

No agent code was altered during the first expanded runs and the baseline failures were recorded before any grading correction. Do not use Build's automatic fix button merely to satisfy these mismatched evaluator suggestions.


## Corrected grading and 100-case expansion

The user authorized expected-answer clarification while preserving runtime behavior. Exactly three rubrics in the original 48 cases changed: `projects Blood Bridge`, `projects Undo Department`, and `WHAT CAN YOU DO?`. Prompts remain identical. `grading-corrections.json` preserves before/after text and `grading-corrections.csv` is a focused 3-case recheck export.

The corrected browse rubrics distinguish an optional offer from actual dispatch, and an initial browse request from a later explicit test/start instruction. Invented profiles, unsupported competence claims and sending an unrequested trial still fail. The help rubric requires a truthful capability answer, not a fabricated demonstration involving an unlisted project. The other 45 original expected answers remain unchanged.

Agentverse cannot edit the question snapshot inside an existing automation. Replacement snapshots Daily 2v2 and Daily 3v2 were created, and Daily 4 and Daily 5 added; Daily 3v3 later replaced Daily 3v2 after the focused help recheck; Daily 1 was retained unchanged. The two original superseded schedules, and subsequently the intermediate Daily 3v2 schedule, were removed with explicit user approval to avoid duplicate daily contacts. Observed platform behavior: removing them also removed their linked native runs from the run count. Their historical 18/20 and 7/8 results and inspected failures remain documented above, not claimed to remain in the native history.

The corrected and new runs must be assessed separately from the earlier 45/48 result. A larger set may expose new matching, capability or rules-answer gaps; do not silently relax those cases to preserve a score.


## 100-case first pass and focused corrections

The unchanged Daily 1 baseline remains 20/20. The four first expanded/corrected snapshots completed as follows:

| Snapshot | Native result |
| --- | --- |
| Daily 2v2 | 20/20 |
| Daily 3v2 (first help clarification) | 19/20 |
| Daily 4 | 17/20 |
| Daily 5 | 16/20 |

Together with the unchanged first batch this was **92/100**. Do not describe it as a fully passing 100-case run. The two original bot-browse mismatches passed after clarification. The remaining uppercase-help evaluator still judged its final fictional-project no-match response against the initial help answer. Its rubric was made explicit about two valid outcomes: a truthful capability answer, or a truthful capability answer followed by an honest no-match response to an unlisted project. A focused native `WHAT CAN YOU DO?` run then passed **1/1**. The runtime was not changed.

Daily 3v3 saves that final rubric into the full 20-case snapshot; its native verification is recorded separately below. Historical results from replaced schedules may disappear from Agentverse when their schedules are removed, so the earlier numbers above remain the audit record.

Seven additional first-pass failures remain in the expanded cases and were not waived:

- Daily 4: `projects budgeting assistant`, `status`, `confirm`.
- Daily 5: `test 0`, `test https://example.com | hello | hello`, `confirm nonexistent-token`, `projects blood`.

These need individual trace review before attributing them to runtime behavior versus the native evaluator's generated follow-ups. They are not the three original mismatches. The schedules continue to surface these failures; no claim of broad agent correctness or completed third-party trials follows from a native score.

## Final verified daily snapshots

Daily 3v3 completed **20/20 (100%)** after the final help-rubric clarification. The focused uppercase-help recheck also passed 1/1. The old Daily 3v2 was removed with explicit approval; its intermediate 19/20 result is retained in this document.

The final five saved daily snapshots and their latest completed results are:

| Snapshot | Latest result |
| --- | --- |
| Daily 1 - Rules and help (unchanged baseline) | 20/20 |
| Daily 2v2 - Bot investigations | 20/20 |
| Daily 3v3 - Edge and rules | 20/20 |
| Daily 4 - Discovery variations | 17/20 |
| Daily 5 - Workflow boundaries | 16/20 |

Total of the latest per-batch results: **93/100**, across separate runs (not one single 100-question run). All three original mismatches now pass. The seven additional cases listed above still need attention; their expected answers were not relaxed and the runtime remains unchanged. Exactly five automations remained in the native UI after cleanup, with 20 questions each. Screenshot evidence is outside Git at `/private/tmp/agentverse-100-questions-corrected.jpg`.
