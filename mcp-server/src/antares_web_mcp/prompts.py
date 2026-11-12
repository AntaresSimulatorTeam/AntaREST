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
MCP prompts: reusable workflows that MCP clients show as commands (e.g. `/mcp__antares-web__...`
in Claude Code, `/` commands in GitHub Copilot chat).
"""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

ANALYSE_STUDY_INPUTS = """\
Analyse the inputs of the Antares study "{study}": explain what it models, why it is set up that way,
and what may be inconsistent. Do not launch any simulation and do not modify anything.

Collect the facts (read-only tools):
1. If you were given a name, find the study id with `list_studies`. Then call `get_study_context`:
   comments, lineage, variant changes (the hypothesis of a variant), districts, files of `user/` and
   `logs/`. If a generation log exists, read it with `read_study_file` (pattern such as
   "scenario|warning|not exist|error|read from|activated", distinct=true): it often names the
   source data and the scenario.
2. `get_study_configuration` and `describe_monte_carlo_scenarios`: Monte-Carlo design, calendar,
   adequacy patch, optimization preferences, output variables kept.
3. `describe_study`, `summarize_installed_capacity`, and `get_table` for the areas (unsupplied
   energy costs, adequacy patch modes, year-by-year outputs) and the links.
4. `list_binding_constraints`, then `get_matrix_stats` on the right-hand sides of the key constraints
   and on the load of the main areas (annual energy = column_sums, peak = max).
5. `check_study` with deep=true.

Find the focus of the author: areas with year-by-year outputs, districts, names of the files in `user/`.
Recognise the modelling tricks (helper areas, availability counters, conversion efficiencies, sinks).

Write the report in the language of the user, with these sections:
- In one sentence: what the study models and what it is for.
- Settings and why: the deliberate choices (Monte-Carlo design, calendar, adequacy patch,
  optimization, outputs kept) and what each one reveals about the intent.
- The modelled system: key figures of the focus area(s) (load, capacity by technology, storages,
  interconnections), then of the whole system.
- Modelling tricks: each helper area or family of binding constraints, what it represents and how.
- What the author is trying to analyse.
- Points of attention: the findings of `check_study`, most severe first, each with what to verify.
- Questions for the author: what cannot be inferred from the study (naming conventions, intentions).

Give figures with units (GW, TWh, EUR/MWh). Clearly separate facts read in the study from inferences.
"""


def register(mcp: MCPServer) -> None:
    @mcp.prompt(title="Analyse the inputs of a study")
    def analyse_study_inputs(
        study: Annotated[str, Field(description="Name or id of the study to analyse.")],
    ) -> str:
        """Explain what a study models, why it is set up that way, and its possible inconsistencies."""
        return ANALYSE_STUDY_INPUTS.format(study=study)
