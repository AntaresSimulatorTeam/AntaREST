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
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, DEFAULT_LAYER_NAME
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import StorageMode, Study
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class DaoFactory:
    """
    Used to initialize a study according to the DAO type
    """

    def __init__(
        self,
        command_context: CommandContext,
        matrix_service: ISimpleMatrixService,
        storage_service: StudyStorageService,
    ) -> None:
        self._command_context = command_context
        self._matrix_service = matrix_service
        self._storage_service = storage_service

    def create_study_dao(self, study: Study) -> StudyDao:
        if study.storage_mode == StorageMode.DATABASE:
            dao = DatabaseStudyDao(study.id, db.session, self._matrix_service)
            dao.save_layer(Layer(id=DEFAULT_LAYER_ID, name=DEFAULT_LAYER_NAME))
            return dao

        return FileStudyTreeDao(
            self._storage_service.get_storage(study).get_raw(study),
            self._command_context.generator_matrix_constants,
            self._command_context.blob_service,
        )
