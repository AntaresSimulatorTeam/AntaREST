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
from unittest.mock import Mock

import pytest
from sqlalchemy import Engine

from antarest.core.utils.fastapi_sqlalchemy import DBSessionMiddleware, db
from antarest.launcher.model import LogType
from antarest.output.storage.v2.repository import DbOutputMetadataV2, OutputV2Repository
from antarest.study.model import Study
from antarest.study.repository import StudyMetadataRepository


@pytest.fixture
def init_db(db_engine: Engine) -> None:
    DBSessionMiddleware(None, custom_engine=db_engine)


@pytest.fixture
def study_repo(init_db) -> StudyMetadataRepository:
    return StudyMetadataRepository(cache_service=Mock())


@pytest.fixture
def output_repo(init_db) -> OutputV2Repository:
    return OutputV2Repository()


def test_repo(study_repo: StudyMetadataRepository, output_repo: OutputV2Repository) -> None:
    with db():
        assert list(output_repo.search_output_metadata()) == []

        # The FK constraints enforces us to create a study first.
        study_repo.save(Study(id="study_id_1", name="name", version="9.2", path=""))
        study_repo.save(Study(id="study_id_2", name="name", version="9.2", path=""))

        # 3 results, 2 for the same study, 1 is archived
        output_repo.save_output_metadata(
            DbOutputMetadataV2(
                study_id="study_id_1",
                output_name="output_1",
                archived=False,
                mode="Economy",
                synthesis=True,
                nb_years=1,
                by_year=True,
            )
        )
        output_repo.save_output_metadata(
            DbOutputMetadataV2(
                study_id="study_id_1",
                output_name="output_2",
                archived=True,
                mode="Economy",
                synthesis=False,
                nb_years=12,
                by_year=True,
            )
        )
        output_repo.save_output_metadata(
            DbOutputMetadataV2(
                study_id="study_id_2",
                output_name="output_1",
                archived=False,
                mode="Adequacy",
                synthesis=True,
                nb_years=24,
                by_year=False,
            )
        )

        # Get all
        assert len(list(output_repo.search_output_metadata())) == 3

        # Get only first study outputs
        study_1_outputs = list(output_repo.search_output_metadata(study_id="study_id_1"))
        assert len(study_1_outputs) == 2
        output_1, output_2 = study_1_outputs[0], study_1_outputs[1]
        assert output_1.output_name == "output_1"
        assert not output_1.archived
        assert output_1.synthesis
        assert output_1.by_year
        assert output_1.nb_years == 1

        assert output_2.output_name == "output_2"
        assert output_2.archived
        assert not output_2.synthesis
        assert output_2.by_year
        assert output_2.nb_years == 12

        # get only one output
        output_2 = output_repo.get_output_metadata(study_id="study_id_1", output_name="output_2")
        assert output_2.output_name == "output_2"

        # get one output which does not exist
        assert output_repo.get_output_metadata(study_id="study_id_2", output_name="not_found") is None

        # get archived ones
        archived_outputs = list(output_repo.search_output_metadata(archived=True))
        assert len(archived_outputs) == 1
        assert archived_outputs[0].output_name == "output_2"

        # get unarchived ones
        unarchived_outputs = list(output_repo.search_output_metadata(archived=False))
        assert len(unarchived_outputs) == 2
        assert [(o.study_id, o.output_name) for o in unarchived_outputs] == [
            ("study_id_1", "output_1"),
            ("study_id_2", "output_1"),
        ]

        # Update one output (archive status)
        output_1 = output_repo.get_output_metadata(study_id="study_id_1", output_name="output_1")
        output_1.archived = True
        output_repo.save_output_metadata(output_1)
        assert len(list(output_repo.search_output_metadata(archived=True))) == 2

        # Delete one output
        output_repo.delete_output("study_id_1", "output_1")
        assert output_repo.get_output_metadata(study_id="study_id_1", output_name="output_1") is None
        assert len(list(output_repo.search_output_metadata())) == 2


def test_get_and_save_logs(study_repo: StudyMetadataRepository, output_repo: OutputV2Repository) -> None:
    with db():
        assert list(output_repo.search_output_metadata()) == []

        # The FK constraints enforces us to create a study first.
        study_repo.save(Study(id="study_id_1", name="name", version="9.2", path=""))
        study_repo.save(Study(id="study_id_2", name="name", version="9.2", path=""))

        output_repo.save_output_metadata(
            DbOutputMetadataV2(
                study_id="study_id_1",
                output_name="output_1",
                archived=False,
                mode="Economy",
                synthesis=True,
                nb_years=1,
                by_year=True,
            )
        )

    with db():
        assert output_repo.get_log("study_id_1", "output_1", LogType.STDOUT) == ""
        assert output_repo.get_log("study_id_1", "output_1", LogType.STDERR) == ""

    with db():
        output_repo.save_log("study_id_1", "output_1", LogType.STDOUT, "out log")
        output_repo.save_log("study_id_1", "output_1", LogType.STDERR, "err log")

        assert output_repo.get_log("study_id_1", "output_1", LogType.STDOUT) == "out log"
        assert output_repo.get_log("study_id_1", "output_1", LogType.STDERR) == "err log"
