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
Tools to fill a study with the data a simulation needs: load, generation clusters and storages.

These tools are "business" tools rather than 1:1 wrappers: for instance a thermal cluster created
through the REST API has a null availability time series (it would produce nothing), so
`create_thermal_cluster` also sets its availability to its installed capacity.
"""

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from antares_web_mcp.client import AntaresWebClient
from antares_web_mcp.enums import RenewableGroupValue, StorageGroupValue, ThermalGroupValue
from antares_web_mcp.tools.common import (
    ADDITIVE,
    DESTRUCTIVE,
    MATRIX_OPERATIONS,
    READ_ONLY,
    UPDATE,
    AreaId,
    StudyId,
    guard,
    without_none,
)

THERMAL = "clusters/thermal"
RENEWABLE = "clusters/renewable"
STORAGE = "storages"
CLUSTER_KINDS = {"thermal": THERMAL, "renewable": RENEWABLE, "storage": STORAGE}

ClusterId = Annotated[str, Field(description="Cluster id, as returned by `list_clusters`.")]
MatrixOperation = Annotated[
    Literal["set", "add", "multiply"],
    Field(description="'set': value in MW; 'add': MW added to every hour; 'multiply': factor (1.1 = +10%)."),
]


class ThermalCluster(BaseModel):
    id: str
    name: str
    group: str | None = None
    enabled: bool | None = None
    unit_count: int | None = None
    nominal_capacity: float | None = Field(default=None, description="Capacity of one unit (MW).")
    marginal_cost: float | None = Field(default=None, description="EUR/MWh.")
    market_bid_cost: float | None = Field(default=None, description="EUR/MWh, used for the merit order.")

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "ThermalCluster":
        return cls(
            id=data["id"],
            name=data["name"],
            group=data.get("group"),
            enabled=data.get("enabled"),
            unit_count=data.get("unitCount"),
            nominal_capacity=data.get("nominalCapacity"),
            marginal_cost=data.get("marginalCost"),
            market_bid_cost=data.get("marketBidCost"),
        )


class RenewableCluster(BaseModel):
    id: str
    name: str
    group: str | None = None
    enabled: bool | None = None
    unit_count: int | None = None
    nominal_capacity: float | None = Field(default=None, description="Capacity of one unit (MW).")
    ts_interpretation: str | None = Field(
        default=None, description="'production-factor' (series in [0, 1]) or 'power-generation' (series in MW)."
    )

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "RenewableCluster":
        return cls(
            id=data["id"],
            name=data["name"],
            group=data.get("group"),
            enabled=data.get("enabled"),
            unit_count=data.get("unitCount"),
            nominal_capacity=data.get("nominalCapacity"),
            ts_interpretation=data.get("tsInterpretation"),
        )


class Storage(BaseModel):
    id: str
    name: str
    group: str | None = None
    enabled: bool | None = None
    injection_capacity: float | None = Field(default=None, description="MW.")
    withdrawal_capacity: float | None = Field(default=None, description="MW.")
    reservoir_capacity: float | None = Field(default=None, description="MWh.")
    efficiency: float | None = None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Storage":
        return cls(
            id=data["id"],
            name=data["name"],
            group=data.get("group"),
            enabled=data.get("enabled"),
            injection_capacity=data.get("injectionNominalCapacity"),
            withdrawal_capacity=data.get("withdrawalNominalCapacity"),
            reservoir_capacity=data.get("reservoirCapacity"),
            efficiency=data.get("efficiency"),
        )


class AreaClusters(BaseModel):
    thermal: list[ThermalCluster]
    renewable: list[RenewableCluster]
    storages: list[Storage]


class ThermalCreation(BaseModel):
    cluster: ThermalCluster
    availability_mw: float = Field(description="Hourly available capacity set for all the time series (MW).")


def thermal_series_path(area_id: str, cluster_id: str) -> str:
    return f"input/thermal/series/{area_id}/{cluster_id.lower()}/series"


def renewable_series_path(area_id: str, cluster_id: str) -> str:
    return f"input/renewables/series/{area_id}/{cluster_id.lower()}/series"


def register(mcp: MCPServer, client: AntaresWebClient, *, read_only: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    async def list_clusters(study_id: StudyId, area_id: AreaId) -> AreaClusters:
        """List the thermal clusters, renewable clusters and short-term storages of an area."""
        thermal = await guard(client.list_clusters(study_id, area_id, THERMAL))
        renewable = await guard(client.list_clusters(study_id, area_id, RENEWABLE))
        storages = await guard(client.list_clusters(study_id, area_id, STORAGE))
        return AreaClusters(
            thermal=[ThermalCluster.from_api(c) for c in thermal],
            renewable=[RenewableCluster.from_api(c) for c in renewable],
            storages=[Storage.from_api(c) for c in storages],
        )

    if read_only:
        return

    @mcp.tool(annotations=UPDATE)
    async def set_area_load(
        study_id: StudyId,
        area_id: AreaId,
        value: Annotated[float, Field(description="Value to apply to every hour (see `operation`).")],
        operation: MatrixOperation = "set",
    ) -> str:
        """
        Set or modify the hourly load (consumption, MW) of an area, applied to all its time series.
        Examples: set a constant 60000 MW load, add 2000 MW, or multiply by 1.1 (+10%).
        """
        await guard(
            client.edit_matrix(study_id, f"input/load/series/load_{area_id}", MATRIX_OPERATIONS[operation], value)
        )
        return f"Load of '{area_id}': {operation} {value:g} applied to every hour."

    @mcp.tool(annotations=ADDITIVE)
    async def create_thermal_cluster(
        study_id: StudyId,
        area_id: AreaId,
        name: Annotated[str, Field(min_length=1, description="Name of the cluster, e.g. 'Nuclear FR'.")],
        group: Annotated[ThermalGroupValue, Field(description="Technology group (used to aggregate results).")],
        nominal_capacity: Annotated[float, Field(gt=0, description="Capacity of one unit (MW).")],
        marginal_cost: Annotated[float, Field(ge=0, description="Marginal operating cost (EUR/MWh).")],
        unit_count: Annotated[int, Field(ge=1, description="Number of identical units.")] = 1,
        market_bid_cost: Annotated[
            float | None,
            Field(ge=0, description="Bid used for the merit order (EUR/MWh). Default: the marginal cost."),
        ] = None,
        must_run: Annotated[bool | None, Field(description="The cluster always produces at full availability.")] = None,
        min_stable_power: Annotated[
            float | None, Field(ge=0, description="Minimum stable power of a unit (MW).")
        ] = None,
        co2: Annotated[float | None, Field(ge=0, description="CO2 emission factor (t/MWh).")] = None,
    ) -> ThermalCreation:
        """
        Create a thermal power plant cluster in an area, ready to be simulated: its hourly
        availability is set to its installed capacity (unit_count x nominal_capacity).
        """
        payload = without_none(
            {
                "name": name,
                "group": group,
                "unitCount": unit_count,
                "nominalCapacity": nominal_capacity,
                "marginalCost": marginal_cost,
                "marketBidCost": marginal_cost if market_bid_cost is None else market_bid_cost,
                "mustRun": must_run,
                "minStablePower": min_stable_power,
                "co2": co2,
            }
        )
        cluster = await guard(client.create_cluster(study_id, area_id, THERMAL, payload))
        availability = unit_count * nominal_capacity
        await guard(client.edit_matrix(study_id, thermal_series_path(area_id, cluster["id"]), "=", availability))
        return ThermalCreation(cluster=ThermalCluster.from_api(cluster), availability_mw=availability)

    @mcp.tool(annotations=UPDATE)
    async def update_thermal_cluster(
        study_id: StudyId,
        area_id: AreaId,
        cluster_id: ClusterId,
        enabled: Annotated[bool | None, Field(description="Enable or disable the cluster.")] = None,
        unit_count: Annotated[int | None, Field(ge=0, description="New number of units.")] = None,
        nominal_capacity: Annotated[float | None, Field(ge=0, description="New capacity of one unit (MW).")] = None,
        marginal_cost: Annotated[
            float | None,
            Field(ge=0, description="New marginal cost (EUR/MWh). Also sets the market bid unless given."),
        ] = None,
        market_bid_cost: Annotated[float | None, Field(ge=0, description="New market bid (EUR/MWh).")] = None,
    ) -> ThermalCreation:
        """
        Update a thermal cluster. Only the provided values are changed. When the capacity changes
        (unit count or nominal capacity), the hourly availability is reset to the new installed capacity.
        """
        if market_bid_cost is None:
            market_bid_cost = marginal_cost
        changes = without_none(
            {
                "enabled": enabled,
                "unitCount": unit_count,
                "nominalCapacity": nominal_capacity,
                "marginalCost": marginal_cost,
                "marketBidCost": market_bid_cost,
            }
        )
        if not changes:
            raise ToolError("Nothing to update: provide at least one property.")
        cluster = await guard(client.update_cluster(study_id, area_id, THERMAL, cluster_id, changes))
        availability = (cluster.get("unitCount") or 0) * (cluster.get("nominalCapacity") or 0.0)
        if unit_count is not None or nominal_capacity is not None:
            await guard(client.edit_matrix(study_id, thermal_series_path(area_id, cluster["id"]), "=", availability))
        return ThermalCreation(cluster=ThermalCluster.from_api(cluster), availability_mw=availability)

    @mcp.tool(annotations=ADDITIVE)
    async def create_renewable_cluster(
        study_id: StudyId,
        area_id: AreaId,
        name: Annotated[str, Field(min_length=1, description="Name of the cluster, e.g. 'Wind onshore FR'.")],
        group: Annotated[RenewableGroupValue, Field(description="Technology group (used to aggregate results).")],
        nominal_capacity: Annotated[float, Field(gt=0, description="Capacity of one unit (MW).")],
        capacity_factor: Annotated[
            float,
            Field(
                ge=0,
                le=1,
                description=(
                    "Constant hourly production factor in [0, 1] (production = factor x installed capacity). "
                    "Typical yearly averages: wind onshore 0.25, wind offshore 0.4, solar PV 0.13."
                ),
            ),
        ],
        unit_count: Annotated[int, Field(ge=1, description="Number of identical units.")] = 1,
    ) -> RenewableCluster:
        """
        Create a renewable generation cluster (wind, solar, ...) in an area, with a constant hourly
        production factor. Renewable clusters are only simulated when the study renewable modelling
        is 'clusters' (the default for new studies, see `describe_study`).
        """
        payload = {
            "name": name,
            "group": group,
            "unitCount": unit_count,
            "nominalCapacity": nominal_capacity,
            "tsInterpretation": "production-factor",
        }
        cluster = await guard(client.create_cluster(study_id, area_id, RENEWABLE, payload))
        await guard(client.edit_matrix(study_id, renewable_series_path(area_id, cluster["id"]), "=", capacity_factor))
        return RenewableCluster.from_api(cluster)

    @mcp.tool(annotations=ADDITIVE)
    async def create_storage(
        study_id: StudyId,
        area_id: AreaId,
        name: Annotated[str, Field(min_length=1, description="Name of the storage, e.g. 'Battery FR'.")],
        injection_capacity: Annotated[float, Field(ge=0, description="Maximum charging power (MW).")],
        withdrawal_capacity: Annotated[float, Field(ge=0, description="Maximum discharging power (MW).")],
        reservoir_capacity: Annotated[float, Field(ge=0, description="Energy capacity (MWh).")],
        group: Annotated[StorageGroupValue, Field(description="Storage technology.")] = "battery",
        efficiency: Annotated[float, Field(gt=0, le=1, description="Charging efficiency in ]0, 1].")] = 1.0,
    ) -> Storage:
        """Create a short-term storage (battery, pumped storage, ...) in an area."""
        payload = {
            "name": name,
            "group": group,
            "injectionNominalCapacity": injection_capacity,
            "withdrawalNominalCapacity": withdrawal_capacity,
            "reservoirCapacity": reservoir_capacity,
            "efficiency": efficiency,
        }
        return Storage.from_api(await guard(client.create_cluster(study_id, area_id, STORAGE, payload)))

    @mcp.tool(annotations=DESTRUCTIVE)
    async def delete_cluster(
        study_id: StudyId,
        area_id: AreaId,
        kind: Annotated[Literal["thermal", "renewable", "storage"], Field(description="Kind of object.")],
        cluster_id: ClusterId,
    ) -> str:
        """
        Delete a thermal cluster, renewable cluster or short-term storage. Fails if it is referenced
        by a binding constraint. This cannot be undone on a raw study.
        """
        await guard(client.delete_clusters(study_id, area_id, CLUSTER_KINDS[kind], [cluster_id]))
        return f"{kind.capitalize()} '{cluster_id}' deleted from area '{area_id}'."
