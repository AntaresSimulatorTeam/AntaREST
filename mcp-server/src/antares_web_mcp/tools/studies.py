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

"""Tools for the study lifecycle: find, describe, create, import, copy, configure and delete studies."""

from pathlib import Path
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import TASK_COMPLETED, AntaresWebClient
from antares_web_mcp.enums import SimulationModeValue
from antares_web_mcp.tools.common import ADDITIVE, DESTRUCTIVE, READ_ONLY, UPDATE, StudyId, guard, without_none

COPY_TIMEOUT_SECONDS = 600
IMPORT_TIMEOUT_SECONDS = 1800
IMPORT_SUFFIXES = {".zip", ".7z"}


class StudySummary(BaseModel):
    """Compact view of a study, to keep tool outputs small for the model."""

    id: str
    name: str
    version: str
    type: str = Field(description="'rawstudy' or 'variantstudy'.")
    owner: str
    workspace: str
    managed: bool
    archived: bool
    parent_id: str | None = Field(default=None, description="Parent study id, for variant studies.")
    tags: list[str] = []
    updated: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "StudySummary":
        owner = data.get("owner") or {}
        return cls(
            id=data["id"],
            name=data["name"],
            version=str(data["version"]),
            type=data["type"],
            owner=str(owner.get("name", "")),
            workspace=data["workspace"],
            managed=data["managed"],
            archived=data["archived"],
            parent_id=data.get("parent_id"),
            tags=data.get("tags") or [],
            updated=data["updated"],
        )


class AreaDescription(BaseModel):
    id: str
    name: str
    thermal_clusters: list[str]
    renewable_clusters: list[str]
    storages: list[str]
    linked_to: list[str] = Field(description="Ids of the areas linked to this one.")


class StudyDescription(BaseModel):
    id: str
    version: str
    renewable_modelling: str = Field(
        description="'clusters': renewable clusters are simulated; 'aggregated': wind/solar area series are used."
    )
    areas: list[AreaDescription]
    outputs: list[str] = Field(description="Ids of the simulation outputs of the study.")


