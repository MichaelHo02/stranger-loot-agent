# Agentverse native question suite

Updated 8 November 2026 (Melbourne). `questions.csv` contains **48 unique cases**. The platform's CSV upload **replaces** the Questions tab and accepts at most **20** questions; it does not append. Do not upload the combined file directly. Import `batch-1.csv`, `batch-2.csv`, and `batch-3.csv` individually and save each as an automation snapshot.

## Saved daily automations

| Native automation | Questions | Daily time shown by Agentverse |
| --- | ---: | --- |
| Daily 1 - Rules and help | 20 | 09:00 |
| Daily 2 - Bot investigations | 20 | 09:15 |
| Daily 3 - Edge cases and vendor | 8 | 09:30 |

The browser's schedule form did not label a timezone, so the table records the displayed values without asserting a timezone. Each automation keeps its own questions even after the Questions tab changes. The current editable Questions tab holds the final 8-case batch; all 48 cases are retained across the three daily automation snapshots. Updating the editable tab does not synchronize the saved automations.

The user explicitly approved daily runs that contact the bots. All three snapshots were saved and their Run now actions were invoked for initial verification. Results are in native Runs. GitHub tests remain active separately.

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

The set also contains the original 12 rule cases, 12 paraphrases, help, recipient/case variations, refusal to fabricate feedback or hires, and unsupported-project cases. Native grading checks our tester's initial discovery/start/block response. It is not proof that all target agents replied, that their outputs were correct, or that the trial finished successfully. No votes, purchases, official feedback or counted hires are created by these tests.

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

No agent code was altered and no expected answers were relaxed to hide these results. Daily schedules remain active with these baseline failures visible. Do not use Build's automatic fix button merely to satisfy these mismatched evaluator suggestions.
