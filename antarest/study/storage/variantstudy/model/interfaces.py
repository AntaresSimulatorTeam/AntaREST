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

import abc
from abc import abstractmethod
from typing import TYPE_CHECKING, List, Optional, Tuple

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.filestudytree import FileStudyTree

if TYPE_CHECKING:
    # avoid circular import
    from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class ICommandExtractor(abc.ABC):
    @abstractmethod
    def extract_area(self, study: FileStudy, area_id: str) -> Tuple[List["ICommand"], List["ICommand"]]:
        raise NotImplementedError()

    @abstractmethod
    def extract_link(
        self,
        study: FileStudy,
        area1: str,
        area2: str,
        links_data: Optional[JSON] = None,
    ) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_cluster(self, study: FileStudy, area_id: str, thermal_id: str) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_renewables_cluster(self, study: FileStudy, area_id: str, thermal_id: str) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_hydro(self, study: FileStudy, area_id: str) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_district(self, study: FileStudy, district_id: str) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_comments(self, study: FileStudy) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def extract_binding_constraint(
        self,
        study: FileStudy,
        binding_id: str,
        bindings_data: Optional[JSON] = None,
    ) -> List["ICommand"]:
        raise NotImplementedError()

    @abstractmethod
    def generate_update_config(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> "ICommand":
        raise NotImplementedError()

    @abstractmethod
    def generate_update_raw_file(
        self,
        study_tree: FileStudyTree,
        url: List[str],
    ) -> "ICommand":
        raise NotImplementedError()

    @abstractmethod
    def generate_update_comments(
        self,
        study_tree: FileStudyTree,
    ) -> "ICommand":
        raise NotImplementedError()

    @abstractmethod
    def generate_replace_matrix(
        self,
        study_tree: FileStudyTree,
        url: List[str],
        default_value: Optional[str] = None,
    ) -> "ICommand":
        raise NotImplementedError()
