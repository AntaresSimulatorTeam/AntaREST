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
from collections.abc import Mapping
from typing import Any, Generic, Self, TypeVar

from pydantic import ConfigDict, model_validator
from typing_extensions import override

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


class _ThermalCertification(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    max_power: Power = 0.0
    max_power_off: Power = 0.0
    participation_cost: Cost = 0.0
    participation_cost_off: Cost = 0.0
    reserve: str

    def to_model(self) -> ThermalReserveCertification:
        return ThermalReserveCertification.model_validate(self.model_dump(exclude={"reserve"}))


class _StorageCertification(AntaresBaseModel):
    model_config = ConfigDict(alias_generator=to_kebab_case, extra="forbid", populate_by_name=True)

    max_release: Power = 0.0
    max_store: Power = 0.0
    participation_cost: Cost = 0.0
    reserve: str

    def to_model(self) -> StorageReserveCertification:
        return StorageReserveCertification.model_validate(self.model_dump(exclude={"reserve"}))


class Symmetry(AntaresBaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    reserves: ReserveSymmetry


_AreaAssetCertification = _ThermalCertification | _StorageCertification
CertificationT = TypeVar("CertificationT", bound=_AreaAssetCertification)


class Participation(ABC, AntaresBaseModel, Generic[CertificationT]):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    certifications: list[CertificationT] = []
    symmetries: list[Symmetry] = []

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Forbid reserve duplication
        if len(self.certifications) != len({certification.reserve for certification in self.certifications}):
            raise ValueError(f"Some reserves are duplicated for {self.get_id()}")

        return self

    @abstractmethod
    def get_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def set_id(self, id: str) -> None:
        raise NotImplementedError


class ThermalParticipation(Participation[_ThermalCertification]):
    cluster: str

    @override
    def get_id(self) -> str:
        return self.cluster

    @override
    def set_id(self, id: str) -> None:
        self.cluster = id


class STStorageParticipation(Participation[_StorageCertification]):
    storage: str

    @override
    def get_id(self) -> str:
        return self.storage

    @override
    def set_id(self, id: str) -> None:
        self.storage = id


ParticipationT = TypeVar("ParticipationT", bound=Participation[Any])


class _AreaAssetParticipationFileData(ABC, AntaresBaseModel, Generic[ParticipationT]):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    participations: list[ParticipationT]

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        # Forbid asset duplication
        self._detect_duplicated_assets()

        # Transform assets ids
        for participation in self.participations:
            participation.set_id(transform_name_to_id(participation.get_id()))

        return self

    @abstractmethod
    def _detect_duplicated_assets(self) -> None:
        raise NotImplementedError

    def get_symmetries(self) -> dict[str, ReserveSymmetries]:
        result = {}
        for participation in self.participations:
            symmetries = []
            for symmetry in participation.symmetries:
                symmetries.append(symmetry.reserves)
            if symmetries:
                result[participation.get_id()] = symmetries
        return result

    @classmethod
    def _reorganize_certifications(
        cls, certifications: Mapping[ReserveDefinitionId, Mapping[str, ReserveCertification]]
    ) -> dict[str, dict[ReserveDefinitionId, ReserveCertification]]:
        # Reorganize certifications to order them by id.

        reorganized_certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]] = {}
        for reserve_id, value in certifications.items():
            for asset_id, certification in value.items():
                reorganized_certifications.setdefault(asset_id, {})[reserve_id] = certification
        return reorganized_certifications

    @classmethod
    def from_model(
        cls,
        symmetries: dict[str, ReserveSymmetries],
        certifications: Mapping[ReserveDefinitionId, Mapping[str, ReserveCertification]],
    ) -> Self:
        reorganized_certifications = cls._reorganize_certifications(certifications)

        participations: list[dict[str, Any]] = []
        cls._build_participations_from_symmetries(participations, symmetries, reorganized_certifications)

        # Iterate through certifications with an id not in symmetries
        cls._iterate_through_certifications(participations, reorganized_certifications)

        return cls.model_validate({"participations": participations})

    @classmethod
    def _iterate_through_certifications(
        cls,
        participations: list[Any],
        certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]],
    ) -> None:
        for cluster_id, values in certifications.items():
            participation: dict[str, Any] = cls.initialize_participation(cluster_id)
            if values:
                participation["certifications"] = [{"reserve": r_id, **c.model_dump()} for r_id, c in values.items()]
            participations.append(participation)

    @classmethod
    @abstractmethod
    def initialize_participation(cls, cluster_id: str) -> dict[str, str]:
        raise NotImplementedError

    @classmethod
    def _build_participations_from_symmetries(
        cls,
        participations: list[Any],
        symmetries: dict[str, list[list[ReserveDefinitionId]]],
        certifications: dict[str, dict[ReserveDefinitionId, ReserveCertification]],
    ) -> None:
        """
        Builds a participation entry for every asset that has symmetries, appending it to `participations`.

        This method is in charge of silently ignoring symmetries that have no associated certifications.
        """
        for asset_id, reserve_symmetries in symmetries.items():
            participation: dict[str, Any] = cls.initialize_participation(asset_id)

            if asset_id in certifications:
                if certifs := certifications.pop(asset_id):
                    certification = [{"reserve": r_id, **c.model_dump()} for r_id, c in certifs.items()]
                    participation["certifications"] = certification

                if any(symmetry for symmetry in reserve_symmetries):
                    symmetries_with_certification = [
                        [reserve_id for reserve_id in symmetry if reserve_id in certifs]
                        for symmetry in reserve_symmetries
                    ]
                    participation["symmetries"] = [{"reserves": s} for s in symmetries_with_certification if len(s) > 1]

            participations.append(participation)


