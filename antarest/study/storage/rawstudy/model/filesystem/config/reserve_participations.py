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

from abc import ABC, abstractmethod
from typing import Any, Self

from pydantic import ConfigDict, model_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.reserve_certification_model import (
    Cost,
    Power,
    ReserveCertification,
    StorageReserveCertification,
    ThermalReserveCertification,
)
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetries, ReserveSymmetry
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id


class _AreaAssetCertification(ABC, AntaresBaseModel):
    reserve: str

    @abstractmethod
    def to_model(self) -> Any:
        raise NotImplementedError


class _ThermalCertification(_AreaAssetCertification):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    max_power: Power = 0.0
    max_power_off: Power = 0.0
    participation_cost: Cost = 0.0
    participation_cost_off: Cost = 0.0

    def to_model(self) -> ThermalReserveCertification:
        return ThermalReserveCertification.model_validate(self.model_dump(exclude={"reserve"}))


class _StorageCertification(_AreaAssetCertification):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    max_release: Power = 0.0
    max_store: Power = 0.0
    participation_cost: Cost = 0.0

    def to_model(self) -> StorageReserveCertification:
        return StorageReserveCertification.model_validate(self.model_dump(exclude={"reserve"}))


class Symmetry(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    reserves: ReserveSymmetry


class Participation(ABC, AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    cluster: str
    certifications: list[_AreaAssetCertification] = []
    symmetries: list[Symmetry] = []

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Forbid reserve duplication
        if len(self.certifications) != len(set(certification.reserve for certification in self.certifications)):
            raise ValueError(f"Some reserves are duplicated for cluster {self.cluster}")

        return self


class ThermalParticipation(Participation):
    certifications: list[_ThermalCertification] = []


class STStorageParticipation(Participation):
    certifications: list[_StorageCertification] = []


class _AreaAssetParticipationFileData(AntaresBaseModel):
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

    def get_symmetries(self) -> dict[str, ReserveSymmetries]:
        result = {}
        for participation in self.participations:
            symmetries = []
            for symmetry in participation.symmetries:
                symmetries.append(symmetry.reserves)
            if symmetries:
                result[participation.cluster] = symmetries
        return result

    @classmethod
    def _reorganize_certifications(
        cls, certifications: dict[ReserveDefinitionId, dict[str, ReserveCertification]]
    ) -> dict[str, dict[ReserveDefinitionId, ReserveCertification]]:
        # Reorganize certifications to order them by id.

        reorganized_certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]] = {}
        for reserve_id, value in certifications.items():
            for thermal_id, certification in value.items():
                reorganized_certifications.setdefault(thermal_id, {})[reserve_id] = certification
        return reorganized_certifications

    @classmethod
    def from_model(
        cls,
        symmetries: dict[str, ReserveSymmetries],
        certifications: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]],
    ) -> Self:
        thermal_certifications = cls._reorganize_certifications(certifications)

        participations = []
        cls._iterate_through_symmetries(participations, symmetries, thermal_certifications)

        # Iterate through certifications with an id not in symmetries
        cls._iterate_through_certifications(participations, thermal_certifications)

        return cls.model_validate({"participations": participations})

    @classmethod
    def _iterate_through_certifications(
        cls,
        participations: list[Any],
        thermal_certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]],
    ):
        for cluster_id, values in thermal_certifications.items():
            participation: dict[str, Any] = cls.initialize_participation(cluster_id)
            if values:
                participation["certifications"] = [{"reserve": r_id, **c.model_dump()} for r_id, c in values.items()]
            participations.append(participation)

    @classmethod
    def initialize_participation(cls, cluster_id: str) -> dict[str, str]:
        raise NotImplementedError

    @classmethod
    def _iterate_through_symmetries(
        cls,
        participations: list[Any],
        symmetries: dict[str, list[list[ReserveDefinitionId]]],
        certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]],
    ):
        for cluster_id, reserve_symmetries in symmetries.items():
            certifs = certifications.pop(cluster_id, {})
            participation: dict[str, Any] = cls.initialize_participation(cluster_id)
            if certifs:
                participation["certifications"] = [{"reserve": r_id, **c.model_dump()} for r_id, c in certifs.items()]
            if reserve_symmetries != [[]]:
                participation["symmetries"] = [{"reserves": s} for s in reserve_symmetries]

            participations.append(participation)


class ThermalReserveParticipationsFileData(_AreaAssetParticipationFileData):
    participations: list[ThermalParticipation]

    def get_certifications(self) -> dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]:
        result: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]] = {}
        for participation in self.participations:
            for certification in participation.certifications:
                model = certification.to_model()
                reserve_id = ReserveDefinitionId(transform_name_to_id(certification.reserve))
                result.setdefault(reserve_id, {})[participation.cluster] = model
        return result

    @classmethod
    def initialize_participation(cls, cluster_id: str) -> dict[str, str]:
        return {"cluster": cluster_id}


class STStorageReserveParticipationsFileData(_AreaAssetParticipationFileData):
    participations: list[STStorageParticipation]

    def get_certifications(self) -> dict[ReserveDefinitionId, dict[str, StorageReserveCertification]]:
        result: dict[ReserveDefinitionId, dict[str, StorageReserveCertification]] = {}
        for participation in self.participations:
            for certification in participation.certifications:
                model = certification.to_model()
                reserve_id = ReserveDefinitionId(transform_name_to_id(certification.reserve))
                result.setdefault(reserve_id, {})[participation.cluster] = model
        return result

    @classmethod
    def initialize_participation(cls, storage_id: str) -> dict[str, str]:
        return {"storage": storage_id}


def parse_thermal_reserves_certifications(
    data: dict[str, Any],
) -> dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]:
    return ThermalReserveParticipationsFileData.model_validate(data).get_certifications()


def serialize_thermal_reserve_participations(
    symmetries: dict[str, ReserveSymmetries],
    certifications: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]],
) -> dict[str, Any]:
    model = ThermalReserveParticipationsFileData.from_model(symmetries, certifications)
    # `exclude_unset` allows us to remove empty lists as they won't be written correctly in the file.
    return model.model_dump(mode="json", by_alias=True, exclude_unset=True)


def parse_thermal_reserves_symmetries(data: dict[str, Any]) -> dict[str, ReserveSymmetries]:
    return ThermalReserveParticipationsFileData.model_validate(data).get_symmetries()
