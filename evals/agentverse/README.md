# Agentverse native question suite

`questions.csv` is the 15-case import for the hosted Stranger Loot Tester agent's **Testing → Questions** page. It contains the 12 rules questions, the agent overview, browse-only clinical discovery and honest handling of missing nail-agent coverage. Expected answers describe required meaning and limitations; native grading is separate from our deterministic GitHub gates.

Imported on 8 November 2026 (Melbourne). The user selected **manual runs initially**. Agentverse's Automations UI offers Daily or Weekly only, so no scheduled automation was created. Run the selected questions with **Run Test**; results appear in **Runs**. Existing manual chat histories are not evidence that this 15-question evaluation passed.

These prompts do not initiate trials against other builders' agents. They do not cast votes or claim official feedback. GitHub Actions remains the source for regression tests, handler timing and live MCP discovery checks. No automatic synchronization from the repository to Agentverse's Questions tab is implemented: import the CSV again when the native question set changes, and review for duplicates first.

First native **Generated Test** run completed on 8 November 2026: **15/15 passed, 100%, Passed / All checks passed** in Agentverse's Runs UI. The question detail showed the actual hosted reply and the platform's grading explanation. This is the platform's assessment of this curated question set, not a guarantee of general correctness, live rules freshness, visible ASI delivery or successful trials against third-party agents. Screenshot evidence is kept outside the public repository.
