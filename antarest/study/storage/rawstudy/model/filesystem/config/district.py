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


from typing import Any, List, Optional

from pydantic import ConfigDict, Field

from antarest.core.serde import AntaresBaseModel
from antarest.study.business.model.district_model import District


class DistrictFileData(AntaresBaseModel):
    """
    Object linked to /inputs/sets.ini information
    """

    caption: Optional[str] = None
    apply_filter: Optional[str] = Field(None, alias="apply-filter")
    add_areas: Optional[List[str]] = Field(None, alias="+")
    subtract_areas: Optional[List[str]] = Field(None, alias="-")
    output: bool = True
    comments: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )

    def get_areas(self, all_areas: List[str]) -> List[str]:
        add_areas_set = set(self.add_areas or [])
        subtract_areas_set = set(self.subtract_areas or [])
        apply_filter = self.apply_filter or "remove-all"
        base_areas = set(all_areas) if apply_filter == "add-all" else set()
        areas = list(base_areas.union(add_areas_set).difference(subtract_areas_set))
        return sorted(areas)

    @classmethod
    def from_model(cls, district: District) -> "DistrictFileData":
        return DistrictFileData.model_validate(
            {
                **district.model_dump(include={"output", "comments", "add_areas", "subtract_areas", "apply_filter"}),
                "caption": district.name,
            }
        )

    @classmethod
    def from_data(cls, data: Any, district_id: str) -> "DistrictFileData":
        return DistrictFileData.model_validate(
            {
                "caption": data.get("caption", district_id),
                "output": data.get("output", True),
                "comments": data.get("comments", None),
                "apply_filter": data.get("apply-filter", None),
                "add_areas": data.get("+", None),
                "subtract_areas": data.get("-", None),
            }
        )

    def to_model(self, district_id: str) -> District:
        return District.model_validate(
            {
                **self.model_dump(
                    include={"output", "comments", "add_areas", "subtract_areas", "apply_filter"}, exclude_none=True
                ),
                "name": self.caption,
                "id": district_id,
            }
        )


def parse_district(item: dict[str, Any], district_id: str) -> District:
    return DistrictFileData.from_data(item, district_id).to_model(district_id)


def serialize_district(district: District) -> dict[str, Any]:
    district_file_data = DistrictFileData.from_model(district)
    district_dict = district_file_data.model_dump(exclude_none=True, mode="json", by_alias=True)

    # Drop "-" and "+" if empty list
    if not district_file_data.add_areas:
        district_dict.pop("+", None)
    if not district_file_data.subtract_areas:
        district_dict.pop("-", None)

    return district_dict
