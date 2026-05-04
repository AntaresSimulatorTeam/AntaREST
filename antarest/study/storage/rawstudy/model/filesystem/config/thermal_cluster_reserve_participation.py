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
from typing import Any

from pydantic import ConfigDict

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
)

# Separator used in the INI section name to combine the cluster and reserve identifiers.
# A standard INI parser merges duplicate sections, so a unique composite key is used to
# address each (cluster, reserve) participation independently. Because cluster and reserve
# IDs may legally contain the separator string itself, the section name is *not* trusted
# for parsing: the canonical source of truth is the ``cluster-name`` field stored in the
# section content (auto-populated from the ``thermal_id``).
SECTION_SEPARATOR = "__"


class ThermalClusterReserveParticipationFileData(AntaresBaseModel):
    """INI-shaped representation of a participation.

    The ``cluster_name`` field is a denormalization of the cluster identity needed by the
    Antares simulator on disk; it is auto-filled from the ``thermal_id`` at serialization
    time and is not part of the canonical business model.
    """

    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    cluster_name: str
    max_power: float = 0.0
    max_power_off: float = 0.0
    participation_cost: float = 0.0
    participation_cost_off: float = 0.0

    def to_model(self, reserve_id: str) -> ThermalClusterReserveParticipation:
        payload = self.model_dump()
        payload.pop("cluster_name", None)
        return ThermalClusterReserveParticipation.model_validate({"id": reserve_id, **payload})

    @classmethod
    def from_model(
        cls, thermal_id: str, participation: ThermalClusterReserveParticipation
    ) -> "ThermalClusterReserveParticipationFileData":
        payload = participation.model_dump(exclude={"id"})
        payload["cluster_name"] = thermal_id
        return cls.model_validate(payload)


def section_name(cluster_id: str, reserve_id: str) -> str:
    return f"{cluster_id}{SECTION_SEPARATOR}{reserve_id}"


def extract_reserve_id(section: str, cluster_name: str) -> str | None:
    """Extract the ``reserve_id`` part from a section name, given the ``cluster_name``
    read from the section content.

    The composite section name follows the convention ``<cluster_name><sep><reserve_id>``.
    Splitting blindly on the separator would be ambiguous because both cluster and reserve
    IDs may contain it; the cluster name from the content is therefore used as the
    canonical anchor.

    Returns ``None`` if the section name does not start with ``<cluster_name><sep>`` (which
    happens for unrelated sections like ``[symmetries]``).
    """
    prefix = f"{cluster_name}{SECTION_SEPARATOR}"
    if not section.startswith(prefix):
        return None
    reserve_id = section[len(prefix) :]
    if not reserve_id:
        return None
    return reserve_id


def parse_thermal_cluster_reserve_participation(
    reserve_id: str, data: dict[str, Any]
) -> ThermalClusterReserveParticipation:
    return ThermalClusterReserveParticipationFileData.model_validate(data).to_model(reserve_id)


def serialize_thermal_cluster_reserve_participation(
    thermal_id: str, participation: ThermalClusterReserveParticipation
) -> dict[str, Any]:
    return ThermalClusterReserveParticipationFileData.from_model(thermal_id, participation).model_dump(
        mode="json", by_alias=True
    )
