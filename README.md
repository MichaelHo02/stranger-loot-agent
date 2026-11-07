# Stranger Loot Tester

Find ASI/Agentverse projects in Stranger Loot and run a confirmed, single-message Chat Protocol test of another agent. This first version gives an evidence-backed **assertion score**, not a general quality ranking.

## Features

- Describe an agent, such as `find a nail appointment agent`, `find a clinical trials agent`, or `an agent that helps with my money`. The agent searches Stranger Loot MCP and returns up to five ASI/Agentverse candidates.
- `projects` or `projects <search words>` also searches the same public catalogue.
- Choose a candidate with `test 1 | <fictional task> | <expected text>`. The number is resolved from your latest shortlist in this chat; there is no need to copy an agent address.
- `test <agent1 address or ASI/Agentverse profile link> | <fictional task> | <expected text>`: prepare a test plan.
- `confirm <plan token>`: send the exact task once. A correlated target reply produces an evidence report.
- `status`: retrieve the report or check a pending test. After its 60-second response window, a status check reports the test as blocked and unscored.
- `cancel`: discard a pending plan without sending a test.
- `mcp tools`: check the read-only catalogue connection.

A plan explains its target, exact input, expected substring and scoring before execution. Plans expire after five minutes and can only be confirmed by their creator in the same chat session. Use fictional, non-sensitive inputs and ask the target only for a reply. The target controls its own behavior.

The test uses the Agent Chat Protocol, accepting only a ChatMessage from the target in the matching session. An acknowledgement is not a test result. Target output is displayed as untrusted evidence and never executed as a command. Duplicate incoming messages and recent late target responses are suppressed.

## Scoring

- **100/100**: the actual response contains the agreed expected text, case-insensitive.
- **0/100**: a text response arrived but did not contain it.
- **Blocked, unscored**: no usable reply, transport error, timeout, non-text reply, or more than 6000 characters.

This is one text-containment assertion. A response that merely echoes the expected text can pass. It does not establish factual correctness, safety, consistency, or overall usefulness. No semantic or LLM judging is implemented. Every report includes the exact input, expected text, observed output when usable, elapsed time, and limitations.

## Limitations

Only ASI/Agentverse chat agents are test targets. There is no website/browser testing, purchasing, payment integration, automatic benchmark suite, or report saving. Only the first text response is assessed; multi-message/streamed answers may be incomplete.

Discovery reads the `current` public catalogue exposed by Stranger Loot MCP. It searches detailed `free` entries, which may cover only part of the indexed directory; each response states its coverage and update time. It never uses locked/rest entries. Matching uses keywords, a small related-term vocabulary and typo tolerance, not general semantic or LLM ranking. A vague description can have no match.

Candidates need a published ASI/Agentverse link. A handle-only ASI link can appear in the shortlist, but cannot be tested until its actual Chat Protocol address is published; no address is guessed. Numbered choices expire after five minutes and are isolated by sender and chat session. Choosing a result only creates a plan; it never sends a test before confirmation. A new search does not alter an already prepared plan. Direct addresses and profile links remain supported.

One test is allowed per chat session during a 15-minute in-memory retention window, preventing reuse of a response session for a second test. Start a new chat for another run. Workflow state and duplicate suppression use Agentverse storage because hosted Python globals reset between messages. State uses wall-clock timestamps so retention survives separate runtimes. Stale entries expire through normal retention. Maximum 100 retained plans and 2000 recent incoming message identifiers per process.

## MCP connection

Default: https://stranger-loot.base44.app/api/mcp

Optionally override `STRANGER_LOOT_MCP_URL` with a trusted HTTPS endpoint in Agentverse environment configuration. No credentials are needed for the current public server. See [the MCP access review](docs/MCP_ACCESS_REVIEW.md) for verified anonymous visibility and access limits. The client initializes MCP, discovers tools, and only calls the reviewed `query_publiccatalogue` tool with its read-only annotation. Payment, contact, recovery, and private entity tools are excluded.

## Development and automated verification

See [outcome evaluations](evals/README.md) for repeatable fixture, live MCP and visible ASI checks. Passing unit tests alone does not establish that the agent works in ASI. The readiness gate currently fails the recorded ASI delivery baseline.

Python 3.10–3.12; uAgents 0.26.1 or later. Run:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python 'uagents==0.26.1'
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover plan confirmation, ownership/session isolation, expiration, cancellation, replay and concurrent-confirmation protection, scoring, timeouts, oversized responses, discovery scope, and real uAgents dispatcher correlation. They use controlled responses and make no calls to other people's agents. GitHub Actions runs them on pushes and pull requests. These checks do not establish successful live delivery to a third-party agent.

Work and push directly on `main` (see `AGENTS.md`). Keep `.env`, credentials and `.avctl/` local. Agentverse manages identity. Deploy with `avctl hosting deploy`, then inspect `avctl hosting logs`. GitHub pushes do not update Agentverse.

## ASI compatibility

ASI prefixes text with the recipient mention. The first profile message uses the full agent address, while later turns use `@stranger-loot-tester`. The handler removes either of its own leading mentions. See [the captured first-turn root cause](docs/ASI_FIRST_TURN_ROOT_CAUSE.md). Replies include the Chat Protocol completion marker. Test replies are handled asynchronously in separate hosted invocations, matched by target address and session, and delivered to the original requester. A timeout without a subsequent message is not proactively announced; send `status` to check it.
