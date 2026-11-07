# Live ASI verification — 7 November 2026

Status: **partially verified; full ASI workflow remains unresolved**.

## Observed in ASI:One

- The public profile loads with the updated agent description, and a signed-in user can address Stranger Loot Tester.
- A synthetic request reached Agentverse. ASI includes the leading `@stranger-loot-tester` mention in Chat Protocol text.
- Before the mention fix, a clinical-trials search returned no matches even though the same live MCP query found TrialFinder.
- A help response was eventually visible in ASI, but delivery was substantially delayed. The corrected clinical-trials shortlist was not visible during this verification window.
- ASI's WebSocket stream included an `Invalid read payload` error: a `ControlReadPayload.event_id` contained an `optimistic:...:0` identifier rather than a UUID. This is an observed platform error, not proof that it caused the missing replies.
- A separate, benign connectivity request to TrialFinder through ASI also had no visible reply during the observation window. This does not establish that TrialFinder or ASI is broken.

## Bugs found and corrected

1. Remove only our own leading recipient mention before command parsing. Other mentions and task content remain intact.
2. Use Agentverse storage for shortlists, plans, test routes, reports and duplicate suppression. Controlled traces showed the same session UUID across messages while Python globals were reset. Wall-clock timestamps replace monotonic process-local timestamps for persisted retention.
3. Persist the test claim before sending so a replay cannot knowingly rerun an already claimed plan.
4. Handle target ChatMessage replies asynchronously. The hosted synchronous exchange returned immediately without a usable result, while a later envelope from the target was observed. New confirmed tests use `ctx.send`, then match incoming target replies by sender and session against stored plans. `status` reports an expired 60-second response window as blocked and unscored. No proactive timeout message is promised without a subsequent status check or reply.
5. Add the Chat Protocol completion marker used in Fetch.ai's [ASI-compatible example](https://innovationlab.fetch.ai/resources/docs/examples/chat-protocol/asi-compatible-uagents). This change did not by itself resolve ASI delivery.

Temporary diagnostic logging was removed. It was restricted to controlled synthetic requests or session/state counts; no credentials were logged.

## Verified through hosted Agentverse direct chat

- `Find a clinical trials agent` returned TrialFinder from the live public catalogue, including when prefixed with the ASI recipient mention.
- `test 1 | Briefly describe your service in one sentence. Do not run a patient search. | clinical` resolved the numbered shortlist and created a confirmation plan in a subsequent hosted invocation.
- Confirmation sent one Chat Protocol request to the published TrialFinder address. The agent reported waiting, with no premature score.
- A later `status` returned **BLOCKED — unscored** at 63.50 seconds: no usable target response was observed during the response window. No patient data, patient search or payment was involved.

This verifies the hosted discovery/selection/confirmation/timeout path. It does not establish a successful target assertion score or completion of the equivalent sequence in ASI. The automated suite covers scoring and reply correlation using controlled responses, including fresh runtime instances between turns.

## Remaining verification

Repeat the shortlist → selection → confirmation flow in ASI once replies can be delivered consistently. Confirm a real correlated target text response and its assertion score. Do not label the agent ASI end-to-end verified, or publish a target quality rating, based only on startup logs, automated fixtures or timeout results.
