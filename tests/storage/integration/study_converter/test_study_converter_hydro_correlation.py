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
import uuid
from pathlib import Path
from unittest.mock import Mock

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.study.business.model.area_properties_model import AreaProperties, initialize_area_properties
from antarest.study.business.model.hydro_correlation_model import HydroCorrelation, HydroCorrelationArea
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.database.database_study_dao import DatabaseStudyDao
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory
from antarest.study.dao.study_conversion.study_converter import StudyConverter
from antarest.study.model import StorageMode, StudyMetadataCreation
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from tests.helpers import create_raw_study, with_db_context


def _setup(dao: StudyDao) -> None:
    for area_name in ["fr", "be", "pl"]:
        props = AreaProperties()
        initialize_area_properties(props, dao.get_version())
        dao.save_areas_with_properties({area_name: props})
    dao.save_hydro_correlation(
        {
            "fr": HydroCorrelation(
                correlation=[
                    HydroCorrelationArea(area_id="fr", coefficient=100.0),
                    HydroCorrelationArea(area_id="be", coefficient=72.0),
                    HydroCorrelationArea(area_id="pl", coefficient=85.0),
                ]
            )
        }
    )


@with_db_context
def test_conversion(dao: StudyDao, study_factory: StudyFactory, tmp_path: Path) -> None:
    _setup(dao)

    matrix_service = dao.matrix_service
    db_dao_factory = DatabaseStudyDaoFactory(matrix_service, Mock())
    fs_dao_factory = FileStudyDaoFactory(
        matrix_service,
        Mock(),
        Mock(),
        study_factory,
        LocalCache(),
        Mock(),  # probably to do ...
    )

    study_id, study_version = str(uuid.uuid4()), dao.get_version()

    creation = StudyMetadataCreation(id=study_id, version=study_version, managed=True)
    if isinstance(dao, DatabaseStudyDao):
        study = create_raw_study(id=study_id, version=str(study_version), storage_mode=StorageMode.DATABASE)
        db.session.add(study)
        db.session.commit()
        new_dao = db_dao_factory.create_study_dao(creation)
    else:
        study = create_raw_study(
            id=study_id, version=str(study_version), storage_mode=StorageMode.FILESYSTEM, path=str(tmp_path / study_id)
        )
        db.session.add(study)
        db.session.commit()
        new_dao = fs_dao_factory.create_study_dao(creation)

    # Conversion shouldn't raise
    converter = StudyConverter(dao, new_dao, dao.get_version(), dao.matrix_service)
    converter.convert_study_inputs()
    pass
