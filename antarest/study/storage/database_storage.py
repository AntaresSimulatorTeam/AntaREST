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
import logging
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from typing_extensions import override

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.model import RawStudy, Study
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants

logger = logging.getLogger(__name__)


class DatabaseStudyStorage(IStudyStorage):
    def __init__(
        self, config: Config, matrix_service: ISimpleMatrixService, generator_matrix_constants: GeneratorMatrixConstants
    ):
        self._matrix_service = matrix_service
        self._generator_matrix_constants = generator_matrix_constants
        self._config = config

    @override
    def get_dao(self, study: Study) -> DatabaseStudyDao:
        return DatabaseStudyDao(study.id, db.session, self._matrix_service, self._generator_matrix_constants)

    @override
    def copy(self, src_study: Study, dest_name: str, groups: list[str], destination_folder: PurePosixPath) -> Study:
        raise NotImplementedError()

    @override
    def write_study_to_filesytem(self, study: Study) -> Path:
        raise NotImplementedError()

    @override
    def normalize_study(self, study: Study) -> None:
        # Nothing to do
        pass

    @override
    def import_study(self, study: RawStudy, stream: BinaryIO) -> RawStudy:
        raise NotImplementedError()
