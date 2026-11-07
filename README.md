# Stranger Loot Tester

Find ASI/Agentverse projects in Stranger Loot and run a confirmed, single-message Chat Protocol test of another agent. Suggested scenarios produce an evidence report and a review checklist. They do not assign an automatic quality score.

## Features

- Describe an agent, such as `find a nail appointment agent`, `find a clinical trials agent`, or `an agent that helps with my money`. The agent searches Stranger Loot MCP and returns up to five ASI/Agentverse candidates.
- `projects` or `projects <search words>` also searches the same public catalogue.
- Choose a candidate with `test 1`. Supported service categories receive a realistic fictional scenario and review checklist; unknown services ask for your task instead of inventing one. Plans and reports use the catalogue name.
- Custom checks remain available: `test 1 | <fictional task> | <expected text>`.
- `test <agent1 address or ASI/Agentverse profile link> | <fictional task> | <expected text>`: prepare a test plan.
- `start` (also `yes` or `confirm`): send the pending task once. Internal identifiers stay out of chat instructions. Legacy `confirm <plan token>` remains supported.
- `status`: retrieve the report or check a pending test. After its 60-second response window, a status check reports the test as blocked and unscored.
- `cancel`: discard a pending plan without sending a test.
- `mcp tools`: check the read-only catalogue connection.

A plan explains its target, exact input and review criteria before execution. Plans expire after five minutes and can only be confirmed by their creator in the same chat session. Use fictional, non-sensitive inputs and ask the target only for a reply. The target controls its own behavior.

The test uses the Agent Chat Protocol, accepting only a ChatMessage from the target in the matching session. An acknowledgement is not a test result. Target output is displayed as untrusted evidence and never executed as a command. Duplicate incoming messages and recent late target responses are suppressed.

## Assessment

Suggested scenarios cover clinical trials, nail appointments, budgets, travel, social meetups and beginner study help. These are curated templates chosen using the public catalogue name and description, not a general scenario generator. They request substantive outputs with constraints and prohibit booking/contact/payment where relevant. Clinical examples use fictional profiles and do not establish medical eligibility.

A suggested test reports the exact reply, response time and service-specific review checklist. The checklist is **not automatically judged**: receiving a reply is not a quality pass. There is no numerical quality score.

Custom expected-text checks report **PASS** or **FAIL** for that phrase only, without a 100/100 score. Echoing the phrase can still pass; this does not establish factual correctness, safety, consistency or usefulness. Unusable, oversized or missing replies are blocked and unscored. No semantic or LLM judging is implemented.

## Limitations

Only ASI/Agentverse chat agents are test targets. There is no website/browser testing, purchasing, payment integration, automatic benchmark suite, or report saving. Only the first text response is assessed; multi-message/streamed answers may be incomplete.

Discovery reads the `current` public catalogue exposed by Stranger Loot MCP. It searches detailed `free` entries, which may cover only part of the indexed directory; each response states its coverage and update time. It never uses locked/rest entries. Matching uses keywords, a small related-term vocabulary and typo tolerance, not general semantic or LLM ranking. A vague description can have no match.

Candidates need a published ASI/Agentverse link. A handle-only ASI link can appear in the shortlist, but cannot be tested until its actual Chat Protocol address is published; no address is guessed. Numbered choices expire after five minutes and are isolated by sender and chat session. Choosing a result only creates a plan; it never sends a test before confirmation. A new search does not alter an already prepared plan. Direct addresses and profile links remain supported.

One test is allowed per chat session during a 15-minute in-memory retention window, preventing reuse of a response session for a second test. Start a new chat for another run. Workflow state and duplicate suppression use Agentverse storage because hosted Python globals reset between messages. State uses wall-clock timestamps so retention survives separate runtimes. Stale entries expire through normal retention. Maximum 100 retained plans and 2000 recent incoming message identifiers per process.

## MCP connection

Default: https://stranger-loot.base44.app/api/mcp

Optionally override `STRANGER_LOOT_MCP_URL` with a trusted HTTPS endpoint in Agentverse environment configuration. No credentials are needed for the current public server. See [the MCP access review](docs/MCP_ACCESS_REVIEW.md) for verified anonymous visibility and access limits. The client initializes MCP, discovers tools, and only calls the reviewed `query_publiccatalogue` tool with its read-only annotation. Payment, contact, recovery, and private entity tools are excluded.

## Development and automated verification

See [outcome evaluations](evals/README.md) for repeatable fixture, live MCP and visible ASI checks. Passing unit tests alone does not establish that the agent works in ASI. The historical failed ASI baseline is retained; current verification must be run against the deployed commit.

Python 3.10–3.12; uAgents 0.26.1 or later. Run:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python 'uagents==0.26.1'
.venv/bin/python -m unittest discover -s tests -v
```

Tests cover plan confirmation, ownership/session isolation, expiration, cancellation, replay and concurrent-confirmation protection, scoring, timeouts, oversized responses, discovery scope, and real uAgents dispatcher correlation. They use controlled responses and make no calls to other people's agents. GitHub Actions runs them on pushes and pull requests, together with six realistic scenario benchmarks (20 repetitions each). Pushes also run live read-only MCP discovery and publish latency scorecards; there is no daily schedule. See [automation and performance budgets](evals/README.md#automated-suite-and-performance-budgets). These checks do not establish successful live delivery to a third-party agent.

Work and push directly on `main` (see `AGENTS.md`). Keep `.env`, credentials and `.avctl/` local. Agentverse manages identity. Deploy with `avctl hosting deploy`, then inspect `avctl hosting logs`. GitHub pushes do not update Agentverse.

## ASI compatibility

ASI prefixes text with the recipient mention. The first profile message uses the full agent address, while later turns use `@stranger-loot-tester`. The handler removes either of its own leading mentions. See [the captured first-turn root cause](docs/ASI_FIRST_TURN_ROOT_CAUSE.md). Replies include the Chat Protocol completion marker. Test replies are handled asynchronously in separate hosted invocations, matched by target address and session, and delivered to the original requester. A timeout without a subsequent message is not proactively announced; send `status` to check it.
