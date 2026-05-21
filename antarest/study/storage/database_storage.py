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
import shutil
from pathlib import Path
from typing import Iterator

from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.model import MatrixReference
from antarest.matrixstore.service import ISimpleMatrixService
from antarest.study.dao.api.study_factory_dao import StudyFactoryDao
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import RawStudy, StorageMode, Study
from antarest.study.storage.study_storage_interface import IStudyStorage
from antarest.study.storage.utils import StudyMetadataCreation

logger = logging.getLogger(__name__)


class DatabaseStudyStorage(IStudyStorage):
    def __init__(self, matrix_service: ISimpleMatrixService, study_dao_factories: dict[StorageMode, StudyFactoryDao]):
        self._matrix_service = matrix_service
        self._dao_factories = study_dao_factories

    @override
    def copy(self, src_study: Study, new_study: RawStudy) -> RawStudy:
        source_dao = self._dao_factories[StorageMode.DATABASE].get_study_dao(src_study.id, True)
        study_version = StudyVersion.parse(src_study.version)

        # Build the new DB DAO
        new_dao = self._dao_factories[StorageMode.DATABASE].get_study_dao(study_id=new_study.id, is_study_managed=True)

        # Copies the inputs
        converter = StudyConverter(
            source_dao=source_dao, new_dao=new_dao, study_version=study_version, matrix_service=self._matrix_service
        )
        converter.convert_study_inputs()

        return new_study

    @override
    def write_study_for_archive(self, study: RawStudy, dst_path: Path) -> None:
        # Nothing to do
        pass

    @override
    def export_study(self, study: Study, dst_path: Path) -> None:
        source_dao = self._dao_factories[StorageMode.DATABASE].get_study_dao(study_id=study.id, is_study_managed=True)
        study_version = StudyVersion.parse(study.version)

        # Create the new FS DAO
        metadata = StudyMetadataCreation(
            id=study.id,
            version=study_version,
            managed=False,  # Means the matrices will be denormalized
            name=study.name,
            author=study.author,
            editor=study.editor,
            created_at=study.created_at,
            updated_at=study.updated_at,
            path=dst_path,
        )
        new_dao = self._dao_factories[StorageMode.FILESYSTEM].create_study_dao(metadata)

        # Convert the DB DAO into an FS DAO
        converter = StudyConverter(
            source_dao=source_dao, new_dao=new_dao, study_version=study_version, matrix_service=self._matrix_service
        )
        converter.convert_study_inputs()

    @override
    def get_disk_usage(self, study: Study) -> int:
        return 0

    @override
    def yield_matrix_references(self, study: Study) -> Iterator[MatrixReference]:
        # Nothing to do
        yield from ()

    @override
    def normalize_study(self, study: Study) -> None:
        # Nothing to do
        pass

    @override
    def import_study(self, study: RawStudy) -> None:
        # Build the 2 DAOs
        study_id = study.id
        source_dao = self._dao_factories[StorageMode.FILESYSTEM].get_study_dao(study_id=study_id, is_study_managed=True)
        new_dao = self._dao_factories[StorageMode.DATABASE].get_study_dao(study_id=study_id, is_study_managed=True)

        # Create the new study inside DB to avoid ForeignKey errors
        session = db.session
        session.add(study)
        session.commit()

        # Convert the FS DAO into a DB one
        converter = StudyConverter(
            source_dao=source_dao,
            new_dao=new_dao,
            study_version=source_dao.get_version(),
            matrix_service=self._matrix_service,
        )
        converter.convert_study_inputs()

        # Delete the source study path once the conversion is done
        shutil.rmtree(Path(study.path))
