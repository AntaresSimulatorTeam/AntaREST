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

from antarest.core.config import Config
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.matrixstore.in_memory import InMemorySimpleMatrixService
from antarest.study.model import STUDY_VERSION_7_0, STUDY_VERSION_9_3, Study
from antarest.study.repository import StudyMetadataRepository
from antarest.study.storage.database_storage import DatabaseStudyStorage
from tests.helpers import create_raw_study, with_db_context


@with_db_context
def test_upgrade(tmp_path: Path) -> None:
    """
    Ensures that if the upgrader fails when exporting data to the FS or during the upgrade process, the study remains in its original state.
    """
    config = Config.from_dict({"storage": {"tmp_dir": tmp_path}})

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
