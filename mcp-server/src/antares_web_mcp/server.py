# Copyright (c) 2026, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

"""
MCP (Model Context Protocol) server exposing Antares Web to AI assistants
(Claude Code, Claude Desktop, GitHub Copilot, ...).

Tools are grouped by domain in ``antares_web_mcp.tools``. Tool docstrings and parameter
descriptions are what the AI model reads to decide which tool to call and how: they are part
of the product, keep them precise. ``INSTRUCTIONS`` gives the model the big picture.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version

from mcp.server.mcpserver import MCPServer

from antares_web_mcp import prompts
from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.tools import analysis, checks, diagnosis, inputs, network, results, simulation, studies

SERVER_NAME = "antares-web"

INSTRUCTIONS = """\
Tools to build, run and analyse Antares Simulator studies (power system models) hosted on an
Antares Web server.

Concepts: a study contains areas (network nodes, with a load) connected by links (with a
transmission capacity). Areas contain thermal clusters (power plants), renewable clusters
(wind, solar) and short-term storages. A simulation (job) produces an output with results.

Find and inspect: `list_studies` gives study ids (UUIDs); `describe_study` gives the whole
content of a study in one call. Areas are referenced by their *id* (the lower-case normalized
name, e.g. "Île-de-France" -> "ile-de-france").

Build a study from scratch, in this order:
1. `create_study` (pick a version supported by a launcher, see `list_launchers`).
2. `create_area` for each area, then `set_area_load` and `update_area_properties`
   (set an unsupplied energy cost, e.g. 10000 EUR/MWh, otherwise marginal prices are meaningless).
3. Generation: `create_thermal_cluster`, `create_renewable_cluster`, `create_storage`.
4. Interconnections: `create_link`, then `set_link_capacity` (a new link has a 0 MW capacity).
5. `update_simulation_settings` (e.g. 1 Monte-Carlo year for a quick test).

Run and analyse:
6. `launch_study`, then `wait_for_job`. If the job failed, call `diagnose_job` for its probable causes
   (then `get_job_logs` to read more of the solver logs).
7. `get_area_results` / `get_link_results` with the output id of the job.

Understand an existing study (inputs), read-only:
- `get_study_context` (comments, lineage, variant changes, `user/` and `logs/` files, see
  `read_study_file`), `get_study_configuration`, `describe_monte_carlo_scenarios`,
  `summarize_installed_capacity`, `list_binding_constraints`, then `check_study` (deep=true to also
  check the time series). Dig with `get_table` and `get_matrix_stats` (never ask for raw matrices).
  The prompt `analyse_study_inputs` chains all of this into a report.
- Settings that differ from the defaults are deliberate choices: explain what each one implies.
- Large studies use modelling tricks, often in helper (virtual) areas named with a prefix such as
  v_, w_, y_, z_: a flat load with a 0 unsupplied energy cost is an optional consumption (a sink:
  electrolysers, power-to-heat); a copy of a fleet at zero cost in an isolated area is an
  availability counter for binding constraints; an "equal" constraint between flows with a
  fractional weight is a conversion efficiency (e.g. electricity to hydrogen); expensive thermal
  clusters in helper areas are alternatives (boilers, imports) or demand response.

Notes:
- To compare alternatives, prefer `create_variant`: changes are recorded on top of the parent study.
- A link is undirected and stored with its area ids in alphabetical order (`area1` < `area2`).
- Archived studies cannot be modified. Ask the user before any destructive operation.
"""


def create_server(
    client: AntaresWebClient, *, read_only: bool = False, allow_study_deletion: bool = False
) -> MCPServer:
    """
    Builds the MCP server.

    Args:
        client: Client used to call the Antares Web REST API. It is closed when the server stops.
        read_only: If ``True``, only tools that do not modify anything are registered.
        allow_study_deletion: If ``True`` (and not read-only), the `delete_study` tool is registered.
    """

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await client.aclose()

    mcp = MCPServer(
        name=SERVER_NAME,
        title="Antares Web",
        instructions=INSTRUCTIONS,
        version=version("antares-web-mcp"),
        lifespan=lifespan,
    )
    studies.register(mcp, client, read_only=read_only, allow_study_deletion=allow_study_deletion)
    network.register(mcp, client, read_only=read_only)
    inputs.register(mcp, client, read_only=read_only)
    simulation.register(mcp, client, read_only=read_only)
    results.register(mcp, client, read_only=read_only)
    analysis.register(mcp, client)
    checks.register(mcp, client)
    diagnosis.register(mcp, client)
    prompts.register(mcp)
    return mcp
