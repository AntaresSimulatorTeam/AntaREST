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

from typing_extensions import override

from antarest.study.business.model.area_properties_model import (
    AreaProperties,
    get_adequacy_patch_path,
    get_optimization_path,
    get_thermal_path,
)
from antarest.study.dao.api.area_properties_dao import AreaPropertiesDao
from antarest.study.model import STUDY_VERSION_8_3
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPatchFileData,
    AreaPropertiesFileData,
    OptimizationFileData,
    ThermalAreasProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyAreaPropertiesDao(AreaPropertiesDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_area_properties(
        self,
        area_id: str,
    ) -> AreaProperties:
        file_study = self.get_file_study()

        current_thermal_props = file_study.tree.get(get_thermal_path())
        current_optim_properties = file_study.tree.get(get_optimization_path(area_id))
        current_adequacy_patch = (
            file_study.tree.get(get_adequacy_patch_path(area_id))
            if file_study.config.version >= STUDY_VERSION_8_3
            else {}
        )

        properties = AreaPropertiesFileData(
            thermal_properties=ThermalAreasProperties(**current_thermal_props),
            optimization_properties=OptimizationFileData(**current_optim_properties),
            adequacy_patch_properties=AdequacyPatchFileData(**current_adequacy_patch),
        )

        return properties.get_area_properties(area_id, file_study.config.version)

    @override
    def save_area_properties(self, area_id: str, area_properties: AreaProperties) -> None:
        file_study = self.get_file_study()

        thermal_props = ThermalAreasProperties(**file_study.tree.get(get_thermal_path()))
        optimization_props = OptimizationFileData(**file_study.tree.get(get_optimization_path(area_id)))
        adequacy_patch_props = (
            AdequacyPatchFileData(**file_study.tree.get(get_adequacy_patch_path(area_id)))
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
                properties.adequacy_patch_properties.model_dump(mode="json", by_alias=True),
                get_adequacy_patch_path(area_id),
            )
        file_study.tree.save(
            properties.thermal_properties.model_dump(mode="json", by_alias=True),
            get_thermal_path(),
        )
