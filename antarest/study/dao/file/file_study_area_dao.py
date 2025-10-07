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
from abc import abstractmethod
from typing import Any, Dict, List

from typing_extensions import override

from antarest.study.business.model.area_model import Area
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAreaDao(AreaDao):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_areas(self) -> List[Area]:
        """
        Retrieve all physical areas of a study.
        """
        raise NotImplementedError()

    @override
    def get_area(self, area_id: str) -> Area:
        """
        Retrieve a specific area by its ID.
        """
        raise NotImplementedError()

    @override
    def area_exists(self, area_id: str) -> bool:
        """
        Check if an area exists in the study.
        """
        raise NotImplementedError()

    @override
    def get_all_areas_ui_info(self) -> Dict[str, Any]:
        """
        Retrieve information about all areas' user interface (UI) from the study.
        """
        raise NotImplementedError()
