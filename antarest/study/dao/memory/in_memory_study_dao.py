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

from dataclasses import dataclass
from typing import Dict, Sequence

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import LinkNotFound
from antarest.study.business.model.link_model import (
    LinkDTO,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


@dataclass(frozen=True)
class LinkKey:
    area1_id: str
    area2_id: str


def link_key(area1_id: str, area2_id: str) -> LinkKey:
    area1_id, area2_id = sorted((area1_id, area2_id))
    return LinkKey(area1_id, area2_id)


class InMemoryStudyDao(StudyDao):
    """
    In memory implementation of study DAO, mainly for testing purposes.
    TODO, warning: no version handling, no check on areas, no checks on matrices ...
    """

    def __init__(self, version: StudyVersion) -> None:
        self._version = version
        self._links: Dict[LinkKey, LinkDTO] = {}
        self._link_capacities: Dict[LinkKey, str] = {}
        self._link_direct_capacities: Dict[LinkKey, str] = {}
        self._link_indirect_capacities: Dict[LinkKey, str] = {}

    @override
    def as_file_study(self) -> FileStudy:
        """
        To ease transition, to be removed when all goes through other methods
        """
        raise NotImplementedError()

    @override
    def get_version(self) -> StudyVersion:
        return self._version

    @override
    def get_links(self) -> Sequence[LinkDTO]:
        return list(self._links.values())

    @override
    def link_exists(self, area1_id: str, area2_id: str) -> bool:
        return link_key(area1_id, area2_id) in self._links

    @override
    def get_link(self, area1_id: str, area2_id: str) -> LinkDTO:
        try:
            return self._links[link_key(area1_id, area2_id)]
        except KeyError:
            raise LinkNotFound(f"The link {area1_id} -> {area2_id} is not present in the study")

    @override
    def save_link(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        self._links[link_key(area1_id, area2_id)] = link

    @override
    def update_link_config(self, area1_id: str, area2_id: str, link: LinkDTO) -> None:
        self._links[link_key(area1_id, area2_id)] = link

    @override
    def save_link_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_direct_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_direct_capacities[link_key(area_from, area_to)] = series_id

    @override
    def save_link_indirect_capacities(self, area_from: str, area_to: str, series_id: str) -> None:
        self._link_indirect_capacities[link_key(area_from, area_to)] = series_id