def register(mcp: MCPServer, client: AntaresWebClient, *, read_only: bool, allow_study_deletion: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_studies(
        name: Annotated[str, Field(description="Case-insensitive substring of the study name.")] = "",
        versions: Annotated[
            list[str] | None, Field(description='Antares versions to keep, e.g. ["8.8", "9.2"].')
        ] = None,
        tags: Annotated[list[str] | None, Field(description="Keep only studies having one of these tags.")] = None,
        variant: Annotated[
            bool | None, Field(description="true: only variant studies, false: only raw studies.")
        ] = None,
        archived: Annotated[bool | None, Field(description="Filter on the archived status.")] = None,
        limit: Annotated[int, Field(ge=1, le=500, description="Maximum number of studies returned.")] = 50,
    ) -> list[StudySummary]:
        """List the Antares studies visible to the current user, sorted by name."""
        studies = await guard(
            client.list_studies(
                name=name, versions=versions, tags=tags, variant=variant, archived=archived, limit=limit
            )
        )
        return [StudySummary.from_api(s) for s in studies]

    @mcp.tool(annotations=READ_ONLY)
    async def get_study(study_id: StudyId) -> dict[str, Any]:
        """Get all the metadata of one study (owner, groups, version, workspace, folder, tags, ...)."""
        return await guard(client.get_study(study_id))

    @mcp.tool(annotations=READ_ONLY)
    async def describe_study(study_id: StudyId) -> StudyDescription:
        """
        Describe the content of a study in one call: its areas with their clusters, storages and
        links, and the list of its simulation outputs. Prefer it to several `list_*` calls.
        """
        synthesis = await guard(client.get_study_synthesis(study_id))
        synthesis_areas: dict[str, dict[str, Any]] = synthesis.get("areas") or {}
        # A link is only stored in its first area (alphabetical order): rebuild both directions.
        neighbours: dict[str, set[str]] = {area_id: set() for area_id in synthesis_areas}
        for area_id, area in synthesis_areas.items():
            for other in area.get("links") or {}:
                neighbours.setdefault(area_id, set()).add(other)
                neighbours.setdefault(other, set()).add(area_id)
        areas = [
            AreaDescription(
                id=area_id,
                name=area.get("name", area_id),
                thermal_clusters=_ids(area.get("thermals")),
                renewable_clusters=_ids(area.get("renewables")),
                storages=_ids(area.get("st_storages")),
                linked_to=sorted(neighbours[area_id]),
            )
            for area_id, area in synthesis_areas.items()
        ]
        return StudyDescription(
            id=synthesis.get("study_id", study_id),
            version=str(synthesis.get("version", "")),
            renewable_modelling=str(synthesis.get("enr_modelling", "")),
            areas=areas,
            outputs=sorted(synthesis.get("outputs") or {}),
        )

    @mcp.tool(annotations=READ_ONLY)
    async def list_study_versions() -> list[str]:
        """List the Antares study versions that can be created on this server (e.g. "8.8", "9.2")."""
        return await guard(client.list_study_versions())

    @mcp.tool(annotations=READ_ONLY)
    async def get_simulation_settings(study_id: StudyId) -> dict[str, Any]:
        """
        Get the general simulation settings of a study: mode (Economy / Adequacy), number of
        Monte-Carlo years, simulated period (first / last day), calendar, outputs (year-by-year, synthesis).
        """
        return await guard(client.get_general_config(study_id))

    if read_only:
        return

    @mcp.tool(annotations=ADDITIVE)
    async def create_study(
        name: Annotated[str, Field(min_length=1, description="Name of the new study.")],
        version: Annotated[
            str | None,
            Field(
                description=(
                    "Antares version, e.g. '8.8' (see `list_study_versions`). Default: the latest one. "
                    "Pick a version supported by a launcher (see `list_launchers`) to be able to run it."
                )
            ),
        ] = None,
        directory: Annotated[
            str | None, Field(description="Directory in which to create the study, e.g. 'project/subfolder'.")
        ] = None,
    ) -> StudySummary:
        """Create a new empty study (no area). Returns the created study."""
        study_id = await guard(client.create_study(name, version=version, directory=directory))
        return StudySummary.from_api(await guard(client.get_study(study_id)))

    @mcp.tool(annotations=ADDITIVE)
    async def import_study(
        path: Annotated[
            str,
            Field(
                min_length=1,
                description=(
                    "Path of a study archive (.zip or .7z) on the machine running this MCP server, "
                    "e.g. '/home/user/Downloads/my_study.zip'."
                ),
            ),
        ],
        groups: Annotated[
            list[str] | None, Field(description="Ids of the user groups to share the imported study with.")
        ] = None,
    ) -> StudySummary:
        """
        Import a study from a local archive (.zip or .7z) into Antares Web, as a new raw study
        (waits for the upload: a large archive can take minutes). The study name comes from the archive.
        """
        archive = Path(path).expanduser()
        if archive.suffix.lower() not in IMPORT_SUFFIXES:
            raise ToolError(f"'{archive.name}' is not a study archive: expected a .zip or .7z file.")
        if not archive.is_file():
            raise ToolError(f"No such file on the MCP server machine: '{archive}'.")
        study_id = await guard(client.import_study(archive, groups=groups, timeout=IMPORT_TIMEOUT_SECONDS))
        return StudySummary.from_api(await guard(client.get_study(study_id)))

    @mcp.tool(annotations=ADDITIVE)
    async def copy_study(
        study_id: StudyId,
        new_name: Annotated[str, Field(min_length=1, description="Name of the copy.")],
        with_outputs: Annotated[bool, Field(description="Also copy the simulation outputs.")] = False,
    ) -> StudySummary:
        """
        Copy a study into a new, independent raw study (waits for the copy to complete).
        Prefer `create_variant` to explore alternatives of a study while keeping track of the changes.
        """
        task_id = await guard(client.copy_study(study_id, new_name, with_outputs=with_outputs))
        task = await guard(client.wait_for_task(task_id, timeout=COPY_TIMEOUT_SECONDS))
        result = task.get("result") or {}
        if task.get("status") != TASK_COMPLETED or not result.get("success"):
            raise ToolError(f"The copy did not complete: {result.get('message') or task}")
        return StudySummary.from_api(await guard(client.get_study(result["returnValue"])))

    @mcp.tool(annotations=ADDITIVE)
    async def create_variant(
        study_id: StudyId,
        name: Annotated[str, Field(min_length=1, description="Name of the variant.")],
    ) -> StudySummary:
        """
        Create a variant of a study. A variant records its changes as commands on top of its parent:
        it is the recommended way to test alternatives (e.g. "what if the interconnection is doubled").
        The variant can be modified and launched like any study.
        """
        variant_id = await guard(client.create_variant(study_id, name))
        return StudySummary.from_api(await guard(client.get_study(variant_id)))

    @mcp.tool(annotations=UPDATE)
    async def update_simulation_settings(
        study_id: StudyId,
        mode: Annotated[SimulationModeValue | None, Field(description="Simulation mode.")] = None,
        nb_years: Annotated[
            int | None, Field(ge=1, le=50000, description="Number of Monte-Carlo years to simulate.")
        ] = None,
        first_day: Annotated[int | None, Field(ge=1, le=366, description="First simulated day of the year.")] = None,
        last_day: Annotated[int | None, Field(ge=1, le=366, description="Last simulated day of the year.")] = None,
        year_by_year: Annotated[bool | None, Field(description="Also write detailed results for each year.")] = None,
        horizon: Annotated[str | None, Field(description="Free label of the study horizon, e.g. '2030'.")] = None,
    ) -> dict[str, Any]:
        """
        Update the general simulation settings of a study. Only the provided values are changed.
        Returns the new settings. Tip: use 1 Monte-Carlo year for quick tests.
        """
        changes = without_none(
            {
                "mode": mode,
                "nbYears": nb_years,
                "firstDay": first_day,
                "lastDay": last_day,
                "yearByYear": year_by_year,
                "horizon": horizon,
            }
        )
        if not changes:
            raise ToolError("Nothing to update: provide at least one setting.")
        await guard(client.update_general_config(study_id, changes))
        return await guard(client.get_general_config(study_id))

    if not allow_study_deletion:
        return

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_study(
        study_id: StudyId,
        with_variants: Annotated[
            bool, Field(description="Also delete the variants of the study (required if it has some).")
        ] = False,
    ) -> str:
        """Permanently delete a study and its outputs. This cannot be undone: ask the user to confirm first."""
        study = await guard(client.get_study(study_id))
        await guard(client.delete_study(study_id, children=with_variants))
        return f"Study '{study['name']}' ({study_id}) deleted."


def _ids(items: Any) -> list[str]:
    """Extracts object ids from a synthesis collection (a list of objects or a mapping keyed by id)."""
    if not items:
        return []
    if isinstance(items, dict):
        return sorted(items)
    return [str(item.get("id") or item.get("name")) if isinstance(item, dict) else str(item) for item in items]
