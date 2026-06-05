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

from typing_extensions import override

from antarest.core.exceptions import AreaNotFound, ConfigFileNotFound
from antarest.study.business.model.area_properties_model import (
    AreaProperties,
    sort_filter_options,
)
from antarest.study.dao.api.area_properties_dao import AreaPropertiesDao
from antarest.study.dao.file.common import check_area_exists
from antarest.study.model import STUDY_VERSION_8_3
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPatchFileData,
    AreaFileData,
    AreaPropertiesFileData,
    OptimizationFileData,
    ThermalAreasFileData,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


def get_thermal_path() -> list[str]:
    return ["input", "thermal", "areas"]


def get_area_path() -> list[str]:
    return ["input", "areas"]


def get_optimization_path(area_id: str) -> list[str]:
    return ["input", "areas", area_id, "optimization"]


def get_adequacy_patch_path(area_id: str) -> list[str]:
    return ["input", "areas", area_id, "adequacy_patch"]


class FileStudyAreaPropertiesDao(AreaPropertiesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_area_properties(self, area_id: str) -> AreaProperties:
        file_study = self.get_file_study()
        check_area_exists(file_study.config, area_id)

        current_thermal_props = file_study.tree.get(get_thermal_path())
        current_optim_properties = file_study.tree.get(get_optimization_path(area_id))
        current_adequacy_patch = (
            file_study.tree.get(get_adequacy_patch_path(area_id))
            if file_study.config.version >= STUDY_VERSION_8_3
            else {}
        )

        properties = AreaPropertiesFileData(
            thermal_properties=ThermalAreasFileData(**current_thermal_props),
            optimization_properties=OptimizationFileData(**current_optim_properties),
            adequacy_patch_properties=AdequacyPatchFileData(**current_adequacy_patch),
        )

        return properties.get_area_properties(area_id, file_study.config.version)

    @override
    def get_all_area_properties(self) -> dict[str, AreaProperties]:
        """
        Retrieves all areas properties of a study.

        Args:
            study: The raw study object.
        Returns:
            A mapping of area IDs to area properties.
        Raises:
            ConfigFileNotFound: if a configuration file is not found.
        """
        file_study = self.get_file_study()

        # Get the area information from the `/input/areas/<area>` file.
        path = get_area_path()
        try:
            areas_cfg = file_study.tree.get(path, depth=5)
        except KeyError:
            raise ConfigFileNotFound("/".join(path)) from None
        else:
            # "list" and "sets" must be removed: we only need areas.
            areas_cfg.pop("list", None)
            areas_cfg.pop("sets", None)

        # Get the unserverd and spilled energy costs from the `/input/thermal/areas.ini` file.
        path = get_thermal_path()
        try:
            thermal_cfg = file_study.tree.get(path, depth=3)
        except KeyError:
            raise ConfigFileNotFound("/".join(path)) from None
        else:
            thermal_areas = ThermalAreasFileData(**thermal_cfg)

        # areas_cfg contains a dictionary where the keys are the area IDs,
        # and the values are objects that can be converted to `AreaFolder`.
        area_map: dict[str, AreaProperties] = {}
        for area_id, area_cfg in areas_cfg.items():
            area_folder = AreaFileData(**area_cfg)
            props_data = AreaPropertiesFileData(
                thermal_properties=thermal_areas,
                optimization_properties=area_folder.optimization,
                adequacy_patch_properties=area_folder.adequacy_patch,
            )
            area_map[area_id] = props_data.get_area_properties(area_id, file_study.config.version)

        return area_map

    @override
    def save_area_properties(self, area_id: str, area_properties: AreaProperties) -> None:
        file_study = self.get_file_study()

        if area_id not in file_study.config.areas:
            raise AreaNotFound(area_id)

        thermal_props = ThermalAreasFileData.model_validate(file_study.tree.get(get_thermal_path()))
        optimization_props = OptimizationFileData.model_validate(file_study.tree.get(get_optimization_path(area_id)))
        adequacy_patch_props = (
            AdequacyPatchFileData.model_validate(file_study.tree.get(get_adequacy_patch_path(area_id)))
            if file_study.config.version >= STUDY_VERSION_8_3
            else AdequacyPatchFileData()
        )

        properties = AreaPropertiesFileData(
            thermal_properties=thermal_props,
            optimization_properties=optimization_props,
            adequacy_patch_properties=adequacy_patch_props,
        )

        properties.set_area_properties(area_id, area_properties)

        file_study.tree.save(
            properties.optimization_properties.model_dump(mode="json", by_alias=True),
            get_optimization_path(area_id),
        )
        if file_study.config.version >= STUDY_VERSION_8_3:
            file_study.tree.save(
                properties.adequacy_patch_properties.model_dump(mode="json", by_alias=True, exclude_none=True),
                get_adequacy_patch_path(area_id),
            )
        file_study.tree.save(
            properties.thermal_properties.model_dump(mode="json", by_alias=True),
            get_thermal_path(),
        )

        # Sync the in-memory config so consumers reading from `file_study.config`
        # (e.g. `get_synthesis`) see the freshly persisted filter values.
        area_config = file_study.config.areas[area_id]
        area_config.filters_synthesis = [str(f) for f in sort_filter_options(area_properties.filter_synthesis)]
        area_config.filters_year = [str(f) for f in sort_filter_options(area_properties.filter_by_year)]
