# antares-web-mcp

[MCP](https://modelcontextprotocol.io) server exposing [Antares Web](https://github.com/AntaresSimulatorTeam/AntaREST)
to AI assistants (Claude Code, Claude Desktop, GitHub Copilot, ...).

It is a client of the Antares Web REST API and has its own environment, independent from the backend.

```bash
uv run antares-web-mcp --help
```

It also contains the agent of the Antares Web assistant (`/v1/assistant` endpoints) and a command-line
client for it:

```bash
uv run antares-assistant "Which studies do I have?"
```

See the full documentation in [`docs/mcp-server.md`](../docs/mcp-server.md).

## Development

```bash
uv sync
uv run pytest
uv run mypy
uv run ruff check && uv run ruff format --check
```
