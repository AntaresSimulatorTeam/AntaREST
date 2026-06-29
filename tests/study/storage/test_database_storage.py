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

import pytest

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.study.dao.database.database_study_factory_dao import DatabaseStudyDaoFactory
from antarest.study.dao.file.file_study_factory_dao import FileStudyDaoFactory, ResourcePaths
from antarest.study.model import STUDY_VERSION_7_0, STUDY_VERSION_9_3, Study, StudyMetadataCreation
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.database_storage import DatabaseStudyStorage
from antarest.study.storage.rawstudy.model.filesystem.factory import StudyFactory
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from tests.helpers import create_raw_study, with_db_context


@with_db_context
def test_upgrade_fails(tmp_path: Path) -> None:
    """
    Ensures that if the upgrader fails when exporting data to the FS or during the upgrade process, the study remains in its original state.
    """
    config = Config.model_validate({"storage": {"tmp_dir": tmp_path}})

    db_dao_factory = Mock()
    db_dao_factory.get_study_dao.side_effect = ValueError("Raises for the test")

    database_storage = DatabaseStudyStorage(
        config=config,
        repository=StudyMetadataRepository(Mock()),
        matrix_service=InMemorySimpleMatrixService(),
        db_dao_factory=db_dao_factory,
        fs_dao_factory=Mock(),
    )

    # Create a study and add it to the database
    study_id = str(uuid.uuid4())
    study = create_raw_study(id=study_id, name="test", path=str(tmp_path), version=str(STUDY_VERSION_7_0))
    db.session.add(study)
    db.session.commit()

    # Upgrade should fail as we intended
    with pytest.raises(ValueError, match="Raises for the test"):
        database_storage.upgrade_study(study, version=STUDY_VERSION_9_3)

    # Ensures the study is still in v7.0 in database
    study_in_db = db.session.query(Study).first()
    assert study_in_db.version == str(STUDY_VERSION_7_0)


@with_db_context
def test_upgrade_does_not_use_cache(tmp_path: Path, study_factory) -> None:
    """
    Ensures that the upgrade method does not use the cache of the FS study exported when filling the DB with new data.
    Otherwise, it would just fill the DB with some info pre-upgrade.
    """
    ##########################
    # Set Up
    ##########################

    config = Config.model_validate({"storage": {"tmp_dir": tmp_path}})
    cache = LocalCache()
    matrix_service = InMemorySimpleMatrixService()
    generator_matrix_constants = GeneratorMatrixConstants(matrix_service)
    study_factory = StudyFactory(matrix_service=matrix_service, cache=cache)

    db_dao_factory = DatabaseStudyDaoFactory(matrix_service, generator_matrix_constants)

    def path_getter(study_id: str) -> ResourcePaths:
        return ResourcePaths(tmp_path, tmp_path)

    fs_dao_factory = FileStudyDaoFactory(
        matrix_service,
        Mock(),
        generator_matrix_constants,
        study_factory,
        cache,
        path_getter,
    )

    database_storage = DatabaseStudyStorage(
        config=config,
        repository=StudyMetadataRepository(cache),
        matrix_service=matrix_service,
        db_dao_factory=db_dao_factory,
        fs_dao_factory=fs_dao_factory,
    )

    ##########################
    # Test case
    ##########################

    # Create a study and add it to the database
    study_id = str(uuid.uuid4())
    study = create_raw_study(id=study_id, name="test", path=str(tmp_path / study_id), version=str(STUDY_VERSION_7_0))
    db.session.add(study)
    db.session.commit()

    # Initialize the study with data
    metadata = StudyMetadataCreation(id=study_id, managed=True, version=STUDY_VERSION_7_0)
    db_dao_factory.create_study_dao(metadata)

    # Upgrade the study
    database_storage.upgrade_study(study, STUDY_VERSION_9_3)

    # Asserts the cache is still empty
    assert cache.cache == {}
