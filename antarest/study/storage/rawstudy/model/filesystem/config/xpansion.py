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

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.core.utils.string import to_kebab_case
from antarest.study.business.model.xpansion_model import (
    CandidateName,
    XpansionCandidate,
    XpansionLinkStr,
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
