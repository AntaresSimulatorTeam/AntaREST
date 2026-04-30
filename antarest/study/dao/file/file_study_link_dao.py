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
from collections.abc import Sequence
from typing import TYPE_CHECKING, Callable

import polars as pl
from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import (
    Link,
)
from antarest.study.dao.api.link_dao import LinkDao
from antarest.study.dao.common import AreaId, LinkSeriesMapping
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.config.link import parse_link, serialize_link
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_series_before_v82_matrix_path(area_from: AreaId, area_to: AreaId) -> list[str]:
    return ["input", "links", area_from, area_to]


def _get_series_after_v82_matrix_path(area_from: AreaId, area_to: AreaId) -> list[str]:
    return ["input", "links", area_from, f"{area_to}_parameters"]


def _get_direct_capacity_matrix_path(area_from: AreaId, area_to: AreaId) -> list[str]:
    return ["input", "links", area_from, "capacities", f"{area_to}_direct"]


def _get_indirect_capacity_matrix_path(area_from: AreaId, area_to: AreaId) -> list[str]:
    return ["input", "links", area_from, "capacities", f"{area_to}_indirect"]


class FileStudyLinkDao(LinkDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_links(self) -> Sequence[Link]:
        file_study = self.get_file_study()
        result: list[Link] = []

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
    def get_link_indirect_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        area_from, area_to = sorted((area_from, area_to))
        url = _get_indirect_capacity_matrix_path(area_from, area_to)
        return self.get_impl().get_matrix(url)

    @override
    def get_link_direct_capacities(self, area_from: str, area_to: str) -> pl.DataFrame:
        area_from, area_to = sorted((area_from, area_to))
        url = _get_direct_capacity_matrix_path(area_from, area_to)
        return self.get_impl().get_matrix(url)

    @override
    def get_link_series(self, area_from: str, area_to: str) -> pl.DataFrame:
        version = self.get_impl().get_version()
        area_from, area_to = sorted((area_from, area_to))
        if version < STUDY_VERSION_8_2:
            url = _get_series_before_v82_matrix_path(area_from, area_to)
        else:
            url = _get_series_after_v82_matrix_path(area_from, area_to)
        return self.get_impl().get_matrix(url)

    @override
    def get_all_links_series(self) -> LinkSeriesMapping:
        version = self.get_impl().get_version()
        if version < STUDY_VERSION_8_2:
            url_getter = _get_series_before_v82_matrix_path
        else:
            url_getter = _get_series_after_v82_matrix_path
        return self._get_link_matrices(url_getter)

    @override
    def get_all_links_indirect_capacities(self) -> LinkSeriesMapping:
        return self._get_link_matrices(_get_indirect_capacity_matrix_path)

    @override
    def get_all_links_direct_capacities(self) -> LinkSeriesMapping:
        return self._get_link_matrices(_get_direct_capacity_matrix_path)

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
    def save_links(self, links: Sequence[Link]) -> None:
        study_data = self.get_file_study()
        for link in links:
            self._update_link_config(link.area1, link.area2, link)
            study_data.tree.save(serialize_link(link), ["input", "links", link.area1, "properties", link.area2])

    def _update_link_config(self, area1_id: str, area2_id: str, link: Link) -> None:
        study_data = self.get_file_study().config
        for area in [area1_id, area2_id]:
            if area not in study_data.areas:
                raise ValueError(f"The area '{area}' does not exist")

        area_from, area_to = sorted([area1_id, area2_id])
        study_data.areas[area_from].links[area_to] = link.to_config()

    def _save_link_matrices(self, series: LinkSeriesMapping, url_getter: Callable[[AreaId, AreaId], list[str]]) -> None:
        matrices_mapping: dict[str, list[MatrixNode]] = {}
        study_data = self.get_file_study()
        for (area_from, area_to), series_id in series.items():
            area_from, area_to = sorted((area_from, area_to))
            url = url_getter(area_from, area_to)
            node = study_data.tree.get_node(url)
            assert isinstance(node, MatrixNode)
            matrix_id = series_id
            matrices_mapping.setdefault(matrix_id, []).append(node)
        self.get_impl().save_matrices(matrices_mapping)

    @override
    def save_link_series(self, series: LinkSeriesMapping) -> None:
        version = self.get_impl().get_version()
        url_getter: Callable[[AreaId, AreaId], list[str]]
        if version < STUDY_VERSION_8_2:
            url_getter = _get_series_before_v82_matrix_path
        else:
            url_getter = _get_series_after_v82_matrix_path
        self._save_link_matrices(series, url_getter)

    @override
    def save_link_direct_capacities(self, series: LinkSeriesMapping) -> None:
        self._save_link_matrices(series, _get_direct_capacity_matrix_path)

    @override
    def save_link_indirect_capacities(self, series: LinkSeriesMapping) -> None:
        self._save_link_matrices(series, _get_indirect_capacity_matrix_path)

    @override
    def delete_link(self, link: Link) -> None:
        study_data = self.get_file_study()

        if study_data.config.version < STUDY_VERSION_8_2:
            study_data.tree.delete(["input", "links", link.area1, link.area2])
        else:
            study_data.tree.delete(_get_series_after_v82_matrix_path(link.area1, link.area2))
            study_data.tree.delete(_get_direct_capacity_matrix_path(link.area1, link.area2))
            study_data.tree.delete(_get_indirect_capacity_matrix_path(link.area1, link.area2))

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

    def _get_link_matrices(self, url_getter: Callable[[AreaId, AreaId], list[str]]) -> LinkSeriesMapping:
        study_data = self.get_file_study()
        matrix_nodes = {}

        areas = study_data.config.areas
        for area_from, value in areas.items():
            for area_to in value.links:
                url = url_getter(area_from, area_to)
                node = study_data.tree.get_node(url)
                assert isinstance(node, MatrixNode)
                matrix_nodes[node] = (area_from, area_to)

        result: LinkSeriesMapping = {}

        matrices_mapping = self.get_impl().get_matrices_ids(list(matrix_nodes))

        for node, matrix_id in matrices_mapping.items():
            area_from, area_to = matrix_nodes[node]
            result[(area_from, area_to)] = matrix_id

        return result
