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

from datetime import datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from antarest.output.dbmodel import Output
from antarest.output.repository import OutputRepository
from antarest.study.model import Study

INITIAL_ACCESS = datetime(2026, 10, 21)


@pytest.fixture
def repository(db_session: Session) -> OutputRepository:
    db_session.add_all([Study(id="study", version="9.2"), Study(id="other-study", version="9.2")])
    db_session.commit()
    return OutputRepository(db_session)


def _metadata(
    repository: OutputRepository, study_id: str = "study", output_id: str = "output"
) -> tuple[datetime | None, bool | None, int | None]:
    output = repository.get(study_id, output_id)
    assert output is not None
    return output.last_access, output.archived, output.disk_space_bytes


@pytest.mark.parametrize("last_access", [None, INITIAL_ACCESS + timedelta(days=1)])
def test_initialize_handles_concurrent_creation(
    repository: OutputRepository, mocker: MockerFixture, last_access: datetime | None
) -> None:
    add_output = repository.session.add

    def concurrent_add(output: Output) -> None:
        with Session(repository.session.get_bind()) as other_session:
            other_session.add(
                Output(
                    study_id="study", output_id="output", last_access=last_access, archived=True, disk_space_bytes=42
                )
            )
            other_session.commit()
        add_output(output)

    mocker.patch.object(repository.session, "add", side_effect=concurrent_add)
    repository.initialize("study", "output", INITIAL_ACCESS, False)

    assert _metadata(repository) == (last_access or INITIAL_ACCESS, True, 42)


def test_initialize_rejects_unknown_study(repository: OutputRepository) -> None:
    with pytest.raises(IntegrityError):
        repository.initialize("missing-study", "output", INITIAL_ACCESS, False)


def test_initialize_preserves_existing_metadata(repository: OutputRepository) -> None:
    repository.save_disk_usage("study", "output", 42)
    assert _metadata(repository) == (None, None, 42)
    repository.update_last_access("study", "output", INITIAL_ACCESS)
    repository.initialize("study", "output", INITIAL_ACCESS + timedelta(days=1), False)
    repository.initialize("study", "output", INITIAL_ACCESS + timedelta(days=2), True)
    assert _metadata(repository) == (INITIAL_ACCESS, False, 42)


def test_updates_are_scoped_to_one_output(repository: OutputRepository) -> None:
    for study_id, output_id in [("study", "output"), ("study", "other-output"), ("other-study", "output")]:
        repository.initialize(study_id, output_id, INITIAL_ACCESS, False)
        repository.save_disk_usage(study_id, output_id, 42)

    repository.update_last_access("study", "output", INITIAL_ACCESS + timedelta(days=1))
    repository.update_archived("study", "output", True)
    assert _metadata(repository) == (INITIAL_ACCESS + timedelta(days=1), True, None)
    repository.save_disk_usage("study", "output", 0)
    assert _metadata(repository) == (INITIAL_ACCESS + timedelta(days=1), True, 0)
    repository.delete("study", "output")

    # Late updates must not recreate deleted metadata.
    repository.update_last_access("study", "output", INITIAL_ACCESS)
    repository.update_archived("study", "output", True)
    assert repository.get("study", "output") is None
    for study_id, output_id in [("study", "other-output"), ("other-study", "output")]:
        assert _metadata(repository, study_id, output_id) == (INITIAL_ACCESS, False, 42)


def test_stale_session_cannot_overwrite_a_more_recent_consultation(repository: OutputRepository) -> None:
    repository.initialize("study", "output", INITIAL_ACCESS, False)
    stale_output = repository.get("study", "output")
    assert stale_output is not None
    repository.session.commit()

    latest_access = INITIAL_ACCESS + timedelta(days=2)
    with Session(repository.session.get_bind()) as other_session:
        OutputRepository(other_session).update_last_access("study", "output", latest_access)

    assert stale_output.last_access == INITIAL_ACCESS
    repository.save_disk_usage("study", "output", 42)
    repository.update_archived("study", "output", True)
    repository.initialize("study", "output", INITIAL_ACCESS, False)
    repository.update_last_access("study", "output", INITIAL_ACCESS + timedelta(days=1))

    assert _metadata(repository) == (latest_access, True, None)
