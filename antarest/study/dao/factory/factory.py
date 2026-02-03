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
from pathlib import Path

from antares.study.version import StudyVersion
from sqlalchemy.orm import Session

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.business.model.area_model import DEFAULT_LAYER_ID, DEFAULT_LAYER_NAME
from antarest.study.business.model.layer_model import Layer
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.file.file_study_dao import FileStudyTreeDao
from antarest.study.model import RawStudy, StorageMode, StudyContentStatus
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.utils import create_new_empty_study, is_managed, update_antares_info
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class DaoFactory:
    """
    Used to initialize a study according to the DAO type
    """

    def __init__(
        self,
        command_context: CommandContext,
        matrix_service: ISimpleMatrixService,
        study_repository: StudyMetadataRepository,
        study_factory: StudyFactory,
        session: Session | None = None,
    ) -> None:
        self._command_context = command_context
        self._matrix_service = matrix_service
        self._study_repository = study_repository
        self._study_factory = study_factory
        self._session = session

    @property
    def session(self) -> Session:
        """Get the SqlAlchemy session or create a new one on the fly if not available in the current thread."""
        if self._session is None:
            return db.session
        return self._session

    def create_study_dao(self, study: RawStudy) -> tuple[StudyDao, RawStudy]:
        study.content_status = StudyContentStatus.VALID
        self._study_repository.save(study)

        dao: StudyDao
        if study.storage_mode == StorageMode.DATABASE:
            dao = DatabaseStudyDao(study.id, self.session, self._matrix_service)
            dao.save_layer(Layer(id=DEFAULT_LAYER_ID, name=DEFAULT_LAYER_NAME))
            return dao, study

        # Create the FileStudy
        path_study = Path(study.path)

        create_new_empty_study(version=StudyVersion.parse(study.version), path_study=path_study)

        file_study = self._study_factory.create_from_fs(path_study, is_managed(study), study.id)
        update_antares_info(study, file_study.tree, update_author=True)

        study.path = str(path_study)

        context = self._command_context
        dao = FileStudyTreeDao(file_study, context.generator_matrix_constants, context.blob_service)
        return dao, study
