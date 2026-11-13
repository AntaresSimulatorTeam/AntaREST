# MCP server (AI assistants)

Antares Web ships an [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server that lets
AI assistants such as **JetBrains AI** (PyCharm, IntelliJ IDEA), **GitHub Copilot** (VS Code agent
mode), **Claude Code** or **Claude Desktop**
explore and edit studies in natural language, e.g. *"In study Base case, create areas FR, DE and BE
and link them all together with DC links"*.

## How it works

```
AI assistant  ──MCP (stdio or HTTP)──▶  antares-web-mcp  ──REST + token──▶  Antares Web
(Claude, Copilot)                       (tools: list_studies, ...)          (/v1/studies/...)
```

The MCP server lives in the `mcp-server/` directory. It is a **separate Python package**
(`antares-web-mcp`) with its own dependencies and lock file, and it is a **client of the public
REST API**: it does not access the database or the study files, and every action is performed with
the permissions of the token it uses. It can thus target any Antares Web instance (local, desktop
or production) and never impacts the backend environment.

## What can be done

With the MCP server, an assistant can build a study from scratch, run it and analyse the results
in a single conversation, for instance:

> Create a study "Demo" with areas FR, DE and BE. Loads: 60 GW in FR, 70 GW in DE, 12 GW in BE,
> unsupplied energy cost 10000 €/MWh. Add 70 GW of nuclear at 15 €/MWh in FR, 60 GW of gas at
> 80 €/MWh and 20 GW of onshore wind in DE, 10 GW of gas at 85 €/MWh and a 1 GW / 4 GWh battery
> in BE. Link FR to DE and BE with 5 GW. Run 1 Monte-Carlo year, then give me the marginal price
> per country and tell me which links are congested.

## Available tools

**Studies**

| Tool                         | Description                                                    | Kind        |
|------------------------------|----------------------------------------------------------------|-------------|
| `list_studies`               | Find studies (filters: name, versions, tags...)                | read-only   |
| `get_study`                  | Metadata of one study                                          | read-only   |
| `describe_study`             | Areas, clusters, storages, links and outputs, in one call      | read-only   |
| `list_study_versions`        | Study versions that can be created                             | read-only   |
| `get_simulation_settings`    | Mode, Monte-Carlo years, simulated period...                   | read-only   |
| `create_study`               | Create an empty study                                          | write       |
| `import_study`               | Import a study from a local .zip / .7z archive                 | write       |
| `copy_study`                 | Copy a study (waits for the copy)                              | write       |
| `create_variant`             | Create a variant of a study                                    | write       |
| `update_simulation_settings` | Change mode, Monte-Carlo years, period...                      | write       |
| `delete_study`               | Delete a study (only with `--allow-study-deletion`)            | destructive |

**Network and input data**

| Tool                       | Description                                                        | Kind        |
|----------------------------|--------------------------------------------------------------------|-------------|
| `list_areas`, `list_links` | Areas and links of a study                                         | read-only   |
| `get_area_properties`      | Unsupplied / spilled energy costs of an area                       | read-only   |
| `list_clusters`            | Thermal, renewable clusters and storages of an area                | read-only   |
| `create_area`              | Create an area                                                     | write       |
| `update_area_properties`   | Set the unsupplied / spilled energy costs                          | write       |
| `set_area_load`            | Set, add to or scale the hourly load of an area                    | write       |
| `create_link`              | Create a link between two areas                                    | write       |
| `update_link`              | Update the properties of a link                                    | write       |
| `set_link_capacity`        | Set the transmission capacity (MW) of a link, in both directions   | write       |
| `create_thermal_cluster`   | Create a power plant, with its availability set to its capacity    | write       |
| `update_thermal_cluster`   | Change capacity, costs... (availability follows the capacity)      | write       |
| `create_renewable_cluster` | Create a wind / solar cluster with a constant production factor    | write       |
| `create_storage`           | Create a short-term storage (battery, pumped storage...)           | write       |
| `delete_area`              | Delete an area (and its links and clusters)                        | destructive |
| `delete_link`              | Delete a link                                                      | destructive |
| `delete_cluster`           | Delete a cluster or a storage                                      | destructive |

**Simulation and results**

| Tool                                   | Description                                                    | Kind        |
|----------------------------------------|----------------------------------------------------------------|-------------|
| `list_launchers`                       | Launchers and the solver versions they support                 | read-only   |
| `get_job`, `list_jobs`                 | Status of simulation jobs                                      | read-only   |
| `wait_for_job`                         | Wait for the end of a job, reporting its progress              | read-only   |
| `get_job_logs`                         | Last lines (or errors only) of the solver logs                 | read-only   |
| `list_outputs`                         | Simulation outputs of a study                                  | read-only   |
| `get_area_results`, `get_link_results` | Key indicators (prices, costs, unsupplied energy, flows...)    | read-only   |
| `get_storage_results`                  | Charge, discharge and level of each short-term storage         | read-only   |
| `launch_study`                         | Run a simulation (picks a compatible solver version)           | write       |
| `kill_job`                             | Stop a simulation                                              | destructive |

**Understanding a study (inputs)**

These tools explain what an existing study models and why it is set up that way. They return
summaries (patterns, totals, statistics) rather than raw matrices, so that the assistant can reason
on a whole industrial study (hundreds of objects, series of 8760 x 1000 values).

| Tool                             | Description                                                                 | Kind      |
|----------------------------------|-----------------------------------------------------------------------------|-----------|
| `get_study_context`              | Comments, lineage, variant changes, districts, files of `user/` and `logs/` | read-only |
| `get_study_configuration`        | All the settings: general, optimization, advanced, adequacy patch, playlist, thematic trimming | read-only |
| `describe_monte_carlo_scenarios` | Scenario builder explained: which series each year uses, what is drawn together, distinct years | read-only |
| `summarize_installed_capacity`   | Capacities by area and group (thermal, renewable, storages), disabled objects | read-only |
| `get_table`                      | Properties of all the objects of a kind (table mode), with filters          | read-only |
| `get_matrix_stats`               | Statistics of a time series (size, min/mean/max, annual sums, identical series) | read-only |
| `list_binding_constraints`       | Binding constraints written as equations, with their right-hand side paths  | read-only |
| `read_study_file`                | Text files (generation logs, notes), filtered by a regular expression       | read-only |
| `check_study`                    | Deterministic consistency checks (quick, or `deep` on the time series)      | read-only |

The MCP prompt **`analyse_study_inputs`** chains these tools into a report: what the study is for,
the deliberate settings, the modelled system, the modelling tricks (helper areas, availability
counters, conversion efficiencies...), the points of attention and the questions for the author.
In Claude Code, run it with `/mcp__antares-web__analyse_study_inputs <study name>`.

Rules of `check_study` (each finding is a *possible* issue, some are deliberate modelling choices):

| Rule                       | Detects                                                                              |
|----------------------------|--------------------------------------------------------------------------------------|
| `calendar`                 | 1 January weekday inconsistent with the horizon, or with a year in the study name    |
| `playlist`                 | Monte-Carlo years excluded by the playlist                                           |
| `thermal_min_stable_power` | Min stable power above the unit capacity                                             |
| `thermal_market_bid`       | Market bid below the marginal cost                                                   |
| `unsupplied_energy_cost`   | Unsupplied energy cost below the most expensive plant, or equal to 0                 |
| `storage_efficiency`       | Storage efficiencies above 1                                                         |
| `disabled_objects`         | Disabled clusters, storages, constraints; enabled ones without capacity              |
| `isolated_areas`           | Areas without any link                                                               |
| `constraint_references`    | Binding constraint terms on missing or disabled objects                              |
| `relaxable_helper_terms`   | Constraints relaxed by lowering a free, optional helper production (never binding)   |
| `hydro_generation_power`*  | Hydro inflows without generating power, in the file the solver reads (`hydro-pmax`)  |
| `thermal_availability`*    | Null availability, or availability above the installed capacity                      |
| `renewable_series`*        | Null series, production factors outside [0, 1]                                       |
| `link_capacities`*         | Links with 0 MW in both directions                                                   |
| `scenarised_constraints`*  | Scenarised constraints whose right-hand side columns are all identical               |

\* deep rules (`deep=true`): they download the time series, about 1.5 minutes for a European study
of 78 areas and 900 clusters. Progress is reported to the client while they run.

Start the server with `--read-only` (or `ANTARES_MCP_READ_ONLY=true`) to expose read-only tools only.

### Built-in Antares know-how

Some tools do more than calling one endpoint, to hide Antares pitfalls from the assistant:

- `create_thermal_cluster` sets the hourly availability to the installed capacity (a cluster created
  through the API has a null availability and would produce nothing), and the market bid to the
  marginal cost (it defaults to 0, i.e. a free plant in the merit order).
- `set_link_capacity` is needed because a new link has a 0 MW capacity; it handles the alphabetical
  storage order of links (direct / indirect capacities).
- `launch_study` picks the study version if the launcher supports it, else the closest higher one.
- `get_area_results` downloads the aggregated output (a CSV with more than a hundred columns) and
  only returns the requested indicators, as a compact table.

## Configuration

| Option / environment variable                      | Default                 | Description                                      |
|----------------------------------------------------|-------------------------|--------------------------------------------------|
| `--url` / `ANTARES_WEB_URL`                        | `http://localhost:8080` | Root URL of Antares Web                          |
| `--token` / `ANTARES_WEB_TOKEN`                    |                         | Bearer token, not needed if security is disabled |
| `--read-only` / `ANTARES_MCP_READ_ONLY`            | `false`                 | Only expose read-only tools                      |
| `--allow-study-deletion` / `ANTARES_MCP_ALLOW_STUDY_DELETION` | `false`      | Expose the `delete_study` tool                   |
| `--no-verify-ssl` / `ANTARES_WEB_VERIFY_SSL=false` | verify                  | Skip TLS certificate verification                |
| `--timeout` / `ANTARES_WEB_TIMEOUT`                | `60`                    | HTTP timeout (seconds)                           |
| `--transport` / `ANTARES_MCP_TRANSPORT`            | `stdio`                 | `stdio` or `streamable-http`                     |

**Token**: create a *bot token* in Antares Web (*Settings > Tokens*), with the smallest set of
permissions you need. Bot tokens can be revoked at any time.

## Setup

Only [uv](https://docs.astral.sh/uv/) is required: it installs Python and the dependencies on the fly.

### Claude Code

The repository provides a `.mcp.json` file: start Claude Code **at the repository root** (the
server command is relative to it) and approve the `antares-web` server. Set `ANTARES_WEB_URL` / `ANTARES_WEB_TOKEN` in your shell to target
another instance. Check the connection with `/mcp`.

### GitHub Copilot (VS Code)

The repository provides `.vscode/mcp.json`: open the *Chat* view in **Agent** mode, start the
`antares-web` server (VS Code prompts for the URL and the token), then enable its tools from the
tools menu.

### JetBrains AI (PyCharm, IntelliJ IDEA)

In *Settings | Tools | AI Assistant | Model Context Protocol (MCP)*, click **Add**, choose **STDIO**
and paste:

```json
{
  "mcpServers": {
    "antares-web": {
      "command": "uv",
      "args": ["run", "--directory", "mcp-server", "antares-web-mcp", "--url", "http://localhost:8080"]
    }
  }
}
```

Set **Working directory** to the repository root, choose the **Server level** (project or global),
then click **OK** and **Apply**. The *Status* column shows the connection; click its icon to list
the tools.

- Pass the options as arguments (`--url`, `--token`, `--read-only`...): the JetBrains configuration
  format only documents `command` and `args`.
- If the IDE was not started from a shell, `uv` may not be on its `PATH`: use its absolute path
  (`which uv`).
- A token passed with `--token` is stored in the IDE settings and visible in the process list: use a
  dedicated bot token with minimal permissions.

### Without cloning the repository

Any MCP client can run the server straight from GitHub:

```bash
uvx --from "git+https://github.com/AntaresSimulatorTeam/AntaREST#subdirectory=mcp-server" antares-web-mcp
```

For instance, in Claude Desktop (`claude_desktop_config.json`) or in another project's `.mcp.json`:

```json
{
  "mcpServers": {
    "antares-web": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/AntaresSimulatorTeam/AntaREST#subdirectory=mcp-server", "antares-web-mcp"],
      "env": { "ANTARES_WEB_URL": "https://antares-web.example.com", "ANTARES_WEB_TOKEN": "<bot token>" }
    }
  }
}
```

### Shared HTTP server

The server can also run as a long-lived HTTP service (endpoint `/mcp`):

```bash
uv run --directory mcp-server antares-web-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

!!! warning
    In this mode, every MCP client reaching the port acts with the server token: do not expose it
    outside a trusted network without an authenticating reverse proxy.

## Assistant endpoint (experimental)

Antares Web can also answer questions itself, without any AI client on the user side: the
`/v1/assistant` endpoints run an AI agent which uses the same MCP tools.

```
User (CLI, UI, curl) ──▶ POST /v1/assistant/chat ──▶ agent process ──▶ model API (API key of the server)
                         (Antares Web backend)        │
                                                      └─ MCP tools ──REST, token of the user──▶ Antares Web
```

- The **agent** lives in the `mcp-server` package (`antares_web_mcp.assistant`). The backend starts it
  as a separate process for each request (`uv run antares-web-assistant`), so the model and MCP SDKs
  never enter the backend environment, and a stuck answer is killed after `assistant.timeout` seconds.
- The agent calls the REST API **with the token of the caller**: the permissions of the user apply.
- It is **read-only by default**: it cannot modify studies nor launch simulations.
- The **API key stays on the server**. It is passed to the agent through its environment, never
  through the command line nor the request.

!!! warning
    The content of the studies read by the tools is sent to the model provider. Check your data
    policy before enabling the assistant on a server which hosts sensitive studies.

### Assistant configuration

In the configuration file of the server (`application.yaml`):

```yaml
assistant:
  # Leave empty to use the ANTHROPIC_API_KEY environment variable of the server. Never commit a key.
  anthropic_api_key: "sk-ant-..."
  read_only: true            # false: the assistant can also modify studies and launch simulations
  # enabled: true
  # model: claude-opus-5-5   # default model of the provider
  # effort: medium           # low | medium | high | xhigh | max
  # timeout: 900             # maximum duration of one answer, in seconds
  # max_tool_rounds: 40
  # antares_url: ""          # URL used by the agent to call the server; default http://127.0.0.1:<port>
  # command: []              # command of the agent; default `uv run antares-web-assistant` in mcp-server/
```

`uv` must be installed on the server. `GET /v1/assistant` tells whether the assistant is available,
and why if it is not.

### Endpoints

| Endpoint                         | Description                                                             |
|----------------------------------|-------------------------------------------------------------------------|
| `GET /v1/assistant`              | Status: `available`, `reason`, `provider`, `model`, `read_only`         |
| `POST /v1/assistant/chat`        | Ask a question; returns the answer, the tool calls made and a `history` |
| `POST /v1/assistant/chat/stream` | Same, as a stream of JSON lines to follow the progress of the agent     |
| `POST /v1/assistant/studies/{study_id}/check` | Check a study (`check_study` with the time series, then an explanation of the findings), as a stream of JSON lines. Query parameter: `language` (`en` or `fr`) |

```bash
curl -X POST http://localhost:8080/v1/assistant/chat -H "Content-Type: application/json" \
  -d '{"message": "What is this study for? Any inconsistency?", "study_id": "<study id>"}'
```

To continue a conversation, send back the `history` of the previous answer, unchanged, with the next
`message`. The server keeps no conversation state.

Events of the streams (one JSON object per line): `tool_call` (`name`, `input`), `tool_progress`
(`name`, `progress`, `total`, `message`, for long tools), `tool_result` (`name`, `is_error`,
`duration_s`, `content`), `text` (progress note), then `done` (`answer`, `history`, `usage`...) or
`error` (`message`).

### In the web interface

When the assistant is available, the header of a study shows a **Check study** button. It calls the
check endpoint and opens a panel with:

- the progress: a percentage while the rules run on the time series (the only step whose duration
  can be predicted), an indeterminate bar while the assistant starts and writes;
- the findings of the rules, by severity, as soon as the rules have run;
- then the analysis written by the assistant.

The result stays available from the button (with the number of errors and warnings) as long as the
user stays on the study.

### Command-line client

```bash
cd mcp-server
uv run antares-assistant "Which studies do I have?"
uv run antares-assistant --study <study id> "Check this study and explain each finding."
uv run antares-assistant                      # interactive conversation
```

Options: `--url` (default `http://localhost:8080`, or `ANTARES_WEB_URL`), `--token` (or
`ANTARES_WEB_TOKEN`). The client only talks to Antares Web: it needs no API key.

### Using another model provider

Only `mcp-server/src/antares_web_mcp/assistant/anthropic_provider.py` depends on a vendor. To use
another one, implement the `ChatProvider` protocol (`provider.py`: one `run_turn` method running the
tool loop in the vendor's message format), register it in `providers.py` with the environment
variable of its key, and set `assistant.provider`. The endpoint, the agent and the tools do not change.

## Development and tests

```bash
cd mcp-server
uv sync
uv run pytest
uv run mypy
uv run ruff check && uv run ruff format --check
```

The tests use an in-memory MCP client and a fake Antares Web (`httpx2.MockTransport`): no server
is needed. The backend test `tests/test_mcp_server_contract.py` checks that the enum values
duplicated in `mcp-server/src/antares_web_mcp/enums.py` stay in sync with the backend.

To try the tools interactively without an AI assistant, use the MCP Inspector (requires Node.js):

```bash
npx @modelcontextprotocol/inspector uv run --directory mcp-server antares-web-mcp
```

### Adding a tool

1. Add the REST call to `AntaresWebClient` (`mcp-server/src/antares_web_mcp/client.py`).
2. Declare the tool in the `register()` function of the right module of
   `mcp-server/src/antares_web_mcp/tools/` (studies, network, inputs, simulation, results, analysis),
   with an explicit docstring, described parameters (`Annotated[..., Field(description=...)]`) and the
   right `ToolAnnotations` (read-only, destructive...). These descriptions are what the model reads.
3. Register write tools after the `read_only` early return.
4. Add a test in the matching `mcp-server/tests/test_<module>.py`, and add the tool to the lists of
   `tests/test_server.py`.

To add a consistency rule, write a `check_<rule>` function in `tools/checks.py` (a quick rule takes
the `StudyData` loaded once, a deep rule also gets a `MatrixReader`), add it to `QUICK_CHECKS` /
`QUICK_RULES` (or the deep lists) and test it in `tests/test_checks.py` without any server.
