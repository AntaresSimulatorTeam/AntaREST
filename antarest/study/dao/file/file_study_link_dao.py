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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Sequence

from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import (
    Link,
)
from antarest.study.storage.rawstudy.model.filesystem.config.link import parse_link, serialize_link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy

if TYPE_CHECKING:
    pass
from antarest.study.dao.api.link_dao import LinkDao
from antarest.study.model import STUDY_VERSION_8_2


class FileStudyLinkDao(LinkDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_links(self) -> Sequence[Link]:
        file_study = self.get_file_study()
        result: List[Link] = []

        for area_from, area in file_study.config.areas.items():
            area_links = file_study.tree.get(["input", "links", area_from, "properties"])
            for area_to, link_data in area_links.items():
                result.append(parse_link(link_data, area_from, area_to))
        return result

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        file_study = self.get_file_study()
        try:
            area1_id, area2_id = sorted((area1_id, area2_id))
            file_study.tree.get(["input", "links", area1_id, "properties", area2_id])
            return True
        except KeyError:
            return False

    @override
    def get_link(self, area1_id: str, area2_id: str) -> Link:
        area_from, area_to = sorted((area1_id, area2_id))
        file_study = self.get_file_study()
        try:
            area_links = file_study.tree.get(["input", "links", area_from, "properties", area_to])
            return parse_link(area_links, area_from, area_to)
        except KeyError:
            raise LinkNotFound(f"The link {area_from} -> {area_to} is not present in the study")

    @override
    def save_link(self, link: Link) -> None:
        study_data = self.get_file_study()
        self._update_link_config(link.area1, link.area2, link)

        study_data.tree.save(serialize_link(link), ["input", "links", link.area1, "properties", link.area2])

    def _update_link_config(self, area1_id: str, area2_id: str, link: Link) -> None:
        study_data = self.get_file_study().config
        if area1_id not in study_data.areas:
            raise ValueError(f"The area '{area1_id}' does not exist")
        if area2_id not in study_data.areas:
            raise ValueError(f"The area '{area2_id}' does not exist")

        area_from, area_to = sorted([area1_id, area2_id])
        study_data.areas[area_from].links[area_to] = link

    @override
    def save_link_series(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self.get_file_study()
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version < STUDY_VERSION_8_2:
            study_data.tree.save(series_id, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(series_id, ["input", "links", area_from, f"{area_to}_parameters"])

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self.get_file_study()
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(series_id, ["input", "links", area_from, "capacities", f"{area_to}_direct"])

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self.get_file_study()
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(series_id, ["input", "links", area_from, "capacities", f"{area_to}_indirect"])

    @override
    def delete_link(self, link: Link) -> None:
        study_data = self.get_file_study()

        if study_data.config.version < STUDY_VERSION_8_2:
            study_data.tree.delete(["input", "links", link.area1, link.area2])
        else:
            study_data.tree.delete(["input", "links", link.area1, f"{link.area2}_parameters"])
            study_data.tree.delete(["input", "links", link.area1, "capacities", f"{link.area2}_direct"])
            study_data.tree.delete(["input", "links", link.area1, "capacities", f"{link.area2}_indirect"])

        study_data.tree.delete(["input", "links", link.area1, "properties", link.area2])

        del study_data.config.areas[link.area1].links[link.area2]
        self._remove_link_from_scenario_builder(link)

    def _remove_link_from_scenario_builder(self, link: Link) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the link to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        study_data = self.get_file_study()
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,area1,area2,year".
                symbol, *parts = key.split(",")
                if symbol == "ntc" and parts[0] == link.area1 and parts[1] == link.area2:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])
