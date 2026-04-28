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
from typing import TYPE_CHECKING, Self

import polars as pl
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import NotAMatrixError
from antarest.core.interfaces.cache import ICache, update_cache
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
from antarest.study.dao.file.file_study_reserve_definition_dao import FileStudyReserveDefinitionDao
from antarest.study.dao.file.file_study_reserves_global_parameters_dao import FileStudyReservesGlobalParametersDao
from antarest.study.dao.file.file_study_scenario_builder_dao import FileStudyScenarioBuilderDao
from antarest.study.dao.file.file_study_st_storage_dao import FileStudySTStorageDao
from antarest.study.dao.file.file_study_thematic_trimming_dao import FileStudyThematicTrimmingDao
from antarest.study.dao.file.file_study_thermal_dao import FileStudyThermalDao
from antarest.study.dao.file.file_study_timseries_config_dao import FileStudyTimeSeriesConfigDao
from antarest.study.dao.file.file_study_user_resources_dao import FileStudyUserResourceDao
from antarest.study.dao.file.file_study_xpansion_dao import FileStudyXpansionDao
from antarest.study.dtos import StudyDataSynthesis
from antarest.study.model import StudyMetadataUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.blobstore.service import IBlobService
    from antarest.matrixstore.service import ISimpleMatrixService
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
    FileStudyReservesGlobalParametersDao,
    FileStudyReserveDefinitionDao,
):
    """
    Implementation of study DAO over the simulator input format.
    """

    def __init__(
        self,
        study: FileStudy,
        is_study_managed: bool,
        generator_matrix_constants: "GeneratorMatrixConstants",
        blob_service: "IBlobService",
        matrix_service: "ISimpleMatrixService",
        cache: ICache,
    ) -> None:
        self._file_study = study
        self._generator_matrix_constants = generator_matrix_constants
        self._blob_service = blob_service
        self._matrix_service = matrix_service
        self._is_study_managed = is_study_managed
        self._cache = cache

    @override
    @property
    def matrix_service(self) -> "ISimpleMatrixService":
        return self._matrix_service

    @property
    def blob_service(self) -> "IBlobService":
        return self._blob_service

    @override
    @property
    def generator_matrix_constants(self) -> "GeneratorMatrixConstants":
        return self._generator_matrix_constants

    @override
    def get_study_id(self) -> str:
        return self._file_study.config.study_id

    @override
    def get_synthesis(self) -> StudyDataSynthesis:
        return StudyDataSynthesis.from_study_config(self._file_study.config)

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

    @override
    def update_antares_file(self, metadata: StudyMetadataUpdate) -> None:
        study_antares = self._file_study.tree.get(["study", "antares"])
        if metadata.editor:
            study_antares["editor"] = metadata.editor
        if metadata.last_save:
            study_antares["lastsave"] = metadata.last_save
        if metadata.name:
            study_antares["caption"] = metadata.name
        if metadata.author:
            study_antares["author"] = metadata.author
        self._file_study.tree.save(study_antares, ["study", "antares"])

    @override
    def update_cache(self) -> None:
        data = FileStudyTreeConfigDTO.from_build_config(self._file_study.config).model_dump()
        update_cache(self._cache, self._file_study.config.study_id, data)

    def get_matrix(self, url: list[str]) -> pl.DataFrame:
        """
        Given a url pointing towards an input matrix, parses it and returns it as a pandas dataframe.
        If it is not a matrix url, it raises a NotAMatrixError exception.
        """
        node = self._file_study.tree.get_node(url)
        if isinstance(node, InputSeriesMatrix):
            return node.parse_as_dataframe()
        raise NotAMatrixError(url)

    def get_matrices_ids(self, nodes: list[MatrixNode]) -> dict[MatrixNode, str]:
        """
        Get multiple matrices ids efficiently.
        It performs at most 1 DB query for the whole list.
        Nodes whose underlying matrix file is missing on disk (no `.link` symlink
        and no raw `.txt`) are silently skipped — callers don't need to pre-filter.
        """
        result = {}

        denormalized_nodes = []

        for matrix_node in nodes:
            if matrix_node.is_normalized:
                # For the normalized nodes, we simply get the matrix id from the matrix mapper.
                matrix_id = matrix_node.matrix_mapper.get_link_content(matrix_node)
                assert isinstance(matrix_id, str)
                result[matrix_node] = matrix_id
            elif matrix_node.config.path.exists():
                denormalized_nodes.append(matrix_node)

        ########## Denormalized nodes ##########
        # The `create_batch` allows us to perform only 1 DB insert for all our matrix ids.
        matrix_service = self._generator_matrix_constants.matrix_service
        matrix_ids = matrix_service.create_batch(node.parse_content() for node in denormalized_nodes)
        for k, node in enumerate(denormalized_nodes):
            result[node] = matrix_ids[k]

        return result

    def save_matrices(self, matrices_mapping: dict[str, list[MatrixNode]]) -> None:
        """
        Saves multiple matrices in their corresponding nodes efficiently.
        It performs 1 DB query for the whole list
        """
        if not self._is_study_managed:
            # The `yield_matrices` allows us to perform only 1 DB query for all our matrix ids.
            for matrix_content in self._matrix_service.yield_matrices(list(matrices_mapping)):
                dataframe = matrix_content.data
                for node in matrices_mapping[matrix_content.id]:
                    node.write_dataframe(dataframe)

            return

        # First, we check if all the matrices are already in the database in 1 single DB query.
        if not self._matrix_service.all_exist(list(matrices_mapping)):
            # Perform other DB queries to raise the proper exception if needed.
            for matrix_id in matrices_mapping:
                if not self._matrix_service.exists(matrix_id):
                    raise ValueError(f"Matrix {matrix_id} does not exist")

        # We simply save the matrix in the matrix mapper of each node.
        for matrix_id, matrix_nodes in matrices_mapping.items():
            for matrix_node in matrix_nodes:
                matrix_node.matrix_mapper.save_matrix(matrix_node, matrix_id)
