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
from typing import Any, Self

from pydantic import ConfigDict, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries
from antarest.study.business.model.thermal_reserve_certification_model import ThermalReserveCertification
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


class Certification(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    reserve: str
    max_power: float = 0.0
    max_power_off: float = 0.0
    participation_cost: float = 0.0
    participation_cost_off: float = 0.0

    def to_model(self) -> ThermalReserveCertification:
        return ThermalReserveCertification.model_validate(self.model_dump(exclude={"reserve"}))


class Symmetry(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    reserves: ReserveSymmetries


class Participation(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cluster: str
    certifications: list[Certification]
    symmetries: list[Symmetry]

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Forbid reserve duplication
        if len(self.certifications) != len(set(certification.reserve for certification in self.certifications)):
            raise ValueError(f"Some reserves are duplicated for cluster {self.cluster}")

        return self


class ThermalReserveParticipationsFileData(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    participations: list[Participation]

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Forbid thermal duplication
        if len(self.participations) != len(set(p.cluster for p in self.participations)):
            raise ValueError("Some thermals are duplicated")

        # Transform thermal ids
        for participation in self.participations:
            participation.cluster = transform_name_to_id(participation.cluster)

        return self

    def get_certifications(self) -> dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]:
        result: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]] = {}
        for participation in self.participations:
            for certification in participation.certifications:
                model = certification.to_model()
                reserve_id = ReserveDefinitionId(transform_name_to_id(certification.reserve))
                result.setdefault(reserve_id, {})[participation.cluster] = model
        return result

    def get_symmetries(self) -> dict[str, ReserveSymmetries]:
        result = {}
        for participation in self.participations:
            symmetries = []
            for symmetry in participation.symmetries:
                symmetries.append(symmetry.reserves)
            result[participation.cluster] = symmetries
        return result


def parse_thermal_reserves_certifications(
    data: dict[str, Any],
) -> dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]:
    return ThermalReserveParticipationsFileData.model_validate(data).get_certifications()


def serialize_thermal_reserve_certifications():
    raise NotImplementedError


def parse_thermal_reserves_symmetries(data: dict[str, Any]) -> dict[str, ReserveSymmetries]:
    return ThermalReserveParticipationsFileData.model_validate(data).get_symmetries()


def serialize_reserve_symmetries(symmetries: ReserveSymmetries) -> list[dict[str, Any]]:
    raise NotImplementedError
