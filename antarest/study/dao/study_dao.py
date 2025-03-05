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
from typing import Any, Dict, List, Sequence

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import (
    LinkDTO,
    LinkInternal,
    LinkProperties,
)
from antarest.study.model import STUDY_VERSION_8_2
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class ReadOnlyStudyDao(ABC):
    @abstractmethod
    def get_version(self) -> StudyVersion:
        raise NotImplementedError()

    @abstractmethod
    def get_links(self) -> Sequence[LinkDTO]:
        raise NotImplementedError()

    @abstractmethod
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        raise NotImplementedError()

    @abstractmethod
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        raise NotImplementedError()


class StudyDao(ReadOnlyStudyDao):
    def read_only(self) -> ReadOnlyStudyDao:
        return ReadOnlyAdapter(self)

    @abstractmethod
    def as_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()

    @abstractmethod
    def save_link(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update_link_config(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def save_link_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        raise NotImplementedError()


class ReadOnlyAdapter(ReadOnlyStudyDao):
    def __init__(self, adaptee: StudyDao):
        self._adaptee = adaptee

    @override
    def get_version(self) -> StudyVersion:
        return self._adaptee.get_version()

    @override
    def get_links(self) -> Sequence[LinkDTO]:
        return self._adaptee.get_links()

    @override
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        return self._adaptee.get_link(area1_id, area2_id)

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return self._adaptee.link_exists(area1_id, area2_id)


class FileStudyTreeDao(StudyDao):
    def __init__(self, study: FileStudy) -> None:
        self._file_study = study

    @override
    def as_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        return self._file_study

    @override
    def get_version(self) -> StudyVersion:
        return self._file_study.config.version

    @override
    def get_links(self) -> Sequence[LinkDTO]:
        file_study = self._file_study
        result: List[LinkDTO] = []

        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])

            for link in area.links:
                link_tree_config: Dict[str, Any] = links_config[link]
                link_tree_config.update({"area1": area_id, "area2": link})
                link_internal = LinkInternal.model_validate(link_tree_config)
                result.append(link_internal.to_dto())
        return result

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        file_study = self._file_study
        try:
            area1_id, area2_id = sorted((area1_id, area2_id))
            file_study.tree.get(["input", "links", area1_id, "properties", area2_id])
            return True
        except KeyError:
            return False

    @override
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        file_study = self._file_study
        try:
            props = file_study.tree.get(["input", "links", area1_id, "properties", area2_id])
        except KeyError:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")
        props.update({"area1": area1_id, "area2": area2_id})
        return LinkInternal.model_validate(props).to_dto()

    @override
    def save_link(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        study_data = self._file_study
        version = study_data.config.version
        area1_id, area2_id = sorted((area1_id, area2_id))
        self.update_link_config(area1_id, area2_id, link)
        to_exclude = {"area1", "area2"}
        if version < STUDY_VERSION_8_2:
            to_exclude.update("filter-synthesis", "filter-year-by-year")

        link_properties = LinkProperties.from_link(link)

        study_data.tree.save(
            link_properties.model_dump(by_alias=True),
            ["input", "links", area1_id, "properties", area2_id],
        )

    @override
    def update_link_config(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        study_data = self._file_study.config
        if area1_id not in study_data.areas:
            raise ValueError(f"The area '{area1_id}' does not exist")
        if area2_id not in study_data.areas:
            raise ValueError(f"The area '{area2_id}' does not exist")

        area_from, area_to = sorted([area1_id, area2_id])
        study_data.areas[area_from].links[area_to] = link.to_config()

    @override
    def save_link_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self._file_study
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version < STUDY_VERSION_8_2:
            study_data.tree.save(series_id, ["input", "links", area_from, area_to])
        else:
            study_data.tree.save(
                series_id,
                ["input", "links", area_from, f"{area_to}_parameters"],
            )

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self._file_study
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(
                series_id,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_direct",
                ],
            )

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        study_data = self._file_study
        version = study_data.config.version
        area_from, area_to = sorted((area_from, area_to))
        if version >= STUDY_VERSION_8_2:
            study_data.tree.save(
                series_id,
                [
                    "input",
                    "links",
                    area_from,
                    "capacities",
                    f"{area_to}_indirect",
                ],
            )
