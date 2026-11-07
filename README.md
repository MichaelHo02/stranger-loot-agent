# Stranger Loot Tester

An Agentverse hosted agent that reads the Stranger Loot public project catalogue through MCP. Uses the Agent Chat Protocol with acknowledgements and a published manifest.

## Try it

- `mcp tools` — connect and discover the enabled public catalogue tool.
- `projects` — show up to five projects from the public snapshot.
- `projects agent` — search project names and descriptions.

## MCP connection

Default endpoint: https://stranger-loot.base44.app/api/mcp

Optionally set `STRANGER_LOOT_MCP_URL` in Agentverse environment configuration to override the endpoint with another trusted HTTPS server. No credentials are needed for the current public endpoint.

The client initializes MCP, discovers tools, and only permits `query_publiccatalogue` with its read-only annotation. It reads the `community-feeds` gallery snapshot. Payment, recovery, contact, and other entity tools are not enabled. No writes, paid reports, agent testing, or payments are implemented.

Requests have a 15-second socket timeout and a 4 MiB response limit. Commands are limited to 500 characters; results include at most five projects. Network calls run off the chat event loop. Failures return a safe availability message without server details.

Catalogue content is third-party data: descriptions are unverified claims, not evidence that the advertised functionality was tested. Results include the snapshot timestamp.

## Development

Python 3.10–3.12, with dependencies from `pyproject.toml`. Agentverse manages agent identity; do not configure a seed, mailbox or local endpoint.

Work and push directly on `main`, as recorded in `AGENTS.md`. Keep `.env` and `.avctl/` local. Deploy from this directory using `avctl hosting deploy`, then inspect `avctl hosting logs`. A GitHub push alone does not update Agentverse.
