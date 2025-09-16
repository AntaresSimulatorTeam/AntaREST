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


from typing import Any, List, Optional

from typing_extensions import Literal

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.district_model import District, DistrictBaseFilter


class DistrictSet(AntaresBaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    name: Optional[str] = None
    inverted_set: bool = False
    areas: Optional[List[str]] = None
    output: bool = True
    comments: Optional[str] = None

    def get_areas(self, all_areas: List[str]) -> List[str]:
        areas = self.areas or []
        if self.inverted_set:
            areas = list(set(all_areas).difference(set(areas)))
        return sorted(areas)

    @classmethod
    def from_model(cls, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> "DistrictSet":
        base_filter = district_base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        return DistrictSet.model_validate(
            {
                **district.model_dump(include={"name", "output", "comments", "areas"}),
                "inverted_set": inverted_set,
            }
        )

    @classmethod
    def from_data(cls, data: Any) -> "DistrictSet":
        inverted_set = district_set_sign_from_data(data) == "-"
        areas = data.get("-", []) if inverted_set else data.get("+", [])
        return DistrictSet.model_validate(
            {
                "name": data.get("caption", None),
                "output": data.get("output", True),
                "comments": data.get("comments", ""),
                "inverted_set": inverted_set,
                "areas": sorted(areas),
            }
        )

    def to_model(self, district_id: str, all_areas: List[str]) -> District:
        return District.model_validate(
            {
                "id": district_id,
                "name": self.name,
                "areas": self.get_areas(all_areas),
                "output": self.output,
                "comments": self.comments or "",
            }
        )


def district_set_sign_from_data(item: dict[str, Any]) -> str:
    if "apply-filter" not in item:
        return "+"
    base_filter = DistrictBaseFilter(item["apply-filter"])
    return district_set_sign_from_base_filter(base_filter)


def district_set_sign_from_base_filter(district_base_filter: Optional[DistrictBaseFilter]) -> Literal["+", "-"]:
    if district_base_filter is None:
        return "+"
    if district_base_filter == DistrictBaseFilter.remove_all:
        return "+"
    return "-"
