# Confirmed ASI first-turn parsing defect

Investigated 8 November 2026 in Melbourne.

## Captured cause

ASI's profile composer and its existing-chat composer use two different recipient representations in Chat Protocol TextContent:

```text
First profile message: @agent1<the tester's full address> Find a clinical trials agent
Later chat message:    @stranger-loot-tester Find a clinical trials agent
```

The UI displays the friendly handle for both. The original normalizer removed only the friendly handle. The actual first-turn address remained in the text, so a command was not recognized or the matcher required a project description to contain the tester's 65-character address. Consequently a valid clinical-trials search returned no matches. The same query in a later turn could work, obscuring the defect.

A controlled first-profile request with a unique synthetic marker captured the full-address prefix. The raw and normalized forms were identical before the fix. The incoming, acknowledgement and outgoing envelope sessions all matched that ASI chat, so this particular failure was not a mismatched-session failure. Repeated requests in an existing chat used the friendly handle and produced the correct TrialFinder shortlist.

## Fix

`normalize_user_text` accepts the actual `ctx.agent.address` and strips either our own leading handle or our own leading address. It does not strip other agents' addresses, similarly named handles, or mentions inside a test task. No general removal of mentions is used.

The handler-boundary regression failed before the fix: the command dispatcher received `@agent1... mcp tools` instead of `mcp tools`. It now receives the normalized command. The captured first-profile format is also part of the discovery outcome eval set.

## Scope of the conclusion

This establishes the first-turn parsing defect and its incorrect/absent useful discovery response. Earlier ASI read-receipt validation errors and transient missing UI responses are separate observations; this investigation does not claim those platform errors caused the parsing defect or that every historical missing reply has the same cause.

## Verification requirement

After the final clean deployment, run three profile-initiated chats. Each must show the actual TrialFinder assistant response within 30 seconds. Then select a numbered result in the same chat and observe a confirmation plan without an unsolicited test run. Per-run evidence, the deployed commit and UI timings are written to the ignored `.eval-results/` directory; old failed baselines remain preserved.

Temporary `[DEBUG-route-08]` diagnostics were limited to controlled commands and message/session IDs. They are removed from the final code.
