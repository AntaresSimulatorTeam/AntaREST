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

    ALL: List[str] = ["hourly", "daily", "weekly", "monthly", "annual"]
    name: Optional[str] = None
    inverted_set: bool = False
    areas: Optional[List[str]] = None
    output: bool = True
    filters_synthesis: List[str] = ALL
    filters_year: List[str] = ALL

    def get_areas(self, all_areas: List[str]) -> List[str]:
        areas = self.areas or []
        return get_areas(self.inverted_set, all_areas, areas)

    @classmethod
    def from_model(cls, district: District, district_base_filter: Optional[DistrictBaseFilter]) -> "DistrictSet":
        base_filter = district_base_filter or DistrictBaseFilter.remove_all
        inverted_set = base_filter == DistrictBaseFilter.add_all
        return DistrictSet.model_validate(
            {
                **district.model_dump(include={"name", "output", "comments"}),
                "inverted_set": inverted_set,
                "areas": district.areas,
            }
        )


def district_set_sign(item: dict[str, Any]) -> str:
    if "apply-filter" not in item:
        return "+"
    if item["apply-filter"] == "remove-all":
        return "+"
    return "-"  # "add-all"


def parse_district(district_id: str, data: Any, all_areas: List[str]) -> District:
    inverted_set = district_set_sign(data) == "-"
    areas = data.get("-", []) if inverted_set else data.get("+", [])
    return District.model_validate(
        {
            "id": district_id,
            "name": data["caption"],
            "areas": get_areas(inverted_set, all_areas, areas),
            "output": data["output"],
            "comments": data.get("comments", ""),
        }
    )


def get_areas(inverted_set: bool, all_areas: List[str], areas: list[str]) -> List[str]:
    if inverted_set:
        areas = list(set(all_areas).difference(set(areas)))
    return sorted(areas)


def areas_sign_from_base_filter(district_base_filter: Optional[DistrictBaseFilter]) -> Literal["+", "-"]:
    if district_base_filter is None:
        return "+"
    if district_base_filter == DistrictBaseFilter.remove_all:
        return "+"
    return "-"