class ThermalReserveParticipationsFileData(_AreaAssetParticipationFileData[ThermalParticipation]):
    @override
    def _detect_duplicated_assets(self) -> None:
        if len(self.participations) != len({p.cluster for p in self.participations}):
            raise ValueError("Some thermals are duplicated")

    def get_certifications(self) -> dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]]:
        result: dict[ReserveDefinitionId, dict[str, ThermalReserveCertification]] = {}
        for participation in self.participations:
            for certification in participation.certifications:
                model = certification.to_model()
                reserve_id = ReserveDefinitionId(transform_name_to_id(certification.reserve))
                result.setdefault(reserve_id, {})[participation.cluster] = model
        return result

    @classmethod
    @override
    def initialize_participation(cls, cluster_id: str) -> dict[str, str]:
        return {"cluster": cluster_id}


class STStorageReserveParticipationsFileData(_AreaAssetParticipationFileData[STStorageParticipation]):
    @override
    def _detect_duplicated_assets(self) -> None:
        if len(self.participations) != len({p.storage for p in self.participations}):
            raise ValueError("Some short-term storages are duplicated")

    def get_certifications(self) -> dict[ReserveDefinitionId, dict[str, StorageReserveCertification]]:
        result: dict[ReserveDefinitionId, dict[str, StorageReserveCertification]] = {}
        for participation in self.participations:
            for certification in participation.certifications:
                model = certification.to_model()
                reserve_id = ReserveDefinitionId(transform_name_to_id(certification.reserve))
                result.setdefault(reserve_id, {})[participation.storage] = model
        return result

    @classmethod
    @override
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


def parse_st_storage_reserves_certifications(
    data: dict[str, Any],
) -> dict[ReserveDefinitionId, dict[str, StorageReserveCertification]]:
    return STStorageReserveParticipationsFileData.model_validate(data).get_certifications()


def serialize_st_storage_reserve_participations(
    symmetries: dict[str, ReserveSymmetries],
    certifications: dict[ReserveDefinitionId, dict[str, StorageReserveCertification]],
) -> dict[str, Any]:
    model = STStorageReserveParticipationsFileData.from_model(symmetries, certifications)
    # `exclude_unset` allows us to remove empty lists as they won't be written correctly in the file.
    return model.model_dump(mode="json", by_alias=True, exclude_unset=True)


def parse_st_storage_reserves_symmetries(data: dict[str, Any]) -> dict[str, ReserveSymmetries]:
    return STStorageReserveParticipationsFileData.model_validate(data).get_symmetries()
