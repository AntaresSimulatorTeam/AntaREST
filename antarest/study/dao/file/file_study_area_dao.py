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
from typing import Mapping

from typing_extensions import override

from antarest.core.exceptions import ConfigFileNotFound
from antarest.study.business.model.area_model import ALL_AREAS_PATH, THERMAL_AREAS_PATH, AreaOutput
from antarest.study.dao.api.area_dao import AreaDao
from antarest.study.storage.rawstudy.model.filesystem.config.area import AreaFileData, ThermalAreasProperties
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAreaDao(AreaDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_area_props(self) -> Mapping[str, AreaOutput]:
        file_study = self.get_file_study()

        # Get the area information from the `/input/areas/<area>` file.
        try:
            areas_cfg = file_study.tree.get(ALL_AREAS_PATH, depth=5)
        except KeyError:
            raise ConfigFileNotFound("/".join(ALL_AREAS_PATH)) from None
        else:
            # "list" and "sets" must be removed: we only need areas.
            areas_cfg.pop("list", None)
            areas_cfg.pop("sets", None)

        # Get the unserverd and spilled energy costs from the `/input/thermal/areas.ini` file.
        try:
            thermal_cfg = file_study.tree.get(THERMAL_AREAS_PATH, depth=3)
        except KeyError:
            raise ConfigFileNotFound("/".join(THERMAL_AREAS_PATH)) from None
        else:
            thermal_areas = ThermalAreasProperties(**thermal_cfg)

        # areas_cfg contains a dictionary where the keys are the area IDs,
        # and the values are objects that can be converted to `AreaFolder`.
        area_map = {}
        for area_id, area_cfg in areas_cfg.items():
            area_folder = AreaFileData(**area_cfg)
            area_map[area_id] = AreaOutput.from_model(
                area_folder,
                average_unsupplied_energy_cost=thermal_areas.unserverd_energy_cost.get(area_id, 0.0),
                average_spilled_energy_cost=thermal_areas.spilled_energy_cost.get(area_id, 0.0),
            )

        return area_map
