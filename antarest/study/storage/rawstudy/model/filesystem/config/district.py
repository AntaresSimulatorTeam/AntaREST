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

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.district_model import DistrictApplyFilter, DistrictDefinition


class DistrictSet(AntaresBaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    name: Optional[str] = None
    apply_filter: Optional[str] = None
    add_areas: Optional[List[str]] = None
    substract_areas: Optional[List[str]] = None
    output: bool = True
    comments: Optional[str] = None

    def get_areas(self, all_areas: List[str]) -> List[str]:
        add_areas_set = set(self.add_areas or [])
        substract_areas_set = set(self.substract_areas or [])
        apply_filter = self.apply_filter or "remove-all"
        base_areas = set(all_areas) if apply_filter == "add-all" else set()
        areas = list(base_areas.union(add_areas_set).difference(substract_areas_set))
        return sorted(areas)

    @classmethod
    def from_model(cls, district: DistrictDefinition) -> "DistrictSet":
        return DistrictSet.model_validate(
            district.model_dump(include={"name", "output", "comments", "add_areas", "substract_areas", "apply_filter"}),
        )

    @classmethod
    def from_data(cls, data: Any, district_id: str) -> "DistrictSet":
        return DistrictSet.model_validate(
            {
                "name": data.get("caption", district_id),
                "output": data.get("output", True),
                "comments": data.get("comments", ""),
                "apply_filter": data.get("apply-filter", "remove-all"),
                "add_areas": data.get("+", []),
                "substract_areas": data.get("-", []),
            }
        )

    def to_model(self, district_id: str) -> DistrictDefinition:
        return DistrictDefinition.model_validate({**self.model_dump(), "id": district_id})


def district_set_apply_filter(item: dict[str, Any]) -> DistrictApplyFilter:
    if "apply-filter" not in item:
        return DistrictApplyFilter.remove_all
    return DistrictApplyFilter(item["apply-filter"])
