# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from typing import Any, Optional

from pydantic import ConfigDict, Field, field_validator

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.xpansion_model import (
    CandidateName,
    Master,
    Solver,
    UcType,
    XpansionCandidate,
    XpansionLinkStr,
    XpansionSensitivitySettings,
    XpansionSettings,
    validate_xpansion_candidate,
)


class XpansionCandidateFileData(AntaresBaseModel):
    """
    Xpansion candidate data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_kebab_case)

    name: CandidateName
    link: XpansionLinkStr
    annual_cost_per_mw: float = Field(ge=0)
    unit_size: Optional[float] = Field(default=None, ge=0)
    max_units: Optional[int] = Field(default=None, ge=0)
    max_investment: Optional[float] = Field(default=None, ge=0)
    already_installed_capacity: Optional[int] = Field(default=None, ge=0)
    # this is obsolete (replaced by direct/indirect)
    link_profile: Optional[str] = None
    # this is obsolete (replaced by direct/indirect)
    already_installed_link_profile: Optional[str] = None
    direct_link_profile: Optional[str] = None
    indirect_link_profile: Optional[str] = None
    already_installed_direct_link_profile: Optional[str] = None
    already_installed_indirect_link_profile: Optional[str] = None

    def to_model(self) -> XpansionCandidate:
        return XpansionCandidate.model_validate(self.model_dump(exclude_none=True))

    @classmethod
    def from_model(cls, candidate: XpansionCandidate) -> "XpansionCandidateFileData":
        return cls.model_validate(candidate.model_dump())


def parse_xpansion_candidate(data: Any) -> XpansionCandidate:
    candidate = XpansionCandidateFileData.model_validate(data).to_model()
    validate_xpansion_candidate(candidate)
    return candidate


def serialize_xpansion_candidate(candidate: XpansionCandidate) -> dict[str, Any]:
    validate_xpansion_candidate(candidate)
    return XpansionCandidateFileData.from_model(candidate).model_dump(mode="json", by_alias=True, exclude_none=True)


##########################
# Settings part
##########################


class XpansionSettingsFileData(AntaresBaseModel):
    """
    Xpansion settings data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    master: Master = Field(default=Master.INTEGER)
    uc_type: UcType = Field(default=UcType.EXPANSION_FAST)
    optimality_gap: float = Field(default=1, ge=0)
    relative_gap: float = Field(default=1e-6, ge=0)
    relaxed_optimality_gap: float = Field(default=1e-5, ge=0)
    max_iteration: int = Field(default=int(1e12), gt=0)
    solver: Solver = Field(default=Solver.XPRESS)
    log_level: int = Field(default=0, ge=0, le=3)
    separation_parameter: float = Field(default=0.5, gt=0, le=1)
    batch_size: int = Field(default=96, ge=0)
    yearly_weights: str = Field("", alias="yearly-weights")
    additional_constraints: str = Field("", alias="additional-constraints")
    timelimit: int = int(1e12)

    @field_validator("max_iteration", mode="before")
    def validate_max_iteration(cls, data: Any) -> Any:
        if isinstance(data, str) and data.lower() == "+inf":
            data = int(1e12)
        return data

    def to_model(self) -> XpansionSettings:
        return XpansionSettings.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, settings: XpansionSettings) -> "XpansionSettingsFileData":
        return cls.model_validate(settings.model_dump(exclude={"sensitivity_config"}))


def parse_xpansion_settings(data: Any) -> XpansionSettings:
    return XpansionSettingsFileData.model_validate(data).to_model()


def serialize_xpansion_settings(settings: XpansionSettings) -> dict[str, Any]:
    data = XpansionSettingsFileData.from_model(settings).model_dump(by_alias=True)
    # Exclude `yearly-weights` and `additional-constraints` if they are an empty str
    for field in ["yearly-weights", "additional-constraints"]:
        if not data[field]:
            del data[field]
    return data


class XpansionSensitivitySettingsFileData(AntaresBaseModel):
    """
    Xpansion sensitivity settings data parsed from INI file.
    """

    model_config = ConfigDict(extra="forbid")

    epsilon: float = Field(default=0, ge=0)
    projection: list[str] = Field(default_factory=list)
    capex: bool = Field(default=False)

    def to_model(self) -> XpansionSensitivitySettings:
        return XpansionSensitivitySettings.model_validate(self.model_dump())

    @classmethod
    def from_model(cls, settings: XpansionSensitivitySettings) -> "XpansionSensitivitySettingsFileData":
        return cls.model_validate(settings.model_dump())


def parse_xpansion_sensitivity_settings(data: Any) -> XpansionSensitivitySettings:
    return XpansionSensitivitySettingsFileData.model_validate(data).to_model()


def serialize_xpansion_sensitivity_settings(settings: XpansionSensitivitySettings) -> dict[str, Any]:
    return XpansionSensitivitySettingsFileData.from_model(settings).model_dump(by_alias=True)
