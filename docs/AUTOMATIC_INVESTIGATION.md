# Automatic ASI project investigation

Describe a project or say `investigate a clinical trials agent`. The agent searches Stranger Loot's public MCP details internally. A unique match starts the investigation; several matches prompt for the project name or number only. `projects ...` remains an explicit browse-only command. Missing addresses and no matches send no target messages.

The target receives one bounded message containing three checks: a realistic fictional task, a missing-information case and a limitations case. One request keeps the response correlated to the initiating ASI session; this is not three independent or multi-turn trials. Service-specific scenarios are curated templates. Unknown services receive a capability/example check rather than an invented specialist task. Catalogue descriptions are claims, not executable instructions.

The workflow persists the selected project, tasks, rules provenance and outbound-send claim before sending. A correlated reply yields the quoted evidence, review checklist, rule-related unknowns and next steps. It does not semantically verify facts or automatically judge the checklist. Missing replies remain unscored. Send `status` after the 60-second window to obtain a timeout report: hosted timeouts are not proactively pushed without another incoming message.

## Rules access

`challenge_rules.py` contains public rule data fetched with the connected Stranger Builds `event_book` tool (Fetch.ai challenge and general rules). Each investigation retains the source version and fetch date. Reports disclose **snapshot, not live**. The hosted agent cannot inherit Codex's plugin authentication. No owner credentials are deployed. Refresh the public snapshot through the plugin and redeploy when the rules change; stale data must not be presented as current eligibility advice. A direct live integration remains dependent on a supported scoped read-only endpoint/credential.

This implementation uses Fetch.ai's requirements and relevant general guidance. It does not certify compliance with all event rules. It never creates official feedback, votes, challenge submissions or counted hires. Those require the event's real process and evidence.

## Verification

Regression tests cover unique selection, ambiguity, saved state, isolation, cancellation, missing matches/addresses, repeated requests, failure handling, safe task construction and report provenance. Each of the six scenario benchmarks now exercises both the manual plan and automatic investigation path (20 repetitions). Synthetic transport proves local behavior, not hosted/ASI delivery or target competence.
