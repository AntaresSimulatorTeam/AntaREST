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

"""Tools for the network: areas (nodes) and links (edges)."""

from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.enums import AssetTypeValue, TransmissionCapacityValue
from antares_web_mcp.tools.common import (
    ADDITIVE,
    DESTRUCTIVE,
    READ_ONLY,
    UPDATE,
    AreaId,
    StudyId,
    guard,
    without_none,
)


class AreaSummary(BaseModel):
    id: str = Field(description="Area id, used to reference the area in other tools.")
    name: str = Field(description="Display name of the area.")


def register(mcp: MCPServer, client: AntaresWebClient, *, read_only: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_areas(study_id: StudyId) -> list[AreaSummary]:
        """List the areas (network nodes) of a study."""
        areas = await guard(client.list_areas(study_id))
        return [AreaSummary(id=a["id"], name=a["name"]) for a in areas]

    @mcp.tool(annotations=READ_ONLY)
    async def list_links(study_id: StudyId) -> list[dict[str, Any]]:
        """
        List the links (network edges between two areas) of a study, with all their properties
        (asset type, transmission capacities mode, hurdle costs, loop flow, phase shifter, display style, ...).
        """
        return await guard(client.list_links(study_id))

    @mcp.tool(annotations=READ_ONLY)
    async def get_area_properties(study_id: StudyId, area_id: AreaId) -> dict[str, Any]:
        """Get the economic properties of an area (unsupplied / spilled energy costs, dispatch options, ...)."""
        return await guard(client.get_area_properties(study_id, area_id))

    if read_only:
        return

    @mcp.tool(annotations=ADDITIVE)
    async def create_area(
        study_id: StudyId,
        name: Annotated[str, Field(min_length=1, description="Display name of the new area, e.g. 'France'.")],
    ) -> AreaSummary:
        """
        Create a new area in a study. The area id is derived from the name (lower-case, normalized)
        and is returned: use it to reference the area afterwards.
        A new area has no load and an unsupplied energy cost of 0: see `set_area_load` and
        `update_area_properties`.
        """
        area = await guard(client.create_area(study_id, name))
        return AreaSummary(id=area["id"], name=area["name"])

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_area(study_id: StudyId, area_id: AreaId) -> str:
        """
        Delete an area from a study, together with all its links and clusters.
        Fails if the area is referenced by a binding constraint: remove it from the constraint first.
        This cannot be undone on a raw study.
        """
        deleted_id = await guard(client.delete_area(study_id, area_id))
        return f"Area '{deleted_id}' deleted."

    @mcp.tool(annotations=UPDATE)
    async def update_area_properties(
        study_id: StudyId,
        area_id: AreaId,
        unsupplied_energy_cost: Annotated[
            float | None,
            Field(
                ge=0,
                description=(
                    "Cost of unsupplied energy (EUR/MWh), also called value of lost load. "
                    "Typical values: 3000 to 20000. With the default (0), marginal prices are meaningless."
                ),
            ),
        ] = None,
        spilled_energy_cost: Annotated[
            float | None, Field(ge=0, description="Cost of spilled energy (EUR/MWh).")
        ] = None,
    ) -> dict[str, Any]:
        """Update the economic properties of an area. Only the provided values are changed."""
        changes = without_none(
            {"energyCostUnsupplied": unsupplied_energy_cost, "energyCostSpilled": spilled_energy_cost}
        )
        if not changes:
            raise ToolError("Nothing to update: provide at least one property.")
        await guard(client.update_area_properties(study_id, area_id, changes))
        return await guard(client.get_area_properties(study_id, area_id))

    @mcp.tool(annotations=ADDITIVE)
    async def create_link(
        study_id: StudyId,
        area1: AreaId,
        area2: AreaId,
        asset_type: Annotated[
            AssetTypeValue | None, Field(description="Physical nature of the link. Default: 'ac'.")
        ] = None,
        transmission_capacities: Annotated[
            TransmissionCapacityValue | None,
            Field(
                description=(
                    "'enabled': capacities are taken from the link time series (default); "
                    "'infinite': no limit; 'ignore': the link is ignored by the simulation."
                )
            ),
        ] = None,
        hurdles_cost: Annotated[bool | None, Field(description="Take hurdle costs into account.")] = None,
        loop_flow: Annotated[bool | None, Field(description="Take loop flows into account.")] = None,
        use_phase_shifter: Annotated[bool | None, Field(description="Use a phase shifter.")] = None,
        comments: Annotated[str | None, Field(description="Free comment attached to the link.")] = None,
    ) -> dict[str, Any]:
        """
        Create a link between two existing areas of a study. Unspecified properties take the
        Antares default values. Returns the created link.
        Important: a new link has a transmission capacity of 0 MW in both directions,
        so nothing flows through it until `set_link_capacity` is called.
        """
        payload: dict[str, Any] = {"area1": area1, "area2": area2}
        payload.update(
            _link_properties(
                asset_type=asset_type,
                transmission_capacities=transmission_capacities,
                hurdles_cost=hurdles_cost,
                loop_flow=loop_flow,
                use_phase_shifter=use_phase_shifter,
                comments=comments,
            )
        )
        return await guard(client.create_link(study_id, payload))

    @mcp.tool(annotations=UPDATE)
    async def update_link(
        study_id: StudyId,
        area1: AreaId,
        area2: AreaId,
        asset_type: Annotated[AssetTypeValue | None, Field(description="New asset type.")] = None,
        transmission_capacities: Annotated[
            TransmissionCapacityValue | None, Field(description="New transmission capacities mode.")
        ] = None,
        hurdles_cost: Annotated[bool | None, Field(description="Take hurdle costs into account.")] = None,
        loop_flow: Annotated[bool | None, Field(description="Take loop flows into account.")] = None,
        use_phase_shifter: Annotated[bool | None, Field(description="Use a phase shifter.")] = None,
        comments: Annotated[str | None, Field(description="New comment.")] = None,
    ) -> dict[str, Any]:
        """
        Update some properties of an existing link. Only the provided properties are changed.
        Returns the updated link. To change the capacity in MW, use `set_link_capacity`.
        """
        changes = _link_properties(
            asset_type=asset_type,
            transmission_capacities=transmission_capacities,
            hurdles_cost=hurdles_cost,
            loop_flow=loop_flow,
            use_phase_shifter=use_phase_shifter,
            comments=comments,
        )
        if not changes:
            raise ToolError("Nothing to update: provide at least one link property.")
        area_from, area_to = sorted([area1, area2])
        return await guard(client.update_link(study_id, area_from, area_to, changes))

    @mcp.tool(annotations=UPDATE)
    async def set_link_capacity(
        study_id: StudyId,
        area1: AreaId,
        area2: AreaId,
        capacity_1_to_2: Annotated[
            float, Field(ge=0, description="Transmission capacity (MW) from `area1` to `area2`, for every hour.")
        ],
        capacity_2_to_1: Annotated[
            float | None,
            Field(ge=0, description="Transmission capacity (MW) from `area2` to `area1`. Default: same as 1 to 2."),
        ] = None,
    ) -> str:
        """
        Set a constant hourly transmission capacity (NTC, in MW) on an existing link, in both directions
        (for studies in version 8.2 or later). Applies to all the time series of the link.
        """
        reverse = capacity_1_to_2 if capacity_2_to_1 is None else capacity_2_to_1
        area_from, area_to = sorted([area1, area2])
        direct, indirect = (capacity_1_to_2, reverse) if area_from == area1 else (reverse, capacity_1_to_2)
        base = f"input/links/{area_from}/capacities/{area_to}"
        await guard(client.edit_matrix(study_id, f"{base}_direct", "=", direct))
        await guard(client.edit_matrix(study_id, f"{base}_indirect", "=", indirect))
        return (
            f"Link {area_from} / {area_to}: {direct:g} MW from {area_from} to {area_to}, "
            f"{indirect:g} MW from {area_to} to {area_from}."
        )

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_link(study_id: StudyId, area1: AreaId, area2: AreaId) -> str:
        """
        Delete the link between two areas. Fails if the link is referenced by a binding constraint.
        This cannot be undone on a raw study.
        """
        area_from, area_to = sorted([area1, area2])
        deleted = await guard(client.delete_link(study_id, area_from, area_to))
        return f"Link '{deleted}' deleted."


def _link_properties(
    *,
    asset_type: str | None,
    transmission_capacities: str | None,
    hurdles_cost: bool | None,
    loop_flow: bool | None,
    use_phase_shifter: bool | None,
    comments: str | None,
) -> dict[str, Any]:
    """Builds the REST payload (camelCase keys, as used by the API) from the provided properties only."""
    return without_none(
        {
            "assetType": asset_type,
            "transmissionCapacities": transmission_capacities,
            "hurdlesCost": hurdles_cost,
            "loopFlow": loop_flow,
            "usePhaseShifter": use_phase_shifter,
            "comments": comments,
        }
    )
