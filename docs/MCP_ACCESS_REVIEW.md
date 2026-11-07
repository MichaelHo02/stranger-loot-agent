# Stranger Loot MCP access review

Observed 7 November 2026 against `https://stranger-loot.base44.app/api/mcp`, without a user token.

## Verified surface

Initialization reports a public, read-only server. `tools/list` advertises 13 `query_*` tools, each with a read-only annotation. No create, update, delete, report-saving, payment, browser, or external-agent messaging tool is exposed. A read-only annotation is descriptive; the server's permissions must enforce access.

| Data | Anonymous probe | Agent access |
| --- | --- | --- |
| PublicCatalogue | At least one visible row; public snapshots readable | Enabled, only `query_publiccatalogue` |
| ProjectAnalysisPreview | At least one visible ID | Not enabled |
| House | No rows returned | Not enabled |
| ProjectAnalysis, ProjectBenchmark, ProjectReview | No rows returned | Not enabled |
| Purchase, AnalystQuota, PassRecoveryRequest, PassRecoveryDelivery | No rows returned | Not enabled |
| ContactMessage, SiteVisit, SyncRun | No rows returned | Not enabled |

Probes requested only one `id` per entity, suppressing record contents. Zero visible rows can mean filtering or no records; it is not by itself proof of denial. The local Stranger Loot schemas independently declare admin-only reads for House, ProjectAnalysis, ProjectReview, Purchase, AnalystQuota, recovery records, visits, and sync runs. ContactMessage and ProjectBenchmark were listed live but were absent from the main checkout inspected for this review. This is an anonymous read-boundary review, not a complete authorization penetration test or a verification of every deployed rule.

## Public search coverage

`PublicCatalogue` contains multiple kinds of public snapshots. The agent previously used only `community-feeds`, whose gallery contained 24 of 121 entries. The `current` snapshot instead exposed 207 indexed project names and 40 detailed public projects during this review. Discovery now queries that `current` record and searches its `free` entries. It does not read `rest` entries or treat all indexed names as fully described/testable projects.

The public catalogue and public analysis previews have `read: true` in the local schemas: their publicly readable rows should contain only material intended for everyone. Any future fields added to those records must be treated as public too. A public preview is not access to a full paid analysis.

## What can have full access

- Public catalogue data can be searched anonymously to the extent the public snapshot actually contains it. The agent can resolve a published ASI/Agentverse address from that data.
- Public previews could be enabled as a separate reviewed, read-only source. They are currently excluded from the agent's tool allowlist.
- Testing another agent uses uAgents Chat Protocol directly. MCP does not execute those tests; discovery never starts one. The user's confirmed test plan authorizes the outbound message.

## What must remain restricted

- Purchases, emails, recovery information, quotas, visitor records and other internal records should not be exposed through this shared public agent.
- Full paid analyses must stay behind the app's entitlement checks. An anonymous MCP client must not be given an admin credential to bypass those checks.
- Saving a test report would need a dedicated authenticated, scoped tool that validates caller ownership, input and write permissions. No such write tool is currently advertised.
- If all 207 projects need descriptions and agent addresses in anonymous search, publish a deliberately sanitized public search index or read-only search tool. Do not make House or the full paid analysis entity publicly readable merely to fill discovery gaps.

No permissions or Stranger Loot app code were changed by this review. Private tool names remain advertised by the server even when anonymous results are empty; reducing that advertised surface is a separate server configuration improvement.
