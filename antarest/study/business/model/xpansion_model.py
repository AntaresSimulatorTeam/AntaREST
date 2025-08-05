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
from typing import Annotated, Optional, TypeAlias

from pydantic import BeforeValidator, Field, PlainSerializer

from antarest.core.exceptions import (
    BadCandidateFormatError,
    CandidateNameIsEmpty,
    IllegalCharacterInNameError,
    WrongLinkFormatError,
)
from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.enum_ignore_case import EnumIgnoreCase


class XpansionResourceFileType(EnumIgnoreCase):
    CAPACITIES = "capacities"
    WEIGHTS = "weights"
    CONSTRAINTS = "constraints"


class UcType(EnumIgnoreCase):
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(EnumIgnoreCase):
    INTEGER = "integer"
    RELAXED = "relaxed"


class Solver(EnumIgnoreCase):
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


class XpansionSensitivitySettings(AntaresBaseModel):
    """
    A DTO representing the sensitivity analysis settings used for Xpansion.

    The sensitivity analysis is optional.

    Attributes:
        epsilon: Max deviation from optimum (€).
        projection: List of candidate names to project (the candidate names should be in "candidates.ini" file).
        capex: Whether to include CAPEX in the sensitivity analysis.
    """

    epsilon: float = Field(default=0, ge=0)
    projection: list[str] = Field(default_factory=list)
    capex: bool = Field(default=False)


class XpansionSensitivitySettingsUpdate(AntaresBaseModel):
    """
    Represents an update of the xpansion sensitivity settings.

    Only not-None fields will be used to update the settings.
    """

    epsilon: float | None = Field(default=None, ge=0)
    projection: list[str] | None = None
    capex: bool | None = None


class XpansionSettings(AntaresBaseModel, extra="ignore", validate_assignment=True, populate_by_name=True):
    """
    A data transfer object representing the general settings used for Xpansion.
    See https://antares-xpansion.readthedocs.io/en/stable/user-guide/get-started/settings-definition

    Attributes:
        optimality_gap: Tolerance on absolute gap for the solution.
        max_iteration: Maximum number of Benders iterations for the solver.
        uc_type: Unit-commitment type used by Antares for the solver.
        master: Resolution mode of the master problem for the solver.
        yearly_weights: Path of the Monte-Carlo weights file for the solution.
        additional_constraints: Path of the additional constraints file for the solution.
        relaxed_optimality_gap: Threshold to switch from relaxed to integer master.
        relative_gap: Tolerance on relative gap for the solution.
        batch_size: Amount of batches in the Benders decomposition.
        separation_parameter: The separation parameter used in the Benders decomposition.
        solver: The solver used to solve the master and the sub-problems in the Benders decomposition.
        timelimit: The timelimit (in seconds) of the Benders step.
        log_level: The severity of the solver's logs in range [0, 3].
        sensitivity_config: The sensitivity analysis configuration for Xpansion, if any.
    """

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
    # (deprecated field)
    timelimit: int = int(1e12)
    sensitivity_config: XpansionSensitivitySettings = XpansionSensitivitySettings()


class XpansionSettingsUpdate(AntaresBaseModel, extra="ignore", validate_assignment=True, populate_by_name=True):
    """
    DTO object used to update the Xpansion settings.

    Fields with a value of `None` are ignored, this allows a partial update of the settings.
    For that reason the fields "yearly-weights" and "additional-constraints" must
    be set to "" instead of `None` if you want to remove the file.
    """

    master: Master | None = None
    uc_type: UcType | None = None
    optimality_gap: float | None = Field(default=None, ge=0)
    relative_gap: float | None = Field(default=None, ge=0)
    relaxed_optimality_gap: float | None = Field(default=None, ge=0)
    max_iteration: int | None = Field(default=None, gt=0)
    solver: Solver | None = None
    log_level: int | None = Field(default=None, ge=0, le=3)
    separation_parameter: float | None = Field(default=None, gt=0, le=1)
    batch_size: int | None = Field(default=None, ge=0)
    yearly_weights: str | None = None
    additional_constraints: str | None = None
    timelimit: int | None = None
    sensitivity_config: XpansionSensitivitySettingsUpdate | None = None


def update_xpansion_settings(settings: XpansionSettings, data: XpansionSettingsUpdate) -> XpansionSettings:
    """
    Updates the xpansion settings according to the provided update data.
    """
    current_settings = settings.model_dump(mode="json")
    update_settings = data.model_dump(mode="json", exclude_none=True)
    if "sensitivity_config" in update_settings:
        current_settings["sensitivity_config"].update(update_settings.pop("sensitivity_config"))
    current_settings.update(update_settings)
    return XpansionSettings.model_validate(current_settings)


##########################
# Candidates part
##########################


class XpansionLink(AntaresBaseModel):
    area_from: str
    area_to: str

    def serialize(self) -> str:
        return f"{self.area_from} - {self.area_to}"


def split_areas(x: str) -> dict[str, str]:
    if " - " not in x:
        raise WrongLinkFormatError(f"The link must be in the format 'area1 - area2'. Currently: {x}")
    area_list = sorted(x.split(" - "))
    return {"area_from": area_list[0], "area_to": area_list[1]}


# link parsed and serialized as "area1 - area2"
XpansionLinkStr: TypeAlias = Annotated[
    XpansionLink,
    BeforeValidator(lambda x: split_areas(x)),
    PlainSerializer(lambda x: x.serialize()),
]


def _validate_candidate_name(name: str) -> str:
    # The name is written directly inside the ini file so a specific check is performed here
    if name.strip() == "":
        raise CandidateNameIsEmpty()

    illegal_name_characters = [" ", "\n", "\t", "\r", "\f", "\v", "-", "+", "=", ":", "[", "]", "(", ")"]
    for char in name:
        if char in illegal_name_characters:
            raise IllegalCharacterInNameError(f"The character '{char}' is not allowed in the candidate name")

    return name


CandidateName: TypeAlias = Annotated[str, BeforeValidator(_validate_candidate_name)]


class XpansionCandidate(AntaresBaseModel, populate_by_name=True, alias_generator=to_kebab_case):
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


class XpansionCandidateCreation(AntaresBaseModel, populate_by_name=True, alias_generator=to_kebab_case):
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


def validate_xpansion_candidate(candidate: XpansionCandidate) -> None:
    possible_format_1 = candidate.max_investment is None and (
        candidate.max_units is not None and candidate.unit_size is not None
    )
    possible_format_2 = candidate.max_investment is not None and (
        candidate.max_units is None and candidate.unit_size is None
    )

    if not (possible_format_1 or possible_format_2):
        raise BadCandidateFormatError(
            "The candidate is not well formatted."
            "\nIt should either contain max-investment or (max-units and unit-size)."
        )


def create_xpansion_candidate(candidate_data: XpansionCandidateCreation) -> XpansionCandidate:
    """
    Creates a candidate from a creation request, checking and initializing it against the specified study version.
    """
    candidate = XpansionCandidate.model_validate(candidate_data.model_dump(exclude_none=True))
    validate_xpansion_candidate(candidate)
    return candidate
