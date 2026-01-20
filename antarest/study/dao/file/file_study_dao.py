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
import typing as t
from typing import Self

import polars as pl
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import NotAMatrixError
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.file.file_study_adequacy_patch_parameters_dao import FileStudyAdequacyPatchParametersDao
from antarest.study.dao.file.file_study_advanced_parameters import FileStudyAdvancedParametersDao
from antarest.study.dao.file.file_study_area_dao import FileStudyAreaDao
from antarest.study.dao.file.file_study_area_properties_dao import FileStudyAreaPropertiesDao
from antarest.study.dao.file.file_study_compatibility_parameters import FileStudyCompatibilityParametersDao
from antarest.study.dao.file.file_study_constraint_dao import FileStudyConstraintDao
from antarest.study.dao.file.file_study_district_dao import FileStudyDistrictDao
from antarest.study.dao.file.file_study_general_config_dao import FileStudyGeneralConfigDao
from antarest.study.dao.file.file_study_hydro_dao import FileStudyHydroDao
from antarest.study.dao.file.file_study_layer_dao import FileStudyLayerDao
from antarest.study.dao.file.file_study_link_dao import FileStudyLinkDao
from antarest.study.dao.file.file_study_optimization_preferences import FileStudyOptimizationPreferencesDao
from antarest.study.dao.file.file_study_playlist_config_dao import FileStudyPlaylistConfigDao
from antarest.study.dao.file.file_study_renewable_dao import FileStudyRenewableDao
from antarest.study.dao.file.file_study_scenario_builder_dao import FileStudyScenarioBuilderDao
from antarest.study.dao.file.file_study_st_storage_dao import FileStudySTStorageDao
from antarest.study.dao.file.file_study_thematic_trimming_dao import FileStudyThematicTrimmingDao
from antarest.study.dao.file.file_study_thermal_dao import FileStudyThermalDao
from antarest.study.dao.file.file_study_timseries_config_dao import FileStudyTimeSeriesConfigDao
from antarest.study.dao.file.file_study_user_resources_dao import FileStudyUserResourceDao
from antarest.study.dao.file.file_study_xpansion_dao import FileStudyXpansionDao
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix

if t.TYPE_CHECKING:
    from antarest.blobstore.service import IBlobService
    from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants


class FileStudyTreeDao(
    StudyDao,
    FileStudyLinkDao,
    FileStudyThermalDao,
    FileStudyRenewableDao,
    FileStudyConstraintDao,
    FileStudySTStorageDao,
    FileStudyXpansionDao,
    FileStudyHydroDao,
    FileStudyGeneralConfigDao,
    FileStudyOptimizationPreferencesDao,
    FileStudyAdvancedParametersDao,
    FileStudyCompatibilityParametersDao,
    FileStudyThematicTrimmingDao,
    FileStudyAdequacyPatchParametersDao,
    FileStudyTimeSeriesConfigDao,
    FileStudyDistrictDao,
    FileStudyLayerDao,
    FileStudyPlaylistConfigDao,
    FileStudyUserResourceDao,
    FileStudyAreaPropertiesDao,
    FileStudyScenarioBuilderDao,
    FileStudyAreaDao,
):
    """
    Implementation of study DAO over the simulator input format.
    """

    def __init__(
        self,
        study: FileStudy,
        generator_matrix_constants: "GeneratorMatrixConstants",
        blob_service: "IBlobService",
    ) -> None:
        self._file_study = study
        self._generator_matrix_constants = generator_matrix_constants
        self._blob_service = blob_service

    @override
    def get_file_study(self) -> FileStudy:
        return self._file_study

    @override
    def get_impl(self) -> Self:
        return self

    @override
    def get_version(self) -> StudyVersion:
        return self._file_study.config.version

    @override
    def get_comments(self) -> str:
        content = self._file_study.tree.get(["settings", "comments"])
        assert isinstance(content, bytes)
        return content.decode("utf-8")

    @override
    def save_comments(self, comments: str) -> None:
        self._file_study.tree.save({"settings": {"comments": comments.encode("utf-8")}})

    def get_matrix(self, url: list[str]) -> pl.DataFrame:
        """
        Given a url pointing towards an input matrix, parses it and returns it as a pandas dataframe.
        If it is not a matrix url, it raises a NotAMatrixError exception.
        """
        node = self._file_study.tree.get_node(url)
        if isinstance(node, InputSeriesMatrix):
            return node.parse_as_dataframe()
        raise NotAMatrixError(url)
